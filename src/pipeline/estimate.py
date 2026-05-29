"""Núcleo de estimativa: features, piso de ruído, avaliação honesta e previsão.

Tese central: com 10 painéis, a métrica que importa não é "o MAE é baixo?" mas
"o erro do modelo está dentro da variação com que humanos medem a MESMA tarefa?".
Por isso tudo é comparado contra o piso de ruído humano.

Partilhado por `modeling.py` (treino/benchmark/deploy) e pelo predict.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

TARGET = "duration_sec"
GROUP = "panel_id"

# features: identidade da micro-op (dominante) + geometria do painel
GEOM = [
    "largura_painel_mm", "altura_painel_mm", "profundidade_painel_mm",
    "largura_perfil_mm", "espessura_perfil_mm", "num_montantes", "num_raias",
    "comprimento_montante_mm", "comprimento_raia_mm", "num_furos_raia",
    "num_placas_por_face", "perimetro_placa_total_mm", "perimetro_placa_maior_mm",
    "espessura_placa_mm",
]

# Canonical UI language is English (matches the frontend). MICRO_OP_NAMES_PT is
# kept for future localisation. These are display labels only — no lookup/enum
# anywhere keys off the string, so changing them is safe.
MICRO_OP_NAMES = {
    1: "Pick profiles", 2: "Place profiles", 3: "Fix frame",
    4: "Measure / align", 5: "Crimp frame", 6: "Place board(s)",
    7: "Measure / adjust board", 8: "Screw board(s)", 9: "Remove fasteners",
    10: "Flip frame", 11: "Crimp 2", 12: "Label", 13: "Pallet / transport",
    14: "Move table",
}

MICRO_OP_NAMES_PT = {
    1: "Pegar nos perfis", 2: "Colocar perfis na bancada", 3: "Fixar estrutura",
    4: "Medições/alinhamentos", 5: "Cravação 1", 6: "Pegar e colocar placa(s)",
    7: "Medições/ajustes placa", 8: "Aparafusar placa(s)", 9: "Remover fixadores",
    10: "Virar estrutura", 11: "Cravação 2", 12: "Etiqueta", 13: "Palete/transporte",
    14: "Transportar mesa",
}


# --- dados ------------------------------------------------------------------

def load_data(train_dir: Path = Path("data/training"), clean: bool = False,
              holdout: list[str] | None = None) -> pd.DataFrame:
    """Event-log unificado (todas as observações individuais).

    `holdout`: panel_ids a excluir do conjunto (para garantir que nenhum painel a
    ser avaliado entra no treino, mesmo que o código colida entre projetos).
    """
    parts = []
    for f in ("training_long.parquet", "test_long.parquet"):
        p = train_dir / f
        if p.exists():
            parts.append(pd.read_parquet(p))
    if not parts:
        raise FileNotFoundError(f"Sem *_long.parquet em {train_dir} (corre `build-training`)")
    d = pd.concat(parts, ignore_index=True).reset_index(drop=True)
    if holdout:
        hold = {h.strip().upper() for h in holdout}
        before = d[GROUP].nunique()
        d = d[~d[GROUP].str.upper().isin(hold)].reset_index(drop=True)
        print(f"  holdout: excluded {sorted(hold)} → {d[GROUP].nunique()}/{before} panels in training")
    if clean:
        from .training_table import clean_observations
        d = clean_observations(d)
    return d


def design_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """micro_op como categórica (one-hot) + geometria numérica."""
    return pd.get_dummies(df[["micro_op_num"] + GEOM], columns=["micro_op_num"]).astype(float)


def align(Xtr: pd.DataFrame, Xte: pd.DataFrame) -> pd.DataFrame:
    """Garante que Xte tem exatamente as colunas de Xtr (preenche 0)."""
    Xte = Xte.copy()
    for c in Xtr.columns:
        if c not in Xte:
            Xte[c] = 0.0
    return Xte[Xtr.columns]


# --- piso de ruído humano ---------------------------------------------------

def human_noise_floor(d: pd.DataFrame) -> dict:
    """Erro de prever uma medição a partir das OUTRAS da mesma tarefa (LOO).

    É o limite que nenhum modelo pode bater de forma fiável.
    """
    errs, cvs = [], []
    for _, g in d.groupby([GROUP, "micro_op_num"]):
        v = g[TARGET].to_numpy(float)
        if len(v) < 2:
            continue
        for i in range(len(v)):
            errs.append(abs(v[i] - np.delete(v, i).mean()))
        if v.mean() > 0:
            cvs.append(v.std(ddof=1) / v.mean())
    return {
        "mae": float(np.mean(errs)),
        "cv_median_pct": float(np.median(cvs) * 100),
        "n_pairs": len(errs),
    }


# --- avaliação LOPO ---------------------------------------------------------

def lopo_fold_maes(predict_fn, d: pd.DataFrame) -> dict[str, float]:
    """MAE por painel (leave-one-panel-out). predict_fn(train_df, test_df)->array."""
    fold = {}
    for held in sorted(d[GROUP].unique()):
        trm, tem = d[d[GROUP] != held], d[d[GROUP] == held]
        pred = np.asarray(predict_fn(trm, tem))
        fold[held] = float(np.mean(np.abs(tem[TARGET].to_numpy() - pred)))
    return fold


def predict_per_op_median(trm: pd.DataFrame, tem: pd.DataFrame) -> np.ndarray:
    m = trm.groupby("micro_op_num")[TARGET].median()
    return tem.micro_op_num.map(m).fillna(trm[TARGET].median()).to_numpy()


# --- intervalos CONFORMAIS (calibrados pelos resíduos do modelo) ------------
#
# Em vez do espalhamento dos dados (heurístico, miscalibrado: prometia 80% e dava
# 70%), usamos os resíduos out-of-sample do próprio modelo. Garante cobertura
# calibrada (~alvo) e distribution-free. Por micro-op, com fallback global.

_MIN_OP = 8  # nº mínimo de resíduos numa op para usar quantil próprio (senão global)


def _conf_q(x, alpha: float) -> float:
    """Quantil conformal conservador (ajuste finito (n+1)α/n)."""
    x = np.asarray(x, float)
    if len(x) == 0:
        return float("inf")
    return float(np.quantile(x, min(1.0, (len(x) + 1) * alpha / len(x)), method="higher"))


def lopo_residuals(predict_fn, d: pd.DataFrame) -> pd.DataFrame:
    """Resíduos RELATIVOS |real − previsto|/previsto, out-of-sample (LOPO).

    Relativo (não absoluto) porque o ruído é multiplicativo (CV ~constante) e as
    durações são positivas/enviesadas — evita bandas simétricas que caem abaixo de 0.
    """
    parts = []
    for held in sorted(d[GROUP].unique()):
        trm, tem = d[d[GROUP] != held], d[d[GROUP] == held]
        pred = np.maximum(0, np.asarray(predict_fn(trm, tem)))
        t = tem[[GROUP, "micro_op_num", TARGET]].copy()
        t["pred"] = pred
        t["rel"] = (t[TARGET] - pred).abs() / np.clip(pred, 1.0, None)
        parts.append(t)
    return pd.concat(parts, ignore_index=True)


def conformal_quantiles(residuals: pd.DataFrame, levels=(0.80, 0.90)) -> dict:
    """Meia-largura RELATIVA q por micro-op (+ global) para cada nível. Usado no deploy."""
    out = {}
    for a in levels:
        gq = _conf_q(residuals["rel"], a)
        qmap = {"__global__": gq}
        for op, g in residuals.groupby("micro_op_num"):
            qmap[str(int(op))] = _conf_q(g["rel"], a) if len(g) >= _MIN_OP else gq
        out[f"q{int(a * 100)}"] = qmap
    return out


def conformal_coverage(predict_fn, d: pd.DataFrame, levels=(0.80, 0.90)) -> dict:
    """Prova honesta: calibra em painéis ≠ held, mede cobertura no held (LOPO)."""
    R = lopo_residuals(predict_fn, d)
    rep = {}
    for a in levels:
        cov, wid = [], []
        for held in sorted(d[GROUP].unique()):
            cal, tgt = R[R[GROUP] != held], R[R[GROUP] == held]
            gq = _conf_q(cal["rel"], a)
            qop = {op: (_conf_q(g["rel"], a) if len(g) >= _MIN_OP else gq)
                   for op, g in cal.groupby("micro_op_num")}
            for _, r in tgt.iterrows():
                q = qop.get(r["micro_op_num"], gq)
                cov.append(abs(r[TARGET] - r["pred"]) <= q * r["pred"])
                wid.append(2 * q * r["pred"])
        rep[f"q{int(a * 100)}"] = {"coverage_pct": float(100 * np.mean(cov)),
                                    "mean_width_sec": float(np.mean(wid))}
    return rep


# --- previsão por painel/projeto com intervalo ------------------------------

def predict_panel(model, design_cols, conformal: dict, panel_geom: dict,
                  micro_ops: list[int] | None = None, level: str = "q90") -> dict:
    """Por micro-op {ponto, lo, hi} + total do painel, com intervalo CONFORMAL calibrado.

    `conformal[level]` = {str(micro_op): q, "__global__": q} — meia-largura do
    intervalo (resíduos LOPO do modelo). O total propaga somando as meias-larguras
    (conservador). `level` ∈ {"q80","q90"}.
    """
    ops = micro_ops or list(range(1, 15))
    rows = pd.DataFrame([{**panel_geom, "micro_op_num": op} for op in ops])
    X = align(pd.DataFrame(columns=design_cols), design_matrix(rows))
    point = model.predict(X)
    qmap = conformal.get(level, {})
    qglobal = qmap.get("__global__", 0.0)

    items, tot, lo_t, hi_t = [], 0.0, 0.0, 0.0
    for op, p in zip(ops, point):
        p = max(0.0, float(p))
        q = float(qmap.get(str(op), qglobal))  # meia-largura RELATIVA
        lo, hi = max(0.0, p * (1 - q)), p * (1 + q)
        items.append({
            "micro_op_num": op, "micro_op_name": MICRO_OP_NAMES.get(op, ""),
            "point_sec": round(p, 1), "lo_sec": round(lo, 1), "hi_sec": round(hi, 1),
        })
        tot += p; lo_t += lo; hi_t += hi
    return {
        "panel_id": panel_geom.get("panel_id", "?"),
        "interval_level": level,
        "micro_ops": items,
        "total_sec": round(tot, 1),
        "total_lo_sec": round(lo_t, 1),
        "total_hi_sec": round(hi_t, 1),
    }

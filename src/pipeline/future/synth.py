"""Geração dos datasets sintéticos (FICTÍCIOS) dos 4 modelos do `future/`.

Princípio: os tempos têm de FAZER SENTIDO em relação aos dados reais —
- painel maior → mais tempo (escala com a geometria real de cada painel),
- cada efeito (desperdício, temperatura, experiência, hora) é multiplicativo
  sobre uma base realista derivada das medianas reais por micro-op.

Tudo determinístico (seed fixa) para ser reprodutível. Schema de cada parquet =
schema real (`panel_id, source, observation_id, micro_op_num, duration_sec` +
14 colunas `E.GEOM`) + a coluna extra do modelo (quando aplicável).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import estimate as E
from . import FUTURE_DIR, OP_IDLE, OP_MATERIAL

GEOMETRY = "data/training/panel_geometry.parquet"

# Medianas reais por micro-op (fallback caso falte algum dado real).
_FALLBACK_BASE = {1: 18, 2: 35, 3: 28, 4: 15, 5: 34, 6: 31, 7: 48, 8: 104,
                  9: 14, 10: 7, 11: 30, 12: 15, 13: 16, 14: 7}

N_OBS = 12          # observações sintéticas por (painel, micro-op)
NOISE_CV = 0.20     # ruído lognormal (~ ruído humano observado)
SEED = 42

# Nomes das pseudo-ops de desperdício (o resto vem de E.MICRO_OP_NAMES).
WASTE_NAMES = {
    OP_IDLE: "Idle — no value (phone, etc.)",
    OP_MATERIAL: "Material run — necessary",
}


def _op_base() -> dict[int, float]:
    """Base de tempo por micro-op = mediana real (cai para fallback se faltar)."""
    try:
        d = E.load_data()
        med = d.groupby("micro_op_num")[E.TARGET].median().to_dict()
        return {op: float(med.get(op, _FALLBACK_BASE[op])) for op in range(1, 15)}
    except Exception:
        return {op: float(v) for op, v in _FALLBACK_BASE.items()}


def _size_factor(geom: pd.Series, area_ref: float) -> float:
    """Painel maior → mais tempo. Sublinear (sqrt) para evitar extremos."""
    area = float(geom["largura_painel_mm"]) * float(geom["altura_painel_mm"])
    return float(np.sqrt(max(area, 1.0) / area_ref))


def _lognoise(rng: np.random.Generator, n: int) -> np.ndarray:
    """Ruído multiplicativo positivo com CV ≈ NOISE_CV (mediana 1)."""
    sigma = np.sqrt(np.log(1 + NOISE_CV ** 2))
    return np.exp(rng.normal(0.0, sigma, n))


def _temp_mult(t: np.ndarray) -> np.ndarray:
    """Conforto a 20°C; quente MUITO improdutivo; frio improdutivo (menos)."""
    return 1.0 + 0.012 * np.maximum(0, t - 20) ** 2 + 0.005 * np.maximum(0, 20 - t) ** 2


def _exp_mult(m: np.ndarray) -> np.ndarray:
    """Mais experiência (meses) → mais rápido. Novato ~1.5×, sénior ~0.86×."""
    return 0.85 + 0.75 * np.exp(-m / 12.0)


# Multiplicador por hora: manhã ótima, pós-almoço e fim do dia piores.
_HOUR_MULT = {8: 0.98, 9: 0.95, 10: 0.96, 11: 1.00, 12: 1.08,
              13: 1.30, 14: 1.32, 15: 1.22, 16: 1.10, 17: 1.26}


def _hour_mult(h: np.ndarray) -> np.ndarray:
    return np.array([_HOUR_MULT.get(int(x), 1.0) for x in h], float)


def _geom_cols(geom: pd.Series) -> dict:
    return {c: geom[c] for c in E.GEOM}


def _build_base(panels: pd.DataFrame, op_base: dict[int, float], area_ref: float,
                rng: np.random.Generator, ops=range(1, 15)) -> pd.DataFrame:
    """Frame longo base (sem efeitos): painel × op × N_OBS, com geometria."""
    rows = []
    oid = 0
    for _, g in panels.iterrows():
        sf = _size_factor(g, area_ref)
        gc = _geom_cols(g)
        for op in ops:
            base = op_base[op] * sf
            durs = base * _lognoise(rng, N_OBS)
            for k in range(N_OBS):
                oid += 1
                rows.append({"panel_id": g["panel_id"], "source": "synthetic",
                             "observation_id": f"S{oid:05d}", "micro_op_num": op,
                             "duration_sec": float(durs[k]), **gc})
    return pd.DataFrame(rows)


# --- os 4 datasets ----------------------------------------------------------

def build_general(panels, op_base, area_ref, rng) -> pd.DataFrame:
    """Ops 1–14 normais + desperdício: idle aleatório (15) e material sistemático (16)."""
    df = _build_base(panels, op_base, area_ref, rng)
    extra = []
    oid = 10**6
    for _, g in panels.iterrows():
        sf = _size_factor(g, area_ref)
        gc = _geom_cols(g)
        material = float(g["perimetro_placa_total_mm"]) / 1000.0 + float(g["num_montantes"]) * 1.5
        for k in range(N_OBS):
            oid += 1
            # NECESSÁRIO: sempre presente, escala com material, ruído baixo → previsível
            # (bloco sizável e consistente — o alvo claro de otimização de processo).
            mat = (35.0 + 2.4 * material) * sf * float(_lognoise(rng, 1)[0] ** 0.5)
            extra.append({"panel_id": g["panel_id"], "source": "synthetic",
                          "observation_id": f"M{oid}", "micro_op_num": OP_MATERIAL,
                          "duration_sec": mat, **gc})
            # SEM VALOR: ~40% das observações, duração aleatória, SEM relação com geometria.
            if rng.random() < 0.40:
                oid += 1
                idle = float(rng.uniform(20, 110))
                extra.append({"panel_id": g["panel_id"], "source": "synthetic",
                              "observation_id": f"I{oid}", "micro_op_num": OP_IDLE,
                              "duration_sec": idle, **gc})
    return pd.concat([df, pd.DataFrame(extra)], ignore_index=True)


def build_temperature(panels, op_base, area_ref, rng) -> pd.DataFrame:
    df = _build_base(panels, op_base, area_ref, rng)
    t = rng.uniform(8, 32, len(df))
    df["duration_sec"] = df["duration_sec"].to_numpy() * _temp_mult(t)
    df["temperatura_c"] = np.round(t, 1)
    return df


def build_experience(panels, op_base, area_ref, rng) -> pd.DataFrame:
    df = _build_base(panels, op_base, area_ref, rng)
    m = rng.uniform(1, 60, len(df))
    df["duration_sec"] = df["duration_sec"].to_numpy() * _exp_mult(m)
    df["experiencia_meses"] = np.round(m, 1)
    return df


def build_timeofday(panels, op_base, area_ref, rng) -> pd.DataFrame:
    df = _build_base(panels, op_base, area_ref, rng)
    h = rng.integers(8, 18, len(df))
    df["duration_sec"] = df["duration_sec"].to_numpy() * _hour_mult(h)
    df["hora_do_dia"] = h.astype(int)
    return df


_BUILDERS = {
    "general": build_general,
    "temperature": build_temperature,
    "experience": build_experience,
    "timeofday": build_timeofday,
}


def build_all_synth(geometry_path: str = GEOMETRY) -> dict[str, pd.DataFrame]:
    """Gera os 4 parquets sintéticos em data/training/future/."""
    panels = pd.read_parquet(geometry_path).drop_duplicates("panel_id").reset_index(drop=True)
    op_base = _op_base()
    area_ref = float((panels["largura_painel_mm"] * panels["altura_painel_mm"]).median())
    FUTURE_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, builder in _BUILDERS.items():
        rng = np.random.default_rng(SEED)  # mesma seed por dataset (reprodutível)
        df = builder(panels, op_base, area_ref, rng)
        df["duration_sec"] = df["duration_sec"].clip(lower=1.0).round(1)
        path = FUTURE_DIR / f"{name}_long.parquet"
        df.to_parquet(path, index=False)
        out[name] = df
        print(f"  {name:12} {len(df):5d} obs × {df['panel_id'].nunique()} painéis → {path}")
    return out

"""Métricas longitudinais: como o modelo melhora à medida que entram dados.

Produz `data/training/metrics.json` com:
  - learning_curve : MAE LOPO vs nº de painéis de treino (+ piso de ruído humano)
  - history        : por marco de volume de dados — MAE + cobertura conformal
                     (backfill honesto via treino em dados crescentes; o último
                     ponto é o modelo atual; retreinos reais acrescentam pontos)
  - projection     : extrapolação (mae → piso) — claramente marcada como projeção

Recalculado a cada `train`. Lido pela página de métricas via /metrics.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import estimate as E


def _catboost_predict_fn():
    from catboost import CatBoostRegressor
    def fn(trm, tem):
        Xtr = E.design_matrix(trm)
        Xte = E.align(Xtr, E.design_matrix(tem))
        m = CatBoostRegressor(iterations=150, depth=3, learning_rate=0.05, l2_leaf_reg=5,
                              loss_function="MAE", random_seed=42, verbose=False)
        m.fit(Xtr, trm[E.TARGET].to_numpy())
        return np.maximum(0, m.predict(Xte))
    return fn


def _lopo_mae(d: pd.DataFrame, predict_fn) -> float:
    return float(np.mean(list(E.lopo_fold_maes(predict_fn, d).values())))


def learning_curve(d: pd.DataFrame, n_subsets: int = 4, seed: int = 42) -> list[dict]:
    """MAE LOPO médio para cada tamanho de conjunto de painéis (3..N)."""
    import itertools
    panels = sorted(d[E.GROUP].unique())
    rng = np.random.RandomState(seed)
    fn = _catboost_predict_fn()
    out = []
    for k in range(3, len(panels) + 1):
        combos = list(itertools.combinations(panels, k))
        rng.shuffle(combos)
        combos = combos[: min(n_subsets, len(combos))]
        maes = [_lopo_mae(d[d[E.GROUP].isin(list(s))], fn) for s in combos]
        out.append({"n_panels": k, "mae": round(float(np.mean(maes)), 2),
                    "n_obs": int(d[d[E.GROUP].isin(list(combos[0]))].shape[0])})
    return out


def history_milestones(d: pd.DataFrame, seed: int = 42) -> list[dict]:
    """Backfill honesto: treina em volumes de dados crescentes e mede MAE+cobertura.

    Cada marco = 'se tivéssemos treinado com este volume de dados'. O último é o
    modelo atual. Retreinos reais (no train) acrescentam pontos a seguir a este.
    """
    panels = sorted(d[E.GROUP].unique())
    rng = np.random.RandomState(seed)
    order = list(panels); rng.shuffle(order)  # ordem de "chegada" dos dados
    fn = _catboost_predict_fn()
    out = []
    for k in range(3, len(panels) + 1):
        sub = d[d[E.GROUP].isin(order[:k])]
        floor = E.human_noise_floor(sub)["mae"]
        mae = _lopo_mae(sub, fn)
        cov = E.conformal_coverage(fn, sub)
        out.append({
            "milestone": f"{k} painéis", "n_panels": k, "n_obs": int(len(sub)),
            "mae": round(mae, 2), "noise_floor": round(floor, 2),
            "coverage_q80": round(cov["q80"]["coverage_pct"], 1),
            "coverage_q90": round(cov["q90"]["coverage_pct"], 1),
            "simulated": k < len(panels),  # o último é o modelo real atual
        })
    return out


def project(curve: list[dict], floor: float, up_to: int = 40) -> list[dict]:
    """Extrapola mae(n) = floor + A·n^(-b) (ajuste log-log). PROJEÇÃO, não medição."""
    n = np.array([p["n_panels"] for p in curve], float)
    y = np.array([p["mae"] for p in curve], float) - floor
    mask = y > 0.1
    if mask.sum() < 2:
        return []
    b, logA = np.polyfit(np.log(n[mask]), np.log(y[mask]), 1)
    A = np.exp(logA)
    start = int(n.max())
    return [{"n_panels": k, "mae": round(float(floor + A * k ** b), 2), "projected": True}
            for k in range(start, up_to + 1, 2)]


def build_metrics(d: pd.DataFrame | None = None) -> dict:
    if d is None:
        d = E.load_data(clean=True)
    floor = E.human_noise_floor(d)
    curve = learning_curve(d)
    hist = history_milestones(d)
    proj = project(curve, floor["mae"])
    return {
        "noise_floor": round(floor["mae"], 2),
        "noise_floor_cv_pct": round(floor["cv_median_pct"], 1),
        "learning_curve": curve,
        "history": hist,
        "projection": proj,
        "n_panels": int(d[E.GROUP].nunique()),
        "n_obs": int(len(d)),
    }


def write_metrics(d: pd.DataFrame | None = None,
                  out: Path = Path("data/training/metrics.json")) -> dict:
    m = build_metrics(d)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2))
    print(f"metrics → {out}  (curva: {len(m['learning_curve'])} pts · "
          f"histórico: {len(m['history'])} · projeção: {len(m['projection'])})")
    return m

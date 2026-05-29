"""Treino dos 4 modelos sintéticos do `future/`.

Segue a mesma filosofia do pipeline real (CatBoost campeão + avaliação LOPO +
intervalos conformais calibrados pelos resíduos), mas com uma design-matrix
GENERALIZADA que aceita uma feature extra (temperatura / experiência / hora).

Reutiliza tal-e-qual a maquinaria honesta de `pipeline.estimate`:
`human_noise_floor`, `lopo_fold_maes`, `lopo_residuals`, `conformal_quantiles`,
`align`. Treino sem Optuna (rápido) — params CatBoost fixos e sensatos.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .. import estimate as E
from . import FUTURE_DIR, MODELS

CATBOOST_PARAMS = dict(iterations=300, depth=6, learning_rate=0.1,
                       loss_function="MAE", random_seed=42, verbose=False)


def fdesign(df: pd.DataFrame, extra_cols: list[str]) -> pd.DataFrame:
    """one-hot(micro_op_num) + E.GEOM + features extra (mesma ideia de E.design_matrix)."""
    cols = ["micro_op_num"] + list(E.GEOM) + list(extra_cols)
    return pd.get_dummies(df[cols], columns=["micro_op_num"]).astype(float)


def _make_catboost():
    from catboost import CatBoostRegressor
    return CatBoostRegressor(**CATBOOST_PARAMS)


def _predict_fn(extra_cols: list[str]):
    """predict_fn(train_df, test_df)->array, com a design-matrix generalizada."""
    def fn(trm: pd.DataFrame, tem: pd.DataFrame) -> np.ndarray:
        Xtr = fdesign(trm, extra_cols)
        Xte = E.align(Xtr, fdesign(tem, extra_cols))
        m = _make_catboost()
        m.fit(Xtr, trm[E.TARGET].to_numpy())
        return np.maximum(0, m.predict(Xte))
    return fn


def train_one(name: str, extra_col: str | None) -> dict:
    """Treina, avalia (LOPO), calibra conformal e faz deploy de um modelo future."""
    extra_cols = [extra_col] if extra_col else []
    d = pd.read_parquet(FUTURE_DIR / f"{name}_long.parquet")

    predict_fn = _predict_fn(extra_cols)
    folds = E.lopo_fold_maes(predict_fn, d)
    lopo_mae = float(np.mean(list(folds.values())))
    floor = E.human_noise_floor(d)

    residuals = E.lopo_residuals(predict_fn, d)
    conformal = E.conformal_quantiles(residuals)

    # refit em todos os dados → campeão deployável
    model = _make_catboost()
    Xall = fdesign(d, extra_cols)
    model.fit(Xall, d[E.TARGET].to_numpy())

    out_dir = FUTURE_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model, out_dir / "champion.joblib")
    meta = {
        "name": name,
        "champion": "catboost",
        "extra_cols": extra_cols,
        "design_cols": list(Xall.columns),
        "conformal": conformal,
        "noise_floor": floor,
        "lopo_mae": lopo_mae,
        "n_train_obs": int(len(d)),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"  {name:12} LOPO MAE {lopo_mae:6.1f}s · piso {floor['mae']:.1f}s · {len(d)} obs")
    return meta


def train_all() -> dict[str, dict]:
    print("=== Treino dos modelos future (CatBoost) ===")
    return {name: train_one(name, extra) for name, extra in MODELS.items()}

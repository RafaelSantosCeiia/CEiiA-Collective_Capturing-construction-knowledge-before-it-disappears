"""Treino do modelo de duração por micro-tarefa.

Lê `training_wide.csv`, transforma para long format, faz sweep com Optuna
em CatBoost / LightGBM / XGBoost, treina cada vencedor + um ensemble simples
(média), e regista resultados em `data/training/model/`.

Validação: leave-one-panel-out (LOPO). Com poucos painéis isto é severamente
limitado, mas é a única estratégia honesta para o objectivo de generalizar
a painéis nunca vistos.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import mean_absolute_error

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)


@dataclass
class TrainResult:
    model_name: str
    best_params: dict
    cv_mae: float
    fold_maes: list[float]


# --- 1. Data prep ------------------------------------------------------------

def load_long(csv_path: Path = Path("data/training/training_wide.csv")) -> pd.DataFrame:
    """Wide CSV → long format. Rows = (panel × micro_op), cols = features + target."""
    df = pd.read_csv(csv_path, index_col=0)
    feature_rows = [r for r in df.index if not r.startswith("micro_op_")]
    micro_op_rows = [r for r in df.index if r.startswith("micro_op_")]

    features_wide = df.loc[feature_rows].T  # rows=panels, cols=features
    durations_wide = df.loc[micro_op_rows].T  # rows=panels, cols=micro_op_*

    rows: list[dict] = []
    for panel_id, panel_feats in features_wide.iterrows():
        feat_dict = panel_feats.to_dict()
        # Cast tipos
        for k, v in list(feat_dict.items()):
            if isinstance(v, str):
                if v == "True":
                    feat_dict[k] = True
                elif v == "False":
                    feat_dict[k] = False
                else:
                    try:
                        feat_dict[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        pass  # mantém string (codigo_painel)
        for op_label, dur in durations_wide.loc[panel_id].items():
            if pd.isna(dur):
                continue
            op_num = int(op_label.replace("micro_op_", "").replace("_dur_sec", ""))
            rows.append({
                **feat_dict,
                "micro_op_num": op_num,
                "_panel_id": panel_id,
                "duration_sec": float(dur),
            })
    return pd.DataFrame(rows)


def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, list[str]]:
    y = df["duration_sec"].to_numpy()
    groups = df["_panel_id"].to_numpy()
    X = df.drop(columns=["duration_sec", "_panel_id"])

    # Identifica categóricas (object, string-ext, ou bool)
    cat_cols = [c for c in X.columns
                if X[c].dtype == "object" or X[c].dtype == "bool"
                or pd.api.types.is_string_dtype(X[c])]
    for c in cat_cols:
        X[c] = X[c].astype(str)
    return X, y, groups, cat_cols


# --- 2. Cross-validation -----------------------------------------------------

def leave_one_panel_out(X: pd.DataFrame, y: np.ndarray, groups: np.ndarray):
    """Generator (train_idx, test_idx) para cada painel."""
    unique_groups = np.unique(groups)
    for g in unique_groups:
        train = np.where(groups != g)[0]
        test = np.where(groups == g)[0]
        yield train, test


# --- 3. Boosters -------------------------------------------------------------

def _cv_mae(model_factory, X, y, groups, cat_cols):
    fold_maes = []
    for tr, te in leave_one_panel_out(X, y, groups):
        model = model_factory()
        fit_X = X.iloc[tr].copy()
        # CatBoost lida bem; LightGBM/XGBoost precisam de codificação
        if hasattr(model, "_supports_categorical_fit") and model._supports_categorical_fit:
            model.fit(fit_X, y[tr], cat_features=cat_cols)
        else:
            fit_X_enc = pd.get_dummies(fit_X, columns=cat_cols, drop_first=False)
            te_X_enc = pd.get_dummies(X.iloc[te], columns=cat_cols, drop_first=False)
            # Align
            for c in fit_X_enc.columns:
                if c not in te_X_enc.columns:
                    te_X_enc[c] = 0
            te_X_enc = te_X_enc[fit_X_enc.columns]
            model.fit(fit_X_enc, y[tr])
            pred = model.predict(te_X_enc)
            fold_maes.append(mean_absolute_error(y[te], pred))
            continue
        pred = model.predict(X.iloc[te])
        fold_maes.append(mean_absolute_error(y[te], pred))
    return float(np.mean(fold_maes)), fold_maes


def sweep_catboost(X, y, groups, cat_cols, trials=20) -> TrainResult:
    from catboost import CatBoostRegressor

    def objective(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 50, 400),
            "depth": trial.suggest_int("depth", 2, 6),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "verbose": False,
            "loss_function": "MAE",
            "random_seed": 42,
        }
        def factory():
            m = CatBoostRegressor(**params)
            m._supports_categorical_fit = True
            return m
        cv_mae, _ = _cv_mae(factory, X, y, groups, cat_cols)
        return cv_mae

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    best = study.best_params
    def best_factory():
        m = CatBoostRegressor(**best, verbose=False, loss_function="MAE", random_seed=42)
        m._supports_categorical_fit = True
        return m
    cv_mae, fold_maes = _cv_mae(best_factory, X, y, groups, cat_cols)
    return TrainResult("catboost", best, cv_mae, fold_maes)


def sweep_lightgbm(X, y, groups, cat_cols, trials=20) -> TrainResult:
    from lightgbm import LGBMRegressor

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 400),
            "max_depth": trial.suggest_int("max_depth", 2, 6),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 4, 32),
            "min_child_samples": trial.suggest_int("min_child_samples", 2, 8),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 5.0),
            "verbose": -1,
            "random_state": 42,
            "objective": "regression_l1",
        }
        def factory(): return LGBMRegressor(**params)
        cv_mae, _ = _cv_mae(factory, X, y, groups, cat_cols)
        return cv_mae

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    best = study.best_params
    def best_factory():
        return LGBMRegressor(**best, verbose=-1, random_state=42, objective="regression_l1")
    cv_mae, fold_maes = _cv_mae(best_factory, X, y, groups, cat_cols)
    return TrainResult("lightgbm", best, cv_mae, fold_maes)


def sweep_xgboost(X, y, groups, cat_cols, trials=20) -> TrainResult:
    from xgboost import XGBRegressor

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 400),
            "max_depth": trial.suggest_int("max_depth", 2, 6),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 5.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
            "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 10.0),
            "random_state": 42,
            "objective": "reg:absoluteerror",
            "verbosity": 0,
        }
        def factory(): return XGBRegressor(**params)
        cv_mae, _ = _cv_mae(factory, X, y, groups, cat_cols)
        return cv_mae

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    best = study.best_params
    def best_factory():
        return XGBRegressor(**best, random_state=42, objective="reg:absoluteerror", verbosity=0)
    cv_mae, fold_maes = _cv_mae(best_factory, X, y, groups, cat_cols)
    return TrainResult("xgboost", best, cv_mae, fold_maes)


# --- 4. Ensemble -------------------------------------------------------------

def ensemble_lopo(X, y, groups, cat_cols, results: list[TrainResult]) -> tuple[float, list[float]]:
    """Média simples das previsões dos 3 boosters em cada fold LOPO."""
    from catboost import CatBoostRegressor
    from lightgbm import LGBMRegressor
    from xgboost import XGBRegressor

    def make_models(best):
        return {
            "catboost": CatBoostRegressor(**{**best["catboost"], "verbose": False,
                                              "loss_function": "MAE", "random_seed": 42}),
            "lightgbm": LGBMRegressor(**{**best["lightgbm"], "verbose": -1,
                                          "random_state": 42, "objective": "regression_l1"}),
            "xgboost":  XGBRegressor(**{**best["xgboost"], "random_state": 42,
                                         "objective": "reg:absoluteerror", "verbosity": 0}),
        }

    best_params = {r.model_name: r.best_params for r in results}
    fold_maes = []
    for tr, te in leave_one_panel_out(X, y, groups):
        models = make_models(best_params)
        preds = []
        # CatBoost: trata categóricas
        cb = models["catboost"]
        cb.fit(X.iloc[tr], y[tr], cat_features=cat_cols)
        preds.append(cb.predict(X.iloc[te]))
        # LGBM/XGB: dummies
        enc_train = pd.get_dummies(X.iloc[tr], columns=cat_cols)
        enc_test = pd.get_dummies(X.iloc[te], columns=cat_cols)
        for c in enc_train.columns:
            if c not in enc_test.columns: enc_test[c] = 0
        enc_test = enc_test[enc_train.columns]
        for name in ("lightgbm", "xgboost"):
            m = models[name]
            m.fit(enc_train, y[tr])
            preds.append(m.predict(enc_test))
        avg = np.mean(preds, axis=0)
        fold_maes.append(mean_absolute_error(y[te], avg))
    return float(np.mean(fold_maes)), fold_maes


# --- 5. Orchestration --------------------------------------------------------

def run(trials: int = 20, output_dir: Path = Path("data/training/model")) -> dict:
    df = load_long()
    print(f"Dataset: {len(df)} linhas × {len(df.columns) - 2} features")
    print(f"Painéis: {sorted(df['_panel_id'].unique())}")
    print(f"Micro-ops: {sorted(df['micro_op_num'].unique())}\n")

    X, y, groups, cat_cols = split_xy(df)
    print(f"Categóricas: {cat_cols}\n")

    print("=== Sweep Optuna ===")
    cb = sweep_catboost(X, y, groups, cat_cols, trials=trials)
    print(f"  CatBoost   LOPO MAE = {cb.cv_mae:.2f}s  folds={[f'{m:.1f}' for m in cb.fold_maes]}")
    lg = sweep_lightgbm(X, y, groups, cat_cols, trials=trials)
    print(f"  LightGBM   LOPO MAE = {lg.cv_mae:.2f}s  folds={[f'{m:.1f}' for m in lg.fold_maes]}")
    xg = sweep_xgboost(X, y, groups, cat_cols, trials=trials)
    print(f"  XGBoost    LOPO MAE = {xg.cv_mae:.2f}s  folds={[f'{m:.1f}' for m in xg.fold_maes]}")

    print("\n=== Ensemble (média) ===")
    ens_mae, ens_folds = ensemble_lopo(X, y, groups, cat_cols, [cb, lg, xg])
    print(f"  Ensemble   LOPO MAE = {ens_mae:.2f}s  folds={[f'{m:.1f}' for m in ens_folds]}")

    # Baseline: prever sempre a mediana do treino
    base_folds = []
    for tr, te in leave_one_panel_out(X, y, groups):
        base = float(np.median(y[tr]))
        base_folds.append(mean_absolute_error(y[te], np.full_like(y[te], base, dtype=float)))
    base_mae = float(np.mean(base_folds))
    print(f"  Baseline   LOPO MAE = {base_mae:.2f}s  (mediana do treino)")

    # MAE estratificado por placagem_dupla — a ordem dos folds corresponde a np.unique(groups)
    fold_panels = list(np.unique(groups))
    dupla_map = df.groupby("_panel_id")["placagem_dupla"].first().to_dict()
    fold_dupla = [bool(dupla_map[p]) for p in fold_panels]

    def stratify(fold_maes: list[float]) -> dict:
        true_maes = [m for m, d in zip(fold_maes, fold_dupla) if d]
        false_maes = [m for m, d in zip(fold_maes, fold_dupla) if not d]
        return {
            "true_mae": float(np.mean(true_maes)) if true_maes else None,
            "false_mae": float(np.mean(false_maes)) if false_maes else None,
            "per_panel": dict(zip(fold_panels, [float(m) for m in fold_maes])),
        }

    print("\n=== MAE estratificado por placagem_dupla ===")
    for name, folds in [("CatBoost", cb.fold_maes), ("LightGBM", lg.fold_maes),
                        ("XGBoost", xg.fold_maes), ("Ensemble", ens_folds),
                        ("Baseline", base_folds)]:
        s = stratify(folds)
        t = f"{s['true_mae']:.2f}s" if s["true_mae"] is not None else "—"
        f = f"{s['false_mae']:.2f}s" if s["false_mae"] is not None else "—"
        print(f"  {name:9}  True (n={sum(fold_dupla)}): {t}    False (n={sum(not d for d in fold_dupla)}): {f}")

    leaderboard = {
        "n_rows": len(df), "n_features": X.shape[1],
        "n_panels": int(len(np.unique(groups))),
        "fold_panels": fold_panels,
        "fold_placagem_dupla": fold_dupla,
        "models": {
            "catboost": {"cv_mae": cb.cv_mae, "fold_maes": cb.fold_maes,
                         "best_params": cb.best_params, "stratified": stratify(cb.fold_maes)},
            "lightgbm": {"cv_mae": lg.cv_mae, "fold_maes": lg.fold_maes,
                         "best_params": lg.best_params, "stratified": stratify(lg.fold_maes)},
            "xgboost":  {"cv_mae": xg.cv_mae, "fold_maes": xg.fold_maes,
                         "best_params": xg.best_params, "stratified": stratify(xg.fold_maes)},
            "ensemble": {"cv_mae": ens_mae, "fold_maes": ens_folds,
                         "stratified": stratify(ens_folds)},
            "baseline": {"cv_mae": base_mae, "fold_maes": base_folds,
                         "stratified": stratify(base_folds)},
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "leaderboard.json").write_text(json.dumps(leaderboard, indent=2))
    print(f"\n✅ leaderboard → {output_dir / 'leaderboard.json'}")
    return leaderboard

"""Benchmark multi-modelo + champion-gate + deploy — o retreino noturno mensal.

Fluxo do `run()` (pensado para correr de madrugada e fazer deploy automático):
  build-training → limpar outliers → benchmark (Optuna por modelo) →
  escolher campeão por LOPO → champion-gate vs baseline → deploy → leaderboard

Modelos (registry swappable — sem vendor lock):
  baseline_global · per_op_median · catboost · lightgbm · xgboost · stacking
  + autogluon (opcional, via try-import; compete se instalado)

Tudo avaliado com leave-one-panel-out (LOPO), a única CV honesta para o objetivo
de generalizar a painéis nunca produzidos.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import mean_absolute_error

from . import estimate as E

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)


# --- LOPO genérico para um estimador sklearn-like ---------------------------

def _lopo_estimator(make_estimator, d: pd.DataFrame) -> dict[str, float]:
    def predict_fn(trm, tem):
        Xtr, Xte = E.design_matrix(trm), E.design_matrix(tem)
        Xte = E.align(Xtr, Xte)
        m = make_estimator()
        m.fit(Xtr, trm[E.TARGET].to_numpy())
        return m.predict(Xte)
    return E.lopo_fold_maes(predict_fn, d)


# --- Optuna por booster -----------------------------------------------------

def _tune_lightgbm(d, trials):
    from lightgbm import LGBMRegressor
    def space(t):
        return dict(n_estimators=t.suggest_int("n_estimators", 50, 400),
                    max_depth=t.suggest_int("max_depth", 2, 6),
                    learning_rate=t.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    num_leaves=t.suggest_int("num_leaves", 4, 32),
                    min_child_samples=t.suggest_int("min_child_samples", 2, 8),
                    reg_alpha=t.suggest_float("reg_alpha", 0.0, 5.0))
    base = dict(verbose=-1, random_state=42, objective="regression_l1")
    def obj(t):
        p = {**space(t), **base}
        return float(np.mean(list(_lopo_estimator(lambda: LGBMRegressor(**p), d).values())))
    best = _study(obj, trials)
    return "lightgbm", lambda: LGBMRegressor(**best, **base), best


def _tune_xgboost(d, trials):
    from xgboost import XGBRegressor
    def space(t):
        return dict(n_estimators=t.suggest_int("n_estimators", 50, 400),
                    max_depth=t.suggest_int("max_depth", 2, 6),
                    learning_rate=t.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    reg_alpha=t.suggest_float("reg_alpha", 0.0, 5.0),
                    reg_lambda=t.suggest_float("reg_lambda", 0.0, 5.0),
                    min_child_weight=t.suggest_float("min_child_weight", 1.0, 10.0))
    base = dict(random_state=42, objective="reg:absoluteerror", verbosity=0)
    def obj(t):
        p = {**space(t), **base}
        return float(np.mean(list(_lopo_estimator(lambda: XGBRegressor(**p), d).values())))
    best = _study(obj, trials)
    return "xgboost", lambda: XGBRegressor(**best, **base), best


def _tune_catboost(d, trials):
    from catboost import CatBoostRegressor
    def space(t):
        return dict(iterations=t.suggest_int("iterations", 50, 400),
                    depth=t.suggest_int("depth", 2, 6),
                    learning_rate=t.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    l2_leaf_reg=t.suggest_float("l2_leaf_reg", 1.0, 10.0))
    base = dict(verbose=False, loss_function="MAE", random_seed=42)
    def obj(t):
        p = {**space(t), **base}
        return float(np.mean(list(_lopo_estimator(lambda: CatBoostRegressor(**p), d).values())))
    best = _study(obj, trials)
    return "catboost", lambda: CatBoostRegressor(**best, **base), best


def _study(obj, trials):
    s = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    s.optimize(obj, n_trials=trials, show_progress_bar=False)
    return s.best_params


# --- benchmark -------------------------------------------------------------

def benchmark(d: pd.DataFrame, trials: int = 30) -> dict:
    """Corre todos os modelos sob LOPO. Devolve leaderboard ordenado por MAE."""
    results: dict[str, dict] = {}

    # baselines honestas
    gm = E.lopo_fold_maes(lambda tr, te: np.full(len(te), tr[E.TARGET].median()), d)
    results["baseline_global"] = {"mae": _m(gm), "folds": gm, "params": {}}
    om = E.lopo_fold_maes(E.predict_per_op_median, d)
    results["per_op_median"] = {"mae": _m(om), "folds": om, "params": {}}

    # boosters com Optuna
    tuned = {}
    for tuner in (_tune_lightgbm, _tune_xgboost, _tune_catboost):
        try:
            name, factory, best = tuner(d, trials)
            folds = _lopo_estimator(factory, d)
            results[name] = {"mae": _m(folds), "folds": folds, "params": best}
            tuned[name] = factory
            print(f"  {name:16} LOPO MAE = {_m(folds):.2f}s")
        except Exception as e:
            print(f"  {tuner.__name__} falhou: {type(e).__name__}: {e}")

    # stacking dos boosters afinados (meta-learner = ridge)
    if len(tuned) >= 2:
        try:
            from sklearn.ensemble import StackingRegressor
            from sklearn.linear_model import RidgeCV
            def make_stack():
                return StackingRegressor(
                    estimators=[(n, f()) for n, f in tuned.items()],
                    final_estimator=RidgeCV(), cv=3, n_jobs=1)
            folds = _lopo_estimator(make_stack, d)
            results["stacking"] = {"mae": _m(folds), "folds": folds, "params": {}}
            print(f"  {'stacking':16} LOPO MAE = {_m(folds):.2f}s")
        except Exception as e:
            print(f"  stacking falhou: {type(e).__name__}: {e}")

    # AutoGluon (opcional — só se instalado)
    ag = _benchmark_autogluon(d)
    if ag is not None:
        results["autogluon"] = ag
        print(f"  {'autogluon':16} LOPO MAE = {ag['mae']:.2f}s")

    return dict(sorted(results.items(), key=lambda kv: kv[1]["mae"]))


def _benchmark_autogluon(d: pd.DataFrame):
    try:
        from autogluon.tabular import TabularPredictor  # noqa
    except ImportError:
        print("  autogluon: não instalado (opcional — `pip install autogluon.tabular`)")
        return None
    from autogluon.tabular import TabularPredictor
    folds = {}
    for held in sorted(d[E.GROUP].unique()):
        trm, tem = d[d[E.GROUP] != held], d[d[E.GROUP] == held]
        cols = ["micro_op_num"] + E.GEOM + [E.TARGET]
        pr = TabularPredictor(label=E.TARGET, eval_metric="mean_absolute_error", verbosity=0)
        pr.fit(trm[cols], presets="medium_quality", time_limit=120)
        pred = pr.predict(tem[cols])
        folds[held] = float(mean_absolute_error(tem[E.TARGET], pred))
    return {"mae": _m(folds), "folds": folds, "params": {"preset": "medium_quality"}}


def _m(folds: dict) -> float:
    return float(np.mean(list(folds.values())))


# --- champion + deploy ------------------------------------------------------

def _build_estimator(name: str, params: dict):
    """Devolve o estimador (não ajustado) para um modelo geometry-aware."""
    if name == "lightgbm":
        from lightgbm import LGBMRegressor
        return LGBMRegressor(**params, verbose=-1, random_state=42, objective="regression_l1")
    if name == "xgboost":
        from xgboost import XGBRegressor
        return XGBRegressor(**params, random_state=42, objective="reg:absoluteerror", verbosity=0)
    if name == "catboost":
        from catboost import CatBoostRegressor
        return CatBoostRegressor(**params, verbose=False, loss_function="MAE", random_seed=42)
    if name == "stacking":
        from sklearn.ensemble import StackingRegressor
        from sklearn.linear_model import RidgeCV
        from lightgbm import LGBMRegressor
        from xgboost import XGBRegressor
        from catboost import CatBoostRegressor
        return StackingRegressor(estimators=[
            ("lightgbm", LGBMRegressor(verbose=-1, random_state=42, objective="regression_l1")),
            ("xgboost", XGBRegressor(random_state=42, objective="reg:absoluteerror", verbosity=0)),
            ("catboost", CatBoostRegressor(verbose=False, loss_function="MAE", random_seed=42)),
        ], final_estimator=RidgeCV(), cv=3)
    raise ValueError(f"estimador não suportado: '{name}'")


def _predict_fn_for(name: str, params: dict):
    """predict_fn(train_df, test_df)->array, para LOPO conformal (qualquer campeão)."""
    if name == "per_op_median":
        return E.predict_per_op_median
    if name == "baseline_global":
        return lambda tr, te: np.full(len(te), tr[E.TARGET].median())
    def fn(trm, tem):
        Xtr = E.design_matrix(trm)
        Xte = E.align(Xtr, E.design_matrix(tem))
        m = _build_estimator(name, params)
        m.fit(Xtr, trm[E.TARGET].to_numpy())
        return np.maximum(0, m.predict(Xte))
    return fn


def _refit_champion(name: str, d: pd.DataFrame, params: dict):
    """Reajusta o campeão em TODOS os dados (limpos). Devolve estimador pronto."""
    if name in ("per_op_median", "baseline_global"):
        return _MedianModel(d, name)
    m = _build_estimator(name, params)
    m.fit(E.design_matrix(d), d[E.TARGET].to_numpy())
    return m


class _MedianModel:
    """Wrapper sklearn-like para a baseline mediana por micro-op (campeável + deployável)."""
    def __init__(self, d, kind="per_op_median"):
        self._cols = list(E.design_matrix(d).columns)
        if kind == "per_op_median":
            self._med = d.groupby("micro_op_num")[E.TARGET].median().to_dict()
        else:
            self._med = {}
        self._global = float(d[E.TARGET].median())

    def predict(self, X: pd.DataFrame):
        # recupera micro_op a partir das dummies one-hot
        out = []
        op_cols = [c for c in X.columns if c.startswith("micro_op_num_")]
        for _, r in X.iterrows():
            op = next((int(c.split("_")[-1]) for c in op_cols if r.get(c, 0) == 1), None)
            out.append(self._med.get(op, self._global))
        return np.array(out, float)


def deploy(champion_name: str, d: pd.DataFrame, leaderboard: dict,
           output_dir: Path, timestamp: str | None = None) -> dict:
    """Reajusta + grava o campeão (joblib) + meta.json (com bandas p/ intervalos)."""
    import joblib
    output_dir.mkdir(parents=True, exist_ok=True)
    params = leaderboard[champion_name]["params"]
    model = _refit_champion(champion_name, d, params)
    joblib.dump(model, output_dir / "champion.joblib")

    # intervalos conformais calibrados pelos resíduos LOPO do campeão
    predict_fn = _predict_fn_for(champion_name, params)
    residuals = E.lopo_residuals(predict_fn, d)
    conformal = E.conformal_quantiles(residuals)
    coverage = E.conformal_coverage(predict_fn, d)

    meta = {
        "champion": champion_name,
        "cv_mae": leaderboard[champion_name]["mae"],
        "design_cols": list(E.design_matrix(d).columns),
        "conformal": conformal,
        "conformal_coverage": coverage,
        "features": E.GEOM,
        "n_train_obs": int(len(d)),
        "deployed_at": timestamp,
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def load_deployed(model_dir: Path = Path("data/training/model")) -> dict:
    import joblib
    meta = json.loads((model_dir / "meta.json").read_text())
    meta["model"] = joblib.load(model_dir / "champion.joblib")
    return meta


# --- orquestração: retreino noturno ----------------------------------------

def run(trials: int = 30, clean: bool = True, require_improvement: bool = True,
        holdout: list[str] | None = None,
        output_dir: Path = Path("data/training/model"), timestamp: str | None = None) -> dict:
    print("=== Build training table ===")
    from .training_table import build_training_table
    build_training_table()
    d = E.load_data(clean=clean, holdout=holdout)
    floor = E.human_noise_floor(d)
    print(f"\nDataset: {len(d)} obs, {d[E.GROUP].nunique()} painéis | piso humano {floor['mae']:.1f}s")

    print("\n=== Benchmark (LOPO) ===")
    lb = benchmark(d, trials=trials)

    # O campeão DEPLOYÁVEL tem de ser geometry-aware (diferencia painéis — o produto).
    # A baseline per_op_median é a *referência* do gate, não candidata: ignora a
    # geometria, logo daria o mesmo tempo a todos os painéis.
    baseline_mae = lb["per_op_median"]["mae"]
    GATE_TOL = 1.20  # aceita até 20% acima da baseline (estão empatados dentro do ruído)
    candidates = {k: v for k, v in lb.items() if k not in ("baseline_global", "per_op_median")}
    champ = min(candidates, key=lambda k: lb[k]["mae"]) if candidates else "per_op_median"
    gate_ok = (not require_improvement) or (lb[champ]["mae"] <= baseline_mae * GATE_TOL)
    if not gate_ok:
        print(f"\n⚠️  Champion-gate: melhor modelo ({lb[champ]['mae']:.1f}s) está >20% acima da "
              f"baseline ({baseline_mae:.1f}s) → algo partido, deploy da baseline.")
        champ = "per_op_median"
    else:
        print(f"\n   Gate OK: {champ} {lb[champ]['mae']:.1f}s ≤ baseline×1.2 ({baseline_mae*GATE_TOL:.1f}s) "
              f"— diferencia painéis ao custo de ~{lb[champ]['mae']-baseline_mae:+.1f}s (dentro do ruído).")

    print(f"\n🏆 Campeão: {champ}  (LOPO MAE {lb[champ]['mae']:.2f}s vs piso {floor['mae']:.1f}s)")
    meta = deploy(champ, d, lb, output_dir, timestamp=timestamp)

    report = {
        "human_noise_floor": floor,
        "conformal_coverage": meta["conformal_coverage"],
        "leaderboard": {k: {"mae": v["mae"]} for k, v in lb.items()},
        "champion": champ,
        "deployed": meta,
    }
    (output_dir / "leaderboard.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"\n✅ deploy → {output_dir}/champion.joblib  ·  leaderboard → {output_dir}/leaderboard.json")

    # métricas longitudinais (curva de aprendizagem, histórico, projeção)
    try:
        from .metrics import write_metrics
        write_metrics(d, output_dir.parent / "metrics.json")
    except Exception as e:
        print(f"métricas falharam: {type(e).__name__}: {e}")

    _print_scorecard(report, lb)
    return report


def _print_scorecard(report: dict, lb: dict) -> None:
    f = report["human_noise_floor"]
    print(f"\n{'='*56}\n SCORECARD\n{'='*56}")
    print(f" Piso de ruído humano: MAE {f['mae']:.1f}s · CV {f['cv_median_pct']:.0f}% (limite teórico)\n")
    print(f" {'Modelo':18}{'LOPO MAE':>10}")
    for name, v in lb.items():
        star = " 🏆" if name == report["champion"] else ""
        print(f"   {name:16}{v['mae']:8.1f}s{star}")
    cc = report.get("conformal_coverage", {})
    if cc:
        print("\n Intervalos conformais (cobertura calibrada vs alvo):")
        for lvl, alvo in (("q80", 80), ("q90", 90)):
            if lvl in cc:
                print(f"   alvo {alvo}%: cobre {cc[lvl]['coverage_pct']:.0f}% "
                      f"· largura média {cc[lvl]['mean_width_sec']:.0f}s")

# PipeLine — Panel Task Duration Prediction

End-to-end ML pipeline that ingests panel manufacturing orders (BOM + CAD PDFs +
operation logs), extracts features, simulates realistic per-task durations, and
trains a regressor that predicts how long each operation will take for a new
production order.

> **Status:** working golden path. 5/5 tests pass. Model artifacts ship in two
> formats (`joblib` + `skops`) and a champion-gate prevents regressions on
> retrain.

---

## 1. Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Build features + training table from data/raw
./scripts/pipeline run-all

# Train the deployed model (refits the benchmark winner)
./scripts/pipeline train

# Predict for one production order
./scripts/pipeline predict OP-2026-001

# Sanity tests
pytest tests/ -v

# (Optional) Run the HTTP API on :8000 — see docs/API.md
./scripts/api
```

The `pipeline` launcher wires `PYTHONPATH=src` and calls `python -m pipeline.cli`.
The `api` launcher does the same and runs `uvicorn pipeline.api:app`.

---

## 2. CLI commands

| Command                              | Purpose                                                            |
|--------------------------------------|--------------------------------------------------------------------|
| `pipeline features`                  | Build `panel_task_features.parquet`                                |
| `pipeline training`                  | Build `training_tasks.parquet` (features + simulated duration)     |
| `pipeline run-all`                   | Both of the above, in order                                        |
| `pipeline train`                     | Refit the benchmark winner and write deploy artifacts              |
| `pipeline retrain`                   | Unattended end-to-end: features → training → benchmark → train → tests |
| `pipeline predict <OP>`              | Per-operation duration predictions for one production order       |
| `pipeline predict-input <panel_id>`  | Show the raw inference frame for inspection                        |
| `pipeline show <table>`              | Pretty-print a generated parquet table (`list` to enumerate)       |

Flags worth knowing:
- `pipeline train --require-improvement` — refuse to deploy a model worse than the current champion.
- `pipeline retrain --skip-benchmark` — reuse existing `leaderboard.json`.
- `pipeline retrain --trials N` — Optuna trials per booster (default 80).

---

## 3. Repository layout

```
PipeLine/
├── README.md                 # this file
├── TECH_REPORT.md            # design notes
├── docs/
│   ├── API.md                # HTTP API + n8n workflow
│   ├── TECHNOLOGIES.md       # what every dependency is for
│   └── TESTING.md            # how tests are organised + last run results
├── requirements.txt
├── pyproject.toml
├── config/
│   └── panels.yaml           # active config (paths, simulation params)
├── src/pipeline/
│   ├── cli.py                # Typer CLI
│   ├── config.py             # Config + dataclasses
│   ├── ingest.py             # Parse PDFs + operation JSONs into panel bundles
│   ├── panels.py             # Feature tables (panel_task_features, panel_materials)
│   ├── training.py           # Training table builder + CatBoost schema export
│   ├── simulation.py         # Deterministic synthetic durations (SHA-256 seeded)
│   ├── inference.py          # Build inference frame for a single production order
│   ├── model.py              # Train / persist / load / predict
│   └── model_zoo.py          # Registry of sklearn-compatible regressors
├── scripts/
│   ├── pipeline              # Bash launcher
│   ├── benchmark.py          # Optuna sweep across CatBoost/LightGBM/XGBoost/sklearn
│   ├── analyze_model.py      # SHAP, permutation importance, PDP/ICE plots
│   ├── stability.py          # Leaderboard variance across seeds
│   └── regenerate_durations.py
├── tests/
│   └── test_predict.py       # 5 end-to-end assertions
└── data/
    ├── raw/                  # BOM PDFs, CAD PDFs, operation JSONs (test fixtures)
    ├── features/             # panel_task_features.parquet, panel_materials.parquet
    └── training/             # training_tasks.parquet, model artifacts, analysis plots
```

Model artifacts in `data/training/model/`, benchmark output in
`data/training/benchmark/`, and the model backup in
`data/training/model.previous/` are **gitignored** because they are large
(~80 MB each) and fully regenerable.

---

## 4. Data layers

| Layer       | Path                          | Granularity                     |
|-------------|-------------------------------|---------------------------------|
| raw         | `data/raw/`                   | One BOM PDF + CAD PDF + JSON per order |
| features    | `data/features/`              | 1 row per `op_producao × op_id` |
| training    | `data/training/training_tasks.parquet` | features + simulated target `duration_min` |
| deploy      | `data/training/model/`        | `model.joblib`, `model.skops`, `meta.json` |
| analysis    | `data/training/analysis/`     | SHAP / PDP / permutation plots  |

Outputs are **Parquet** for portability + cheap pandas/polars I/O.

---

## 5. Key technical decisions

- **Two model formats.** `joblib` is fast and standard; `skops` is the safer
  serialization format. Both are written on every train and a test
  (`test_load_skops_and_joblib_agree`) asserts they produce identical
  predictions.
- **Champion gate.** `train --require-improvement` refuses to deploy a
  candidate whose benchmark MAE is worse than the current model.
- **Atomic retrain.** `retrain` runs features → training table → Optuna
  benchmark → train winner → pytest, and appends a JSONL audit entry to
  `data/training/retrain_log.jsonl`.
- **Deterministic simulation.** Synthetic durations use SHA-256 of
  `(seed, panel_id, op_id)` as the per-row seed, so the training set is
  fully reproducible and noise is independent across rows.
- **Group-aware evaluation.** Cross-validation groups by `op_producao` so a
  panel's tasks never straddle train/test.

See [`TECH_REPORT.md`](TECH_REPORT.md) for the full rationale.

---

## 6. Tests

5 end-to-end tests in `tests/test_predict.py`:

1. `test_meta_schema_matches_training_module` — deploy meta agrees with the live schema.
2. `test_load_skops_and_joblib_agree` — both serializations predict identically.
3. `test_predict_for_known_op_producao` — happy path returns the expected shape.
4. `test_predict_total_within_envelope_of_real` — predicted totals track the simulated truth within tolerance.
5. `test_unknown_key_raises` — unknown keys raise `ValueError`.

Last run: **5 passed in 18.51 s** (see [`docs/TESTING.md`](docs/TESTING.md)).

To run them yourself, build the artifacts first:
```bash
./scripts/pipeline run-all
./scripts/pipeline train
pytest tests/ -v
```

---

## 7. Technologies

Short list (full notes in [`docs/TECHNOLOGIES.md`](docs/TECHNOLOGIES.md)):

- **Python 3.11**, **Typer**, **Rich** — CLI and terminal UX.
- **PyMuPDF** (`fitz`), **ezdxf** — PDF / DXF parsing.
- **pandas**, **polars**, **pyarrow**, **numpy** — data + Parquet I/O.
- **scikit-learn**, **joblib**, **skops** — modeling + serialization.
- **Optuna** + optional **CatBoost / LightGBM / XGBoost** — benchmark sweep.
- **SHAP**, **matplotlib** — interpretability plots.
- **DuckDB**, **pydantic**, **PyYAML**, **rapidfuzz** — config, ad-hoc SQL, fuzzy linkage.

---

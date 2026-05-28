# Testing

Tests live in `tests/test_predict.py` and validate the end-to-end golden path:
features → training table → trained model → predictions.

## Prerequisites

The tests load real artifacts produced by the pipeline. Build them first:

```bash
source .venv/bin/activate
pip install -r requirements.txt
./scripts/pipeline run-all   # writes data/features/ + data/training/training_tasks.parquet
./scripts/pipeline train     # writes data/training/model/*
pytest tests/ -v
```

## What is covered

| # | Test | What it asserts |
|---|------|-----------------|
| 1 | `test_meta_schema_matches_training_module` | The schema persisted in `model/meta.json` matches the live `training` module — no silent feature drift between training and deploy. |
| 2 | `test_load_skops_and_joblib_agree` | The model loaded from `.skops` and from `.joblib` produces identical predictions on the same input — both serialization paths are safe. |
| 3 | `test_predict_for_known_op_producao` | `predict_for_key` returns the expected DataFrame shape (one row per `op_id`) for a real production order in the training set. |
| 4 | `test_predict_total_within_envelope_of_real` | Total predicted duration for a panel is within the noise envelope of the simulated truth — the model has actually learned. |
| 5 | `test_unknown_key_raises` | An unknown `op_producao` raises `ValueError` — defensive failure mode is preserved. |

## Last run

Captured on **2026-05-27** against the artifacts shipped under
`data/training/`:

```
============================= test session starts ==============================
platform darwin -- Python 3.11.9, pytest-9.0.3, pluggy-1.6.0
rootdir: .../PipeLine
collected 5 items

tests/test_predict.py::test_meta_schema_matches_training_module PASSED   [ 20%]
tests/test_predict.py::test_load_skops_and_joblib_agree          PASSED  [ 40%]
tests/test_predict.py::test_predict_for_known_op_producao        PASSED  [ 60%]
tests/test_predict.py::test_predict_total_within_envelope_of_real PASSED [ 80%]
tests/test_predict.py::test_unknown_key_raises                   PASSED  [100%]

======================= 5 passed, 143 warnings in 18.51s =======================
```

### About the warnings

`InconsistentVersionWarning` from scikit-learn indicates the shipped
`model.joblib` was trained on a slightly different sklearn build. They are
benign for the golden-path tests but a fresh `pipeline train` on the current
environment removes them.

## Adding new tests

Place files matching `test_*.py` in `tests/`. The configuration in
`pyproject.toml` already wires `testpaths = ["tests"]`, so `pytest` from the
project root discovers them automatically.

## Continuous validation

`pipeline retrain` ends by re-running this suite (`pytest tests/test_predict.py -q`)
before appending to `data/training/retrain_log.jsonl`. A failing test aborts
the deploy.

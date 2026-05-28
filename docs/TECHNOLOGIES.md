# Technologies

A short note on what every dependency is used for and why it was chosen.

## Runtime stack

### CLI & UX

| Library | Role | Why |
|---------|------|-----|
| **Typer** | Command-line framework | Decorator-based CLI on top of Click; the whole `pipeline.cli` module is ~250 lines because Typer handles parsing, help text and subcommands. |
| **Rich** | Terminal rendering | Tables and coloured status output in `pipeline show`, `pipeline predict`, and `retrain` stages. |

### Document parsing

| Library | Role | Why |
|---------|------|-----|
| **PyMuPDF** (`fitz`) | PDF text/vector extraction | Reliable vector text extraction from BOM and CAD PDFs; faster and more accurate than pdfminer for tabular layouts. |
| **ezdxf** | DXF parsing | Native DXF reader for CAD files in DXF format (kept for future ingestion, parser scaffold present in `ingest.py`). |

### Data layer

| Library | Role | Why |
|---------|------|-----|
| **pandas** | Primary DataFrame API | All feature/training tables are pandas DataFrames before Parquet serialization. |
| **polars** | Alternate DataFrame engine | Available for performance-critical paths; complementary to pandas. |
| **pyarrow** | Parquet I/O | Backs `pd.read_parquet` / `to_parquet`. Parquet is the canonical exchange format. |
| **numpy** | Numerical arrays | Standard transitive dependency for sklearn and pandas. |
| **DuckDB** | Embedded SQL | Provides ad-hoc SQL over the Parquet tables for debugging and joins. |

### Config

| Library | Role | Why |
|---------|------|-----|
| **PyYAML** | YAML parsing | `config/panels.yaml` is loaded into the `Config` dataclass. |
| **pydantic** | Type validation | Strict validation of config objects; catches typos before they reach the pipeline. |

### Modeling

| Library | Role | Why |
|---------|------|-----|
| **scikit-learn** (`>=1.8,<1.9` pinned) | Training pipeline | Provides `Pipeline`, `ColumnTransformer`, `OrdinalEncoder`, and a half-dozen regressors (`ExtraTrees`, `RandomForest`, `GradientBoosting`, `HistGradientBoosting`, `Ridge`). The version is **pinned** because joblib model files are sensitive to API changes between minor releases. |
| **joblib** | Primary model serialization | Fast pickle-based serialization; used in `model.joblib`. |
| **skops** | Safer model serialization | Stores the same fitted estimator in a non-arbitrary-code-execution format. Both formats are validated to agree by `test_load_skops_and_joblib_agree`. |
| **rapidfuzz** | Fuzzy string matching | Reserved for future linkage work between BOM line designations and operation labels. |

### Benchmark (optional)

These are installed in dev environments only and pulled by `scripts/benchmark.py`:

| Library | Role |
|---------|------|
| **Optuna** | Bayesian hyperparameter search across booster families. |
| **CatBoost** | Native handling of categorical features without manual one-hot. |
| **LightGBM** | Fast histogram-based gradient boosting. |
| **XGBoost** | Battle-tested gradient boosting baseline. |

The benchmark writes `data/training/benchmark/leaderboard.json`. The winning
booster family is then refit by `pipeline train`.

### Analysis (optional)

| Library | Role |
|---------|------|
| **SHAP** | Per-feature contribution plots (`analysis/shap_*.png`). |
| **matplotlib** | PDP / ICE / permutation importance plots. |

## Installing extras

```bash
pip install -r requirements.txt           # runtime
pip install -e ".[benchmark]"             # for scripts/benchmark.py
pip install -e ".[analysis]"              # for scripts/analyze_model.py
pip install -e ".[dev]"                   # pytest
```

## Why Python 3.11

Pinned via `requires-python = ">=3.11"` in `pyproject.toml`. Matches the
`scikit-learn 1.8.x` line and gets `tomllib`, structural pattern matching,
and the faster CPython interpreter for parsing-heavy workloads.

## Storage format choice: Parquet

- Columnar → cheap to read only the columns you need.
- Self-describing → schema travels with the file.
- Cross-language → DuckDB, pandas, polars, Arrow all read it natively.
- Stable → no version drift between runs.

DuckDB sits on top of the Parquet files for ad-hoc SQL when needed; it is not
the source of truth.

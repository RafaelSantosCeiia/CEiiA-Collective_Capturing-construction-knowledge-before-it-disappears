# BluFab — Per-panel production time estimation

Fixathon 2026 · Casais/BluFab challenge — *Production Time Estimation by Panel*

Estimates the **production time of a modular bathroom panel**, broken down by
**micro-operation** (framing → crimping → boarding → screwing → …), from the
**technical drawing**. It reads the process PDF, extracts the panel's features,
and predicts the duration of each micro-operation — with a **confidence
interval** — feeding the cost configurator.

> **The thesis:** with the available data, the model is already **at the noise
> floor of the data itself** — it errs less (≈15s) than two humans disagree when
> timing the same task (≈20s, CV 35%). The bottleneck is not the algorithm, it is
> the **quality and quantity of data** — which is exactly what automatic video
> capture solves. That is why we always measure against the human floor, not
> against an arbitrary number.

---

## 1. End-to-end flow

```
process PDF ──split──► sub-panels ──Gemini──► 21 features ─┐
                                                           ├─► model ─► times
time Excels (human annotation) ──parse──► observed times  ─┘    per micro-op,
                                                                panel and project
                                                                (with interval)
```

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) extract geometry from the PDFs (Gemini 3.5 Flash; needs GEMINI_API_KEY)
export GEMINI_API_KEY="..."
./scripts/pipeline extract-geometry

# 2) build the training table (times ⨝ geometry)
./scripts/pipeline build-training

# 3) train: multi-model benchmark + champion-gate + champion deploy
./scripts/pipeline train --trials 50

# 4) honest scorecard (human floor vs baselines vs model)
./scripts/pipeline evaluate

# 5) estimate a new drawing (offline uses the already-extracted geometry cache)
./scripts/pipeline predict-drawing "data/raw/Desenhos Técnicos - ECOCIAF/ECOCIAF01_PANCAS_IS01A_PROCESSO 1.pdf"
```

---

## 2. Commands

| Command | What it does |
|---|---|
| `extract-geometry` | process PDFs → 21 features per sub-panel (provider Gemini/Claude/Ollama) |
| `build-training` | observed times ⨝ geometry → `training_long` / `test_long` |
| `train` | benchmark CatBoost/LGBM/XGB/stacking (+AutoGluon if installed) with Optuna, champion-gate and deploy |
| `evaluate` | LOPO scorecard: human noise floor vs baselines vs model (no deploy) |
| `predict-drawing <pdf>` | estimates times per micro-op, panel and project, with interval |
| `parse-times` | re-parse the PICUA + ECOCIAF time Excels |
| `future-build` | **[demo · fictitious data]** generates the synthetic datasets + trains the 4 *Future Vision* models (see §6) |

Useful flags: `train --no-clean` (train on raw data), `train --no-gate` (deploy
without champion-gate), `predict-drawing --provider gemini` (live extraction;
falls back to the geometry cache if the provider is unavailable).

### API, frontend and n8n

```bash
# serve the API (frontend + n8n consume this)
PYTHONPATH=src python -m uvicorn pipeline.api:app --host 127.0.0.1 --port 8000

# frontend (in-browser React, no build step)
python -m http.server 5500 -d frontend     # http://127.0.0.1:5500
```

The frontend is organised by audience, in three sidebar groups (hash routing —
`#predict`, `#metrics`, … — with deep-links and browser back/forward):

- **Operations** (shop floor + sales):
  - **Live Dashboard** — shop-floor mock (simulated data, with a *DEMO* badge and
    tooltips). It has a **Wall mode**: a kiosk view for a mounted display, with the
    in-production panel as the hero (large code + timer, readable from a distance)
    and the dense tables hidden.
  - **Predictor** — panel code or PDF → prediction. Leads with the **total +
    confidence range** (q80/q90); per-micro-op detail is collapsed by default;
    **Recent orders** (local history, one-click re-run); **CSV** export (with
    intervals) and a one-page branded **PDF quote**.
- **Model** (ML owner):
  - **Model Metrics** — model-health chip, learning curve and calibration, in
    plain language.
  - **Training** — manual retrain + scheduling (n8n triggers the retrain here).
  - **History** (*Retrain history*) — each retrain, **what changed** (Δ MAE vs the
    previous deploy), and a clickable detail modal.
- **Vision**: **Future Vision** — the §6 demonstration (fictitious data).

Predictions and state persist when switching tabs (in-memory cache).

For n8n / public exposure: set `API_KEY` in `.env` (enables the `X-API-Key`
header) and open a tunnel (`cloudflared tunnel --url http://127.0.0.1:8000` or
`ngrok http 8000`). Prediction, retrain and scheduling endpoints (and the n8n
flow) are documented in [`docs/API.md`](docs/API.md).

---

## 3. How we evaluate (the part that matters to the jury)

We don't ask "is the MAE low?". We ask **"is the model's error within the
variation with which humans measure the same task?"**. The data has 344
observations, 10 panels, ~2.6 repeated measurements per (panel × micro-op) — which
lets us measure the **human noise floor** (leave-one-observation-out):

| | LOPO MAE | Note |
|---|---|---|
| **Human noise floor** | **~13–20s** (CV 35%) | theoretical limit; no model reliably beats it |
| Global median | ~22s | naive baseline |
| Per-micro-op median | ~15s | smart baseline (the champion-gate reference) |
| **Model (champion)** | **~15–16s** | differentiates per panel; tied with the baseline *within the noise* |

- The **panel-total MAPE** (the number that goes to the configurator) is ~26%,
  much better than the ~47% per micro-op — errors cancel out in the sum.
- **Outlier cleaning** (`--clean`, default) removes ~8% of clearly mis-recorded
  observations (>3.5 MAD), logged in `removed_observations.csv`, and lowers the
  noise floor from ~20s → ~13s. It is conservative data cleaning, not make-up.
- **Conformal intervals (calibrated):** each prediction carries a band sized by
  the model's own out-of-sample residuals (relative split-conformal, per
  micro-op). Unlike heuristic bands (which promised 80% and delivered 70%), these
  **hit the target**: ~83% real coverage at 80% and ~93% at 90%, measured on
  held-out data. `predict-drawing --level q80|q90`.

---

## 4. What is functional / heuristic / mock (briefing requirement)

| Component | Status |
|---|---|
| 21-feature extraction from the PDF (Gemini, validated Pydantic schema) | **Functional** (live with API key; offline cache for the 21 already-extracted panels) |
| Parsing the time Excels → 14 canonical micro-ops | **Functional** |
| Multi-model training + Optuna + champion-gate + deploy | **Functional** |
| Prediction per micro-op / panel / project + intervals | **Functional** |
| Outlier cleaning | **Heuristic** (3.5 MAD rule, conservative, auditable) |
| Uncertainty bands (calibrated conformal) | **Functional** (relative split-conformal; coverage verified on held-out) |
| Mapping micro-ops from different observers to the 14 canonical ones | **Heuristic** (see `picua_times.py`) |
| Video capture (transition detection) | **Not implemented** — *integration designed*, see §5 |
| AutoGluon in the benchmark | **Optional** (joins if installed; does not block) |
| *Future Vision* page (4 models: waste, temperature, experience, time of day) | **Demonstrative** — **fictitious data**; illustrates patterns richer data would unlock, **not** real results (see §6) |

---

## 5. Video-ready (without building it)

Video capture is just **one more source** of the same event-log. The ingestion
boundary is a JSON:

```json
{
  "panel_id": "PG02K", "mes_order": "OP-2026-0142", "source": "cv",
  "events": [
    {"micro_op_num": 5, "micro_op_name": "Crimp frame",
     "start_sec": 0.0, "end_sec": 34.0, "duration_sec": 34.0, "confidence": 0.91}
  ]
}
```

The Excel parser already produces this format (without `start/end`). A video
transition detector emits exactly the same. Swapping the source **touches nothing
downstream** — model, retraining and prediction stay identical. More `source:"cv"`
data → the noise floor drops → the model improves on its own. That's the feedback
loop.

---

## 6. Future vision — what richer data unlocks (FICTITIOUS data)

§5 explains how video capture feeds the same event-log with far more data. This
page is an **interactive demonstration** of that future: with **fictitious data**
— generated from the *real* panel geometry, so the times make sense (bigger panel
→ more time) — we show the actionable patterns more measurements would reveal, and
which the current model (10 panels) can't see.

Four synthetic models (CatBoost, with the **same honest evaluation** as the real
pipeline — LOPO + conformal intervals):

| Model | What it demonstrates |
|---|---|
| **General** | separates productive work from two kinds of waste: *no-value idle* (random → wide interval, unpredictable) vs *material run* (systematic → narrow interval, a **clear process-optimization target**) |
| **Temperature** | productivity vs ambient temperature — best at ~20°C, much worse hot than cold |
| **Experience** | more experienced operators are consistently faster |
| **Time of day** | productivity dip after lunch and at the end of the day |

```bash
./scripts/pipeline future-build      # generates the synthetic datasets + trains the 4 models
```

In the frontend, the **Future Vision** sidebar entry opens a dedicated page: the
central estimate from the *general* model (with the waste breakdown) and, below,
**scenario curves** showing how temperature, experience and time of day move the
time. A **100% parallel** subsystem — it lives in `src/pipeline/future/` and
`data/training/future/`, with its own endpoints (`/future/*`), and **does not
touch** the real pipeline/model.

> **Important for the jury:** this section uses **made-up data** to illustrate the
> *value* of richer data — it is a proof of concept of the §5 feedback loop, not
> real results.

---

## 7. Structure

```
src/pipeline/
  cli.py              # Typer CLI (extract/build/train/evaluate/predict/parse + future-build)
  extraction/         # PDF → 21 features (Gemini/Claude/Ollama, Pydantic schema)
  picua_times.py      # time Excels → 14 canonical micro-ops
  training_table.py   # times ⨝ geometry + outlier cleaning
  estimate.py         # features, noise floor, intervals, per-panel prediction
  modeling.py         # multi-model benchmark + champion-gate + deploy
  predict_drawing.py  # PDF → prediction per micro-op/panel/project
  api.py              # HTTP API (FastAPI) — pipeline + retrain + /future/*
  future/             # [demo] future vision: synthetic data + 4 models (§6)
data/
  raw/                # PDFs, BOMs, Excels (Casais data — DO NOT publish)
  training/           # long parquets, geometry, model, scorecard
  training/future/    # [demo] synthetic datasets + the 4 Future Vision models
frontend/             # in-browser React (no build): Predictor, Metrics, …, Future Vision
```

**Monthly overnight retrain:** `./scripts/pipeline train --trials 80` runs the
full benchmark, picks the champion by LOPO, passes the champion-gate and deploys
automatically. Designed to run overnight (compute cost negligible).

---

## 8. Confidentiality

The data in `data/raw/` belongs to Casais/BluFab and must not be exposed in public
demos, publications, or reused outside the scope of the event.

# HTTP API — contract for the frontend and n8n

Wraps the prediction pipeline and retraining. What the API returns for
predictions is exactly what the `predict-drawing` CLI produces.

## Start

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...      # or put it in .env (loaded automatically)
PYTHONPATH=src python -m uvicorn pipeline.api:app --host 127.0.0.1 --port 8000
```

Interactive docs (Swagger) at `http://<host>:<port>/docs`.

## Authentication (optional)

Controlled by the `API_KEY` variable in `.env`:

- **`API_KEY` empty** → no auth (local use).
- **`API_KEY` set** → all endpoints (except `/health`) require the
  `X-API-Key: <value>` header. Use this **whenever you expose the API over a
  tunnel** (cloudflared/ngrok), because the data is confidential (Casais).

```bash
curl -H "X-API-Key: <your-key>" http://127.0.0.1:8000/model
```

In the frontend the key is stored in the browser (localStorage `blufab_api_key`);
in n8n add the `X-API-Key` header to each HTTP Request node (or a Header Auth
credential).

## Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | liveness (no auth) |
| GET | `/model` | champion metadata (UI confidence) |
| GET | `/metrics` | longitudinal metrics (learning curve, calibration, projection) |
| POST | `/predict/pdf` | PDF upload → prediction (frontend shape) |
| POST | `/predict` | prediction by panel code already in cache (`{key}`) |
| POST | `/predict-drawing` | PDF upload → prediction (raw shape, same as CLI) |
| POST | `/retrain` (alias `/train`) | starts an async retrain → `job_id` |
| GET | `/retrain/{job_id}` | job status (poll) |
| GET | `/retrain/log` | retrain history |
| GET | `/schedule` | next automatic retrain |
| POST | `/schedule` | registers the schedule (accepts `cron`) |
| GET | `/future/models` | **[demo]** metadata of the 4 *Future Vision* models |
| POST | `/future/predict` | **[demo]** *future* prediction by panel code (`{key}`) |
| POST | `/future/predict/pdf` | **[demo]** *future* prediction by PDF upload |

---

### `GET /model`
```json
{
  "champion": "catboost",
  "cv_mae_sec": 16.5,
  "n_train_obs": 315,
  "conformal_coverage": {
    "q80": {"coverage_pct": 83.5, "mean_width_sec": 56.3},
    "q90": {"coverage_pct": 93.0, "mean_width_sec": 106.2}
  },
  "features": ["largura_painel_mm", "..."]
}
```
Use `conformal_coverage` to show "80% interval → covers 83% (calibrated)".

### `GET /metrics`
Reads `data/training/metrics.json` (produced by `train`). Contains `noise_floor`,
`history` (MAE + coverage by number of panels) and `projection` (extrapolation).
`404` if there are no metrics yet → run `pipeline train`.

### `POST /predict/pdf`
`multipart/form-data` with `file` (PDF). Query: `provider`
(`gemini`|`cache`|`claude`|`ollama`), `level` (`q80`|`q90`). Returns the frontend
shape: `{key, predictions[], total_sec, total_lo_sec, total_hi_sec, panels[],
extracted, warnings}`.

### `POST /predict`
Fast prediction by a panel code already present in the geometry cache.
```json
{ "key": "PG02K", "level": "q80" }
```
`404` if the panel is not in cache (use `/predict/pdf`).

### `POST /predict-drawing`
`multipart/form-data` with `file` (PDF). Query: `provider`, `level`. Raw shape:

```bash
curl -F "file=@ISCTE_PG01K.pdf" \
  "http://127.0.0.1:8000/predict-drawing?provider=gemini&level=q80"
```
```json
{
  "project_id": "ISCTE", "interval_level": "q80", "n_panels": 1,
  "project_total_sec": 383.0, "project_total_lo_sec": 62.0, "project_total_hi_sec": 760.0,
  "panels": [
    {
      "panel_id": "PG01K", "total_sec": 383.0, "total_lo_sec": 62.0, "total_hi_sec": 760.0,
      "micro_ops": [
        {"micro_op_num": 1, "micro_op_name": "Pick profiles",
         "point_sec": 20.2, "lo_sec": 5.4, "hi_sec": 34.9}
      ]
    }
  ],
  "panels_without_geometry": []
}
```
Times in **seconds**. `lo_sec`/`hi_sec` = calibrated conformal interval. Panel
total = sum of the micro-ops; project total = sum of the panels.

> With `provider=gemini`, live extraction is attempted first; if the provider is
> unavailable it falls back to the cached geometry. Panels with no geometry
> (neither live nor cached) are listed in `panels_without_geometry`.

---

## Retraining (async) — n8n flow

`POST /retrain` starts a background job and returns the `job_id` immediately. A
real retrain takes ~30 min; **poll** `GET /retrain/{job_id}` until `status` is
terminal.

### `POST /retrain` (or `/train`)
Body (all optional):
```json
{
  "dry_run": true,
  "dry_run_outcome": "deployed",
  "dry_run_seconds": 15,
  "trials": 80,
  "require_improvement": true
}
```
- **`dry_run`** — simulates without training (to test the flow). `dry_run_outcome`
  = `deployed` | `rejected` | `failed`; `dry_run_seconds` = 1–120.
- **Real retrain** (`dry_run` absent/false): `trials` (Optuna),
  `require_improvement` (safety gate). Only **one** runs at a time (2nd request →
  `409`).

Immediate response:
```json
{ "job_id": "job_xxxx", "status": "running", "deployed": null, "started_at": "...", "params": {...} }
```

### `GET /retrain/{job_id}`
```json
{
  "job_id": "job_xxxx",
  "status": "deployed",          // running | deployed | rejected | failed
  "deployed": true,
  "started_at": "...", "finished_at": "...",
  "train_report": {"model_name": "catboost", "mae": 16.5}
}
```
On failure: `status: "failed"`, `error`, `stderr_tail`.

### `GET /retrain/log?limit=20`
```json
{ "items": [ { "job_id": "...", "status": "deployed", "train_report": {"mae": 15.6, "model_name": "catboost"},
              "prior_mae": 16.5, "improvement_pct": 5.3 } ], "count": 1 }
```
Includes in-memory jobs still running. Persisted in
`data/training/retrain_jobs.json`. Each deployed job is annotated with `prior_mae`
(the previous deploy's MAE) and `improvement_pct` (> 0 = lower error, better) —
used by the History tab's *Change* column to show "what changed".

### n8n workflow example
1. **Start Retrain** — `POST {base}/retrain` with the body above → store `job_id`.
2. **Wait** (e.g. 30s).
3. **Poll Status** — `GET {base}/retrain/{{ $('Start Retrain').item.json.job_id }}`.
4. **IF** `status == "running"` → back to Wait; otherwise branch on
   `deployed`/`rejected`/`failed`.

> In each HTTP Request node: if the API has `API_KEY`, add the `X-API-Key` header;
> otherwise, `Authentication = None`.

---

## Scheduling

### `GET /schedule`
Next automatic run. Reads `data/training/schedule.json` (recomputed from the
stored cron, so it never goes stale); if absent, returns the monthly default.
```json
{ "next_run_utc": "2026-06-01T03:00:00+00:00", "cron": "0 3 1 * *",
  "cadence": "monthly", "source": "overnight retrain (n8n)", "timezone": "UTC" }
```

### `POST /schedule`
Registers the schedule. Accepts **`cron`** (5 fields — computes the next run)
and/or **`next_run_utc`** (explicit ISO 8601):
```json
{ "cron": "0 0 1 * *", "source": "n8n" }
```
`422` if you send neither a valid `cron` (5 fields) nor `next_run_utc`.

---

## Future Vision (demo — FICTITIOUS data)

A parallel subsystem that illustrates patterns richer data would unlock (see §6 of
the README). It does **not** use the real model; it serves the 4 synthetic models
from `data/training/future/` (generated by `pipeline future-build`).

### `GET /future/models`
Metadata of the 4 models: `[{name, champion, lopo_mae, noise_floor_mae,
extra_cols, n_train_obs}]`.

### `POST /future/predict`
Prediction by a cached panel code. Body: `{ "key": "PG02K", "level": "q80" }`.
Returns the central prediction (`general`, with a productive/waste breakdown) and
the scenarios (`temperature`, `experience`, `timeofday`), each with `scenarios`
(highlight cards) and `curve` (fine grid for the chart):
```json
{
  "panel_id": "PG02K", "interval_level": "q80", "n_panels": 1,
  "general": {
    "items": [{"micro_op_num": 1, "micro_op_name": "Pick profiles",
               "point_sec": 14.0, "lo_sec": 10.1, "hi_sec": 17.9}, "..."],
    "total_sec": 599.8,
    "breakdown": {"productive_pct": 75.6, "idle_no_value_pct": 13.0, "material_necessary_pct": 11.4, "...": "..."}
  },
  "temperature": {
    "feature": "temperatura_c", "unit": "°C", "note": "...",
    "scenarios": [{"value": 10, "label": "10°C — cold", "total_sec": 649.2}, "..."],
    "curve": [{"value": 8, "total_sec": 727.0}, "..."]
  },
  "experience": { "...": "..." }, "timeofday": { "...": "..." }
}
```

### `POST /future/predict/pdf`
`multipart/form-data` with `file` (process PDF). Query: `level` (`q80`|`q90`).
Geometry comes from the cache; for multi-panel PDFs it aggregates the sub-panels
(`n_panels`, `panel_ids`, `panels_without_geometry`). Same response shape as the
endpoint above.

---

## Error codes
- `401` — `X-API-Key` missing or invalid (when `API_KEY` is set)
- `409` — a retrain is already running
- `415` — file is not a `.pdf`
- `422` — no geometry / invalid parameters
- `503` — no deployed model (run `pipeline train`)

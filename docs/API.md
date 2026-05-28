# HTTP API

FastAPI wrapper around the pipeline, intended for n8n (retrain orchestration)
and direct service-to-service calls (predict).

## Running

```bash
pip install -r requirements.txt
./scripts/api                       # binds 0.0.0.0:8000
./scripts/api 127.0.0.1 8080        # custom host/port
```

Interactive docs are auto-generated at `http://<host>:<port>/docs`
(Swagger UI) and `/redoc`.

## Endpoints

| Method | Path                  | Purpose                                    | Sync? |
|--------|-----------------------|--------------------------------------------|-------|
| GET    | `/health`             | Liveness probe                             | yes   |
| GET    | `/model`              | Deployed model metadata                    | yes   |
| POST   | `/predict`            | Predict per-op durations for one order     | yes   |
| POST   | `/retrain`            | Kick off retrain → returns `job_id`        | **async** |
| GET    | `/retrain/{job_id}`   | Status of a retrain job                    | yes   |
| GET    | `/retrain/log`        | Tail of `retrain_log.jsonl`                | yes   |

### `POST /predict`

```json
{ "key": "OP-2026-001", "prefer": "skops" }
```

Response:
```json
{
  "key": "OP-2026-001",
  "predictions": [
    { "op_id": "op001", "op_order": "0", "predicted_duration_sec": 18.65 },
    ...
  ],
  "total_sec": 312.4,
  "warnings": []
}
```

Returns `404` if the key is unknown, `503` if no model is deployed.

### `POST /predict/pdf`

`multipart/form-data` upload. Extracts the `op_producao` identifier from the
PDF text (looks for `OP-YYYY-NNN` patterns on every page) and runs the same
prediction.

```bash
curl -X POST http://api/predict/pdf -F "file=@BOM_OP_2026_001.pdf"
```

Response is the same as `/predict` plus an `extracted` object with the panel
attributes parsed from the PDF (panel_id, dimensions, material, etc.).

Error codes:
- `415` — file isn't a `.pdf`.
- `422` — PDF parsed but no `OP-…` identifier found in any page.
- `404` — identifier found, but that production order isn't in the features
  database (ingest the order and run `pipeline run-all` first).

### `POST /retrain`

```json
{ "trials": 80, "require_improvement": true, "skip_benchmark": false, "skip_tests": false }
```

**Dry run** — for testing orchestration (e.g. an n8n workflow) without
running the real benchmark for 30+ minutes. Sleeps `dry_run_seconds`, then
returns a simulated outcome with no side effects:

```json
{
  "dry_run": true,
  "dry_run_outcome": "deployed",       // or "rejected" | "failed"
  "dry_run_seconds": 15
}
```

The simulator populates `status`, `deployed`, `train_report`, `error` and
`stderr_tail` exactly the same way the real retrain does, so downstream
branching logic can be validated end-to-end.

Response (HTTP 202):
```json
{ "job_id": "a1b2c3d4e5f6", "status": "running" }
```

Retrain runs in a background thread. Poll `/retrain/{job_id}` for status:

```json
{
  "job_id": "a1b2c3d4e5f6",
  "status": "completed",
  "started_at": "2026-05-27T09:12:31",
  "finished_at": "2026-05-27T09:38:04",
  "deployed": true,
  "train_report": { "model_name": "...", "mae": 1.42, ... }
}
```

Status values: `running`, `completed`, `failed`. On failure, fields `error`,
`stderr_tail`, `stdout_tail` are populated for debugging.

> ⚠️ Jobs live in process memory. Restarting the API forgets prior `job_id`s.
> The authoritative audit trail lives in `data/training/retrain_log.jsonl`
> (read via `/retrain/log`).

## n8n workflow for monthly retrain

Five-node workflow:

1. **Cron** — `0 2 1 * *` (02:00 on the 1st of each month).
2. **HTTP Request** — `POST http://<api-host>:8000/retrain`
   - Body: `{ "trials": 80, "require_improvement": true }`
   - Capture `job_id` from the response.
3. **Wait** — 5 minutes (lets the first benchmark trials warm up; tune to your runtime).
4. **HTTP Request (loop)** — `GET /retrain/{{$json.job_id}}` with retry-until,
   condition: `{{$json.status}} !== "running"`. Use the *Polling* pattern
   (built-in node setting) or a Loop Over Items node with a Wait + IF.
5. **IF / Slack** — branch on `status` and `deployed`:
   - `completed` & `deployed=true` → Slack: "✅ Model deployed. MAE = {{$json.train_report.mae}}"
   - `completed` & `deployed=false` → Slack: "⚠️ Champion gate rejected new model. Current model retained."
   - `failed` → Slack: "❌ Retrain failed. {{$json.error}}\n{{$json.stderr_tail}}"

## n8n workflow for batch predict on new orders

1. **Google Drive Trigger** — watch a folder, fire when a BOM/CAD/OP file arrives.
2. **Function / Code** — derive the `op_producao` key from the filename.
3. **HTTP Request** — `POST /predict { "key": "<key>" }`.
4. **Google Sheets / Airtable** — append the predicted rows to a tracking sheet.

For this to work end-to-end you also need an ingest step that drops the file
into `data/raw/` and runs `pipeline features`. Until that's wired, this
workflow only works for orders already present in the training data.

## Security notes

The API has no authentication. Before exposing it beyond a private network:

- Put it behind a reverse proxy (Caddy, nginx) with TLS.
- Add an API key dependency (`fastapi.Depends`) or a JWT layer.
- Restrict `/retrain` to internal callers — it's resource-intensive.
- n8n's HTTP node supports header auth out of the box.

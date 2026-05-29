# API HTTP — contrato para o frontend e n8n

Envolve o pipeline de previsão e o retreino. O que a API devolve nas previsões é
exatamente o que o CLI `predict-drawing` produz.

## Arrancar

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...      # ou põe no .env (carregado automaticamente)
PYTHONPATH=src python -m uvicorn pipeline.api:app --host 127.0.0.1 --port 8000
```

Docs interativos (Swagger) em `http://<host>:<port>/docs`.

## Autenticação (opcional)

Controlada pela variável `API_KEY` no `.env`:

- **`API_KEY` vazio** → sem auth (uso local).
- **`API_KEY` preenchido** → todos os endpoints (exceto `/health`) exigem o header
  `X-API-Key: <valor>`. Usa isto **sempre que expões a API por túnel** (cloudflared/ngrok),
  porque os dados são confidenciais (Casais).

```bash
curl -H "X-API-Key: <a-tua-chave>" http://127.0.0.1:8000/model
```

No frontend a chave é guardada no browser (localStorage `blufab_api_key`); no n8n
adiciona o header `X-API-Key` em cada nó HTTP Request (ou uma credencial Header Auth).

## Endpoints

| Método | Rota | Para quê |
|---|---|---|
| GET | `/health` | liveness (sem auth) |
| GET | `/model` | metadados do campeão (confiança na UI) |
| GET | `/metrics` | métricas longitudinais (learning curve, calibração, projeção) |
| POST | `/predict/pdf` | upload de PDF → previsão (forma do frontend) |
| POST | `/predict` | previsão por código de painel já em cache (`{key}`) |
| POST | `/predict-drawing` | upload de PDF → previsão (forma crua, igual ao CLI) |
| POST | `/retrain` (alias `/train`) | arranca um retreino assíncrono → `job_id` |
| GET | `/retrain/{job_id}` | estado de um job (poll) |
| GET | `/retrain/log` | histórico dos retreinos |
| GET | `/schedule` | próximo retreino automático |
| POST | `/schedule` | regista o agendamento (aceita `cron`) |
| GET | `/future/models` | **[demo]** metadados dos 4 modelos da *Visão de Futuro* |
| POST | `/future/predict` | **[demo]** previsão *futuro* por código de painel (`{key}`) |
| POST | `/future/predict/pdf` | **[demo]** previsão *futuro* por upload de PDF |

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
Usa o `conformal_coverage` para mostrar "intervalo 80% → cobre 83% (calibrado)".

### `GET /metrics`
Lê `data/training/metrics.json` (gerado pelo `train`). Contém `noise_floor`,
`history` (MAE + cobertura por nº de painéis) e `projection` (extrapolação).
`404` se ainda não houver métricas → corre `pipeline train`.

### `POST /predict/pdf`
`multipart/form-data` com `file` (PDF). Query: `provider` (`gemini`|`cache`|`claude`|`ollama`),
`level` (`q80`|`q90`). Devolve a forma do frontend: `{key, predictions[], total_sec,
total_lo_sec, total_hi_sec, panels[], extracted, warnings}`.

### `POST /predict`
Previsão rápida por código de painel já presente na cache de geometria.
```json
{ "key": "PG02K", "level": "q80" }
```
`404` se o painel não estiver em cache (usa `/predict/pdf`).

### `POST /predict-drawing`
`multipart/form-data` com `file` (PDF). Query: `provider`, `level`. Forma crua:

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
        {"micro_op_num": 1, "micro_op_name": "Pegar nos perfis",
         "point_sec": 20.2, "lo_sec": 5.4, "hi_sec": 34.9}
      ]
    }
  ],
  "panels_without_geometry": []
}
```
Tempos em **segundos**. `lo_sec`/`hi_sec` = intervalo conformal calibrado.
Total do painel = soma das micro-ops; total do projeto = soma dos painéis.

---

## Retreino (assíncrono) — fluxo n8n

`POST /retrain` arranca um job em background e devolve já o `job_id`. O retreino real
demora ~30 min; faz-se **poll** a `GET /retrain/{job_id}` até o `status` ser terminal.

### `POST /retrain` (ou `/train`)
Body (tudo opcional):
```json
{
  "dry_run": true,
  "dry_run_outcome": "deployed",
  "dry_run_seconds": 15,
  "trials": 80,
  "require_improvement": true
}
```
- **`dry_run`** — simula sem treinar (para testar o fluxo). `dry_run_outcome` =
  `deployed` | `rejected` | `failed`; `dry_run_seconds` = 1–120.
- **Retreino real** (`dry_run` ausente/false): `trials` (Optuna), `require_improvement`
  (gate de segurança). Só corre **um** de cada vez (2.º pedido → `409`).

Resposta imediata:
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
Em falha: `status: "failed"`, `error`, `stderr_tail`.

### `GET /retrain/log?limit=20`
```json
{ "items": [ { "job_id": "...", "status": "deployed", "train_report": {...} } ], "count": 1 }
```
Inclui jobs em memória ainda a correr. Persistido em `data/training/retrain_jobs.json`.

### Exemplo de workflow n8n
1. **Start Retrain** — `POST {base}/retrain` com o body acima → guarda `job_id`.
2. **Wait** (ex. 30s).
3. **Poll Status** — `GET {base}/retrain/{{ $('Start Retrain').item.json.job_id }}`.
4. **IF** `status == "running"` → volta ao Wait; senão ramifica por `deployed`/`rejected`/`failed`.

> Em cada nó HTTP Request: se a API tiver `API_KEY`, adiciona o header `X-API-Key`;
> caso contrário, `Authentication = None`.

---

## Agendamento

### `GET /schedule`
Próxima execução automática. Lê `data/training/schedule.json` (recalcula a partir do
cron guardado, por isso nunca fica obsoleto); se não existir, devolve o mensal default.
```json
{ "next_run_utc": "2026-06-01T03:00:00+00:00", "cron": "0 3 1 * *",
  "cadence": "monthly", "source": "overnight retrain (n8n)", "timezone": "UTC" }
```

### `POST /schedule`
Regista o agendamento. Aceita **`cron`** (5 campos — calcula a próxima execução) e/ou
**`next_run_utc`** (ISO 8601 explícito):
```json
{ "cron": "0 0 1 * *", "source": "n8n" }
```
`422` se não enviares nem `cron` (válido, 5 campos) nem `next_run_utc`.

---

## Visão de Futuro (demo — dados FICTÍCIOS)

Subsistema paralelo que ilustra padrões que dados mais ricos desbloqueariam (ver §6
do README). **Não** usa o modelo real; serve os 4 modelos sintéticos de
`data/training/future/` (gerados por `pipeline future-build`).

### `GET /future/models`
Metadados dos 4 modelos: `[{name, champion, lopo_mae, noise_floor_mae, extra_cols, n_train_obs}]`.

### `POST /future/predict`
Previsão por código de painel em cache. Body: `{ "key": "PG02K", "level": "q80" }`.
Devolve a previsão central (`general`, com breakdown produtivo/desperdício) e os
cenários (`temperature`, `experience`, `timeofday`), cada um com `scenarios`
(cartões de destaque) e `curve` (grelha fina para o gráfico):
```json
{
  "panel_id": "PG02K", "interval_level": "q80", "n_panels": 1,
  "general": {
    "items": [{"micro_op_num": 1, "micro_op_name": "Pegar nos perfis",
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
`multipart/form-data` com `file` (PDF de processo). Query: `level` (`q80`|`q90`).
A geometria vem da cache; em PDFs multi-painel agrega os sub-painéis (`n_panels`,
`panel_ids`, `panels_without_geometry`). Mesma forma de resposta do endpoint acima.

---

## Códigos de erro
- `401` — `X-API-Key` em falta ou inválido (quando `API_KEY` está definido)
- `409` — já há um retreino a correr
- `415` — ficheiro não é `.pdf`
- `422` — sem geometria / parâmetros inválidos
- `503` — sem modelo deployado (corre `pipeline train`)

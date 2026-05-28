# API HTTP — contrato para o frontend

Envolve o pipeline de previsão. O que a API devolve é exatamente o que o CLI
`predict-drawing` produz.

## Arrancar

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...      # ou põe no .env (carregado automaticamente)
./scripts/api                  # 0.0.0.0:8000
./scripts/api 127.0.0.1 8011   # host/port custom
```

Docs interativos (Swagger) em `http://<host>:<port>/docs`.

## Endpoints

| Método | Rota | Para quê |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/model` | metadados do campeão (mostrar confiança na UI) |
| POST | `/predict-drawing` | upload de PDF → previsão |

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

### `POST /predict-drawing`
`multipart/form-data` com `file` (PDF). Query params:
- `provider` — `gemini` (default, live, precisa de chave) · `cache` (offline) · `claude` · `ollama`
- `level` — `q80` (default) · `q90`

```bash
curl -F "file=@ISCTE_PG01K.pdf" \
  "http://127.0.0.1:8000/predict-drawing?provider=gemini&level=q80"
```

Resposta:
```json
{
  "project_id": "ISCTE",
  "champion": "catboost",
  "interval_level": "q80",
  "n_panels": 1,
  "project_total_sec": 383.0,
  "project_total_lo_sec": 62.0,
  "project_total_hi_sec": 760.0,
  "panels": [
    {
      "panel_id": "PG01K",
      "total_sec": 383.0,
      "total_lo_sec": 62.0,
      "total_hi_sec": 760.0,
      "micro_ops": [
        {"micro_op_num": 1, "micro_op_name": "Pegar nos perfis",
         "point_sec": 20.2, "lo_sec": 5.4, "hi_sec": 34.9}
      ]
    }
  ],
  "panels_without_geometry": [],
  "filename": "ISCTE_PG01K.pdf"
}
```

Tempos em **segundos**. `lo_sec`/`hi_sec` = intervalo conformal calibrado.
Total do painel = soma das micro-ops; total do projeto = soma dos painéis.

Códigos de erro:
- `415` — ficheiro não é `.pdf`
- `422` — nenhum painel previsto (sem geometria; se `provider=cache` e o projeto não
  está em cache, usa `provider=gemini`)
- `503` — sem modelo deployado (corre `pipeline train`)

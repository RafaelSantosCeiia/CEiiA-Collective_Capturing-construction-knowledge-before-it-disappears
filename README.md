# BluFab — Estimativa de tempo de produção por painel

Fixathon 2026 · Desafio Casais/BluFab — *Production Time Estimation by Panel*

Estima o **tempo de produção de um painel de casa-de-banho modular**, decomposto
por **micro-operação** (framing → cravação → placagem → aparafusamento → …), a
partir do **desenho técnico**. Lê o PDF de processo, extrai as características do
painel, e prevê a duração de cada micro-operação — com **intervalo de confiança**
— alimentando o configurador de custos.

> **A tese:** com os dados disponíveis, o modelo já está **no piso de ruído dos
> próprios dados** — erra menos (≈15s) do que dois humanos discordam ao cronometrar
> a mesma tarefa (≈20s, CV 35%). O gargalo não é o algoritmo, é a **qualidade e
> quantidade de dados** — que é exatamente o que a captura automática por vídeo
> resolve. Por isso medimos sempre contra o piso humano, não contra um número no ar.

---

## 1. Fluxo end-to-end

```
PDF de processo ──split──► sub-painéis ──Gemini──► 21 features ─┐
                                                                ├─► modelo ─► tempos
Excels de tempos (anotação humana) ──parse──► tempos observados ┘    por micro-op,
                                                                     painel e projeto
                                                                     (com intervalo)
```

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) extrair geometria dos PDFs (Gemini 3.5 Flash; precisa de GEMINI_API_KEY)
export GEMINI_API_KEY="..."
./scripts/pipeline extract-geometry

# 2) construir a tabela de treino (tempos ⨝ geometria)
./scripts/pipeline build-training

# 3) treinar: benchmark multi-modelo + champion-gate + deploy do campeão
./scripts/pipeline train --trials 50

# 4) scorecard honesto (piso humano vs baselines vs modelo)
./scripts/pipeline evaluate

# 5) estimar um desenho novo (offline usa a cache de geometria já extraída)
./scripts/pipeline predict-drawing "data/raw/Desenhos Técnicos - ECOCIAF/ECOCIAF01_PANCAS_IS01A_PROCESSO 1.pdf"
```

---

## 2. Comandos

| Comando | O que faz |
|---|---|
| `extract-geometry` | PDFs de processo → 21 features por sub-painel (provider Gemini/Claude/Ollama) |
| `build-training` | tempos observados ⨝ geometria → `training_long` / `test_long` |
| `train` | benchmark CatBoost/LGBM/XGB/stacking (+AutoGluon se instalado) com Optuna, champion-gate e deploy |
| `evaluate` | scorecard LOPO: piso de ruído humano vs baselines vs modelo (sem deploy) |
| `predict-drawing <pdf>` | estima tempos por micro-op, painel e projeto, com intervalo |
| `parse-times` | re-parsear os Excels de tempos PICUA + ECOCIAF |

Flags úteis: `train --no-clean` (treina com dados crus), `train --no-gate`
(deploy sem champion-gate), `predict-drawing --provider gemini` (extração live).

### API, frontend e n8n

```bash
# servir a API (frontend + n8n consomem esta)
PYTHONPATH=src python -m uvicorn pipeline.api:app --host 127.0.0.1 --port 8000

# frontend (React in-browser, sem build)
python -m http.server 5500 -d frontend     # http://127.0.0.1:5500
```

Páginas do frontend: **Live Dashboard** (mock de chão de fábrica, dados simulados),
**Predictor** (PDF → previsão por painel/micro-op + export PDF/CSV), **Model Metrics**
(curva de aprendizagem e calibração ao longo do tempo), **Training** e **History**
(retreino manual + agendamento).

Para n8n / exposição pública: define `API_KEY` no `.env` (ativa o header `X-API-Key`)
e abre um túnel (`cloudflared tunnel --url http://127.0.0.1:8000` ou `ngrok http 8000`).
Endpoints de previsão, retreino e agendamento (e o fluxo n8n) estão em
[`docs/API.md`](docs/API.md).

---

## 3. Como avaliamos (a parte que interessa ao júri)

Não perguntamos "o MAE é baixo?". Perguntamos **"o erro do modelo está dentro da
variação com que humanos medem a mesma tarefa?"**. Os dados têm 344 observações,
10 painéis, ~2,6 medições repetidas por (painel × micro-op) — o que permite medir
o **piso de ruído humano** (leave-one-observation-out):

| | MAE LOPO | Nota |
|---|---|---|
| **Piso de ruído humano** | **~13–20s** (CV 35%) | limite teórico; nenhum modelo o bate de forma fiável |
| Mediana global | ~22s | baseline ingénua |
| Mediana por micro-op | ~15s | baseline esperta (referência do champion-gate) |
| **Modelo (campeão)** | **~15–16s** | diferencia por painel; empatado com a baseline *dentro do ruído* |

- O **MAPE no total do painel** (o número que vai para o configurador) é ~26%,
  muito melhor que os ~47% por micro-op — os erros cancelam-se na soma.
- A **limpeza de outliers** (`--clean`, default) remove ~8% de observações
  claramente mal gravadas (>3,5 MAD), registadas em `removed_observations.csv`, e
  baixa o piso de ruído de ~20s → ~13s. É data cleaning conservador, não maquilhagem.
- **Intervalos conformais (calibrados):** cada previsão traz uma banda dimensionada
  pelos resíduos out-of-sample do próprio modelo (split-conformal relativo, por
  micro-op). Ao contrário de bandas heurísticas (que prometiam 80% e entregavam
  70%), estas **acertam no alvo**: ~83% de cobertura real a 80% e ~93% a 90%,
  medido em held-out. `predict-drawing --level q80|q90`.

---

## 4. O que é funcional / heurístico / mock (requisito do briefing)

| Componente | Estado |
|---|---|
| Extração de 21 features do PDF (Gemini, schema Pydantic validado) | **Funcional** (live com API key; cache offline para os 21 painéis já extraídos) |
| Parsing dos Excels de tempos → 14 micro-ops canónicas | **Funcional** |
| Treino multi-modelo + Optuna + champion-gate + deploy | **Funcional** |
| Previsão por micro-op / painel / projeto + intervalos | **Funcional** |
| Limpeza de outliers | **Heurístico** (regra 3,5 MAD, conservadora, auditável) |
| Bandas de incerteza (conformal calibrado) | **Funcional** (split-conformal relativo; cobertura verificada em held-out) |
| Mapeamento das micro-ops de observadores diferentes p/ 14 canónicas | **Heurístico** (ver `picua_times.py`) |
| Captura por vídeo (deteção de transições) | **Não implementado** — *integração desenhada*, ver §5 |
| AutoGluon no benchmark | **Opcional** (entra se instalado; não bloqueia) |

---

## 5. Pronto para vídeo (sem o construir)

A captura por vídeo é só **mais uma fonte** do mesmo event-log. A fronteira de
ingestão é um JSON:

```json
{
  "panel_id": "PG02K", "mes_order": "OP-2026-0142", "source": "cv",
  "events": [
    {"micro_op_num": 5, "micro_op_name": "Cravação 1",
     "start_sec": 0.0, "end_sec": 34.0, "duration_sec": 34.0, "confidence": 0.91}
  ]
}
```

O parser de Excel já produz este formato (sem `start/end`). Um detetor de
transições por vídeo emite exatamente o mesmo. Trocar a fonte **não toca em nada
a jusante** — modelo, retreino e previsão ficam iguais. Mais dados `source:"cv"`
→ piso de ruído desce → modelo melhora sozinho. É o feedback loop.

---

## 6. Estrutura

```
src/pipeline/
  cli.py              # Typer CLI (6 comandos)
  extraction/         # PDF → 21 features (Gemini/Claude/Ollama, schema Pydantic)
  picua_times.py      # Excels de tempos → 14 micro-ops canónicas
  training_table.py   # tempos ⨝ geometria + limpeza de outliers
  estimate.py         # features, piso de ruído, intervalos, previsão por painel
  modeling.py         # benchmark multi-modelo + champion-gate + deploy
  predict_drawing.py  # PDF → previsão por micro-op/painel/projeto
data/
  raw/                # PDFs, BOMs, Excels (dados Casais — NÃO versionar publicamente)
  training/           # parquets long, geometria, modelo, scorecard
```

**Retreino noturno mensal:** `./scripts/pipeline train --trials 80` corre o
benchmark completo, escolhe o campeão por LOPO, passa o champion-gate e faz deploy
automático. Pensado para correr de madrugada (custo de compute irrelevante).

---

## 7. Confidencialidade

Os dados em `data/raw/` são da Casais/BluFab e não devem ser expostos em demos
públicas, publicações, ou reutilizados fora do âmbito do evento.

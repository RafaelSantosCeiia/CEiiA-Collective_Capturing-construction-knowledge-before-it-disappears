# 21-feature extraction pipeline from the PDFs

Each ECOCIAF sub-panel spans 2–4 pages in the process PDF
(`ECOCIAF01_PANCAS_IS01A_PROCESSO 1.pdf` etc.). This pipeline:

1. Detects each sub-panel by its title (`ECOCIAF01_<PANEL_ID>`).
2. Extracts only that panel's pages.
3. Sends them to the chosen provider with a single prompt.
4. Validates the response against the Pydantic schema (21 features + 4 keys).
5. Writes to `data/training/panel_geometry.parquet`.

## Chosen model — **Gemini 3.5 Flash**

Default provider. Manual inspection against a handful of panels (PG02K, PCT01K, …)
showed good fidelity to the drawing dimensions. Latency ~13 s/panel, cost
~$0.0003/panel. For the ~21 ECOCIAF sub-panels: a few minutes, ~$0.007 total.

> **Heuristic/inferred:** the extraction is validated by the Pydantic schema
> (types + physical bounds), but the values were not audited field-by-field
> against every drawing. Treat as "inferred with sanity validation", not "truth".

## Supported providers

| Provider | Default model | Where it runs | Approximate cost |
|---|---|---|---|
| **`gemini`** (default) | `gemini-3.5-flash` | Cloud, free tier OK | ~$0.0003 per panel |
| `claude` | `claude-sonnet-4-6` | Cloud, MAX plan | ~$0.01–0.03 per panel |
| `ollama` | `qwen2.5vl:7b` | Local (Ollama) | Free |

To add another provider, create `src/pipeline/extraction/extractors/<name>.py`
that extends `Extractor` and register it with `@register("name")`.

## Configuration

```bash
# For Gemini (default choice)
export GEMINI_API_KEY="AQ..."          # or GOOGLE_API_KEY

# For Claude
export ANTHROPIC_API_KEY="sk-ant-…"

# For Ollama (runs locally)
ollama serve
ollama pull qwen2.5vl:7b
```

## Commands

```bash
# Extract all 22 panels (Gemini by default)
./scripts/pipeline extract-geometry

# Specific provider
./scripts/pipeline extract-geometry --provider claude

# Only some panels
./scripts/pipeline extract-geometry --panels PG02K,PCT01K

# Re-extract (overwrite) panels already in the parquet
./scripts/pipeline extract-geometry --overwrite
```

## Output schema — `panel_geometry.parquet`

Defined in `src/pipeline/extraction/schema.py`. 25 columns (4 join keys + 21
features):

**Keys:** `panel_id`, `is_id`, `project_id`, `drawing_revision`

**Metal structure (10):** `largura_painel_mm`, `altura_painel_mm`,
`profundidade_painel_mm`, `largura_perfil_mm`, `espessura_perfil_mm`,
`num_montantes`, `num_raias`, `comprimento_montante_mm`, `comprimento_raia_mm`,
`num_furos_raia`

**Boarding (6):** `num_placas_por_face`, `perimetro_placa_total_mm`,
`perimetro_placa_maior_mm`, `espessura_placa_mm`, `placagem_dupla`, `tem_entalhes`

**Archetype (5):** `codigo_painel`, `e_tecto`, `e_pavimento`, `e_porta`,
`e_zona_humida`

> The feature column names are kept in Portuguese because they match the dataset
> columns the model trains on; renaming them would break the join. UI labels are
> English (see `MICRO_OP_NAMES` in `estimate.py`).

It joins with `ecociaf_times_long.parquet` on `panel_id` to produce the training
tables.

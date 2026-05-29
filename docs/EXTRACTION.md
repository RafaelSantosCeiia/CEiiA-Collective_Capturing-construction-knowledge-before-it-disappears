# Pipeline de extracção das 21 features dos PDFs

Cada sub-painel ECOCIAF tem 2–4 páginas no PDF de processo (`ECOCIAF01_PANCAS_IS01A_PROCESSO 1.pdf` etc.). Esta pipeline:

1. Detecta cada sub-painel pelo título (`ECOCIAF01_<PANEL_ID>`).
2. Extrai só as páginas desse painel.
3. Envia ao provider escolhido com um prompt único em PT.
4. Valida a resposta contra o schema Pydantic (21 features + 4 chaves).
5. Grava em `data/training/panel_geometry.parquet`.

## Modelo escolhido — **Gemini 3.5 Flash**

Provider default. Inspecção manual contra um punhado de painéis (PG02K, PCT01K, …)
mostrou boa fidelidade às cotas do desenho. Latência ~13 s/painel, custo
~$0,0003/painel. Para os ~21 sub-painéis ECOCIAF: poucos minutos, ~$0,007 total.

> **Heurístico/inferido:** a extração é validada pelo schema Pydantic (tipos +
> limites físicos), mas os valores não foram auditados campo-a-campo contra todos
> os desenhos. Tratar como "inferido com validação de sanidade", não "verdade".

## Providers suportados

| Provider | Modelo default | Onde corre | Custo aproximado |
|---|---|---|---|
| **`gemini`** (default) | `gemini-3.5-flash` | Cloud, free tier OK | ~$0,0003 por painel |
| `claude` | `claude-sonnet-4-6` | Cloud, plano MAX | ~$0,01–0,03 por painel |
| `ollama` | `qwen2.5vl:7b` | Local (Ollama) | Grátis |

Para adicionar outro provider, cria `src/pipeline/extraction/extractors/<nome>.py` que extende `Extractor` e regista-se com `@register("nome")`.

## Configuração

```bash
# Para Gemini (escolha por defeito)
export GEMINI_API_KEY="AQ..."          # ou GOOGLE_API_KEY

# Para Claude
export ANTHROPIC_API_KEY="sk-ant-…"

# Para Ollama (corre localmente)
ollama serve
ollama pull qwen2.5vl:7b
```

## Comandos

```bash
# Extrair todos os 22 painéis (Gemini por defeito)
./scripts/pipeline extract-geometry

# Provider específico
./scripts/pipeline extract-geometry --provider claude

# Só alguns painéis
./scripts/pipeline extract-geometry --panels PG02K,PCT01K

# Re-extrair (overwrite) painéis já no parquet
./scripts/pipeline extract-geometry --overwrite
```

## Schema de saída — `panel_geometry.parquet`

Definido em `src/pipeline/extraction/schema.py`. 25 colunas (4 chaves de junção + 21 features):

**Chaves:** `panel_id`, `is_id`, `project_id`, `drawing_revision`

**Estrutura metálica (10):** `largura_painel_mm`, `altura_painel_mm`, `profundidade_painel_mm`, `largura_perfil_mm`, `espessura_perfil_mm`, `num_montantes`, `num_raias`, `comprimento_montante_mm`, `comprimento_raia_mm`, `num_furos_raia`

**Placagem (6):** `num_placas_por_face`, `perimetro_placa_total_mm`, `perimetro_placa_maior_mm`, `espessura_placa_mm`, `placagem_dupla`, `tem_entalhes`

**Arquétipo (5):** `codigo_painel`, `e_tecto`, `e_pavimento`, `e_porta`, `e_zona_humida`

Junta-se com `ecociaf_times_long.parquet` em `panel_id` para produzir a `training_clean.parquet`.

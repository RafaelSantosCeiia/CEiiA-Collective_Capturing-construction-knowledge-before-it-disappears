# Relatório técnico — Pipeline de ingestão multimodal

## Objetivo
Construir uma pipeline local, modular e idempotente que ingere ficheiros
reais de três tipos (vídeo, CAD, BOM), associa-os por assembly, normaliza
em camadas e produz datasets prontos para CatBoost — incluindo uma
simulação determinística de tempos sintéticos por micro-tarefa.

## Stack escolhida
| componente   | escolha                  | porquê                                                                 |
|--------------|--------------------------|------------------------------------------------------------------------|
| Linguagem    | Python 3                 | ecossistema de PDF/DXF/vídeo + pandas/ML                               |
| BOM PDF      | PyMuPDF (`fitz`)         | extração de texto vetorial fiável, sem OCR                             |
| CAD          | PyMuPDF + ezdxf          | suporta PDF e DXF (os ficheiros reais eram DXF, não PDF)               |
| Vídeo        | ffprobe → OpenCV         | metadata rica via ffprobe; fallback puro Python                        |
| Storage      | DuckDB + Parquet         | upsert simples, joins SQL, inspeção universal                          |
| Schema       | pydantic v2              | validação de config                                                    |
| CLI          | Typer + Rich             | comandos limpos, output legível                                        |
| Dedupe       | sha256 + PK upsert       | re-runs idempotentes                                                   |

## Fluxo
1. **Discovery** (`discovery.py`): walks `data/raw/`, calcula sha256,
   classifica por extensão + hints de nome + peek de conteúdo, extrai
   guesses de `assembly_id`/`drawing_ref`/`bom_ref`/`revision` por regex.
2. **Parse runner** (`parse_runner.py`): despacha cada documento ao parser
   correto, popula tabelas normalizadas, marca `parse_status`.
3. **Bundles** (`bundles.py`): agrupa por `assembly_id`, computa
   `linkage_status` ∈ {matched, partial, orphan, ambiguous} e back-fill
   `bundle_id` em tabelas filhas.
4. **Linkage** (`linkage.py`): para cada `bom_item`, procura `cad_item_evidence`
   por `(assembly_id, item_nr)`; liga vídeo pelo bundle. Confidence é blend.
5. **Simulação** (`simulation.py`): regras determinísticas baseadas em
   features reais ingeridas, ruído gaussiano com σ função de
   `linkage_confidence`, seed por linha derivada de SHA-256.
6. **Export** (`export.py`): junta BOM + CAD features + video + linkage,
   produz `training_microtasks` (por micro-tarefa) e `training_items`
   (agregado), declara colunas categóricas em `catboost_schema.json`.

## Estratégia de idempotência
- `documents_inventory.sha256` permite detectar duplicados antes de gastar
  CPU em parsing (já há método `Storage.has_hash`; o ingest copia sem
  sobrescrever e o discovery refaz hash → upsert por PK).
- Cada `upsert` é uma operação **read → concat → drop_duplicates(PK, keep=last) → atomic write**.
- Simulação faz `replace` total: é barata e elimina drift se mudarem
  regras/seed.
- Re-correr `run-all` num diretório igual deixa todas as contagens estáveis
  (verificado: 10/5/64/148/64/7400/7400/64 inalterados).

## Pontos onde evoluir (não bloqueia a v1)
- **Vídeo**: hoje só metadata. Estrutura de `video_features` aceita
  duration/fps/dims; pode crescer para frame sampling + detecção de ação.
- **CAD PDF**: contagem de objetos vetoriais e `dimension_count` em PDF
  estão conservadoras (a maioria dos ficheiros de exemplo eram DXF).
- **Linkage**: hoje a chave é `(assembly_id, item_nr)`. Para casos
  ambíguos pode-se adicionar fuzzy match (rapidfuzz) sobre `designacao`.
- **Material family**: heurística simples; um dicionário maior melhora a
  feature `material_family` sem mudar arquitetura.

## Como verificar
```bash
./scripts/pipeline run-all
./scripts/pipeline report
./scripts/pipeline query "SELECT * FROM training_microtasks LIMIT 5"
```

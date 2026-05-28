"""Extraction prompt (PT) with the BluFab construction vocabulary.

Same prompt for every provider — only the request mechanics differ.
"""
from __future__ import annotations


SYSTEM_PROMPT = """És um assistente que extrai features de geometria a partir \
de desenhos técnicos de painéis modulares de casa-de-banho da BluFab (projecto \
ECOCIAF). Respondes SEMPRE com JSON estrito que cumpre o schema fornecido. \
Não inventas valores: se algo não estiver claramente legível no desenho, \
escolhes o valor mais provável com base no contexto vizinho e flagas \
internamente como incerteza."""


USER_PROMPT_TEMPLATE = """Estás a olhar para todas as páginas do desenho \
técnico de UM sub-painel ECOCIAF (panel_id = `{panel_id}`, is_id = `{is_id}`, \
project_id = `{project_id}`, drawing_revision = `{drawing_revision}`).

Cada sub-painel tem 2-4 páginas no PDF:
  • "Kit Perfis" (estrutura metálica) — vista FRENTE, Corte de Perfis, \
isométrico, tabela de peças no fundo
  • "Kit Placas" (revestimento) — vista Corte/Placagem, Posição, isométrico, \
tabela de peças

VOCABULÁRIO BLUFAB (usado literalmente nos desenhos):
  • Perfil      = peça de aço dobrado em U (família de Montantes e Raias)
  • Montante    = perfil vertical (part code: `M48-09-2171` = Montante 48mm × 0,9mm × 2171mm)
  • Raia        = perfil horizontal (part code: `R48-09-910` = Raia 48mm × 0,9mm × 910mm)
  • Placa       = folha de gesso cartonado (part code: `GGP-2270-906-12,5` = 2270mm × 906mm × 12,5mm)
  • Placagem    = acto de fixar as placas ao perfilado
  • Furos       = buracos pré-feitos nas raias (anotados `<n>xØ<diâmetro>`, ex.: `4xØ35`)
  • Entalhe     = recorte em L nos cantos da placa
  • Codigo painel = sigla na legenda DWG NO (ex.: `ECOCIAF01_PCT01K` → `PCT`)

FEATURES A EXTRAIR (21 no total):

Estrutura metálica (de "Kit Perfis"):
  largura_painel_mm       = última cota horizontal na vista FRENTE
  altura_painel_mm        = cota vertical na vista FRENTE
  profundidade_painel_mm  = cota vertical na vista "Corte de Perfis"
  largura_perfil_mm       = primeiro número do part code do Montante (M48 → 48)
  espessura_perfil_mm     = token central do part code (M48-09-2171 → 0.9)
  num_montantes           = QTY da linha "Montante" na tabela de peças
  num_raias               = QTY da linha "Raia"
  comprimento_montante_mm = último número do part code do Montante (M48-09-2171 → 2171)
  comprimento_raia_mm     = último número do part code da Raia
  num_furos_raia          = soma dos N nas anotações `<n>xØ...` perto do ITEM 2 \
detail (no canto inferior-esquerdo). Se não houver anotação, devolve 0.

Placagem (de "Kit Placas"):
  num_placas_por_face     = soma das QTY de todas as linhas na tabela de peças \
do Kit Placas (NÃO o número de linhas — uma linha pode ter QTY > 1). \
Ex.: PT01K tem 2 placas iguais + 1 mais estreita → num_placas_por_face = 3.
  perimetro_placa_total_mm = SOMA de 2(L+W) de todas as placas (considerando QTY). \
Ex.: 2× placas 1963×1200 + 1× placa 1963×443 → 2×2(1963+1200) + 2(1963+443) = 17464.
  perimetro_placa_maior_mm = 2(L+W) da placa de maior área individual. \
Ex.: no caso anterior → 2(1963+1200) = 6326.
  espessura_placa_mm      = último token do part code (GGP-2270-906-12,5 → 12,5). \
Todas as placas do mesmo painel têm a mesma espessura.
  placagem_dupla          = TRUE se o título da vista Corte for "1ª Placagem" \
(implica que há uma 2ª placagem). FALSE se for só "Placagem". Confirma com a \
razão Σ(área placas) / (largura_painel × altura_painel): ≈1 → simples; ≈2 → dupla.
  tem_entalhes            = TRUE se a placa na vista Corte tiver canto não-rectangular \
(forma em L/degrau) E houver uma vista ampliada `A(1:6)` / `E(1:6)` separada \
no canto inferior com cotas pequenas tipo "50×55" ou "85×45". \
NÃO confundir com os detalhes A/B/C/D da vista "Posição" (1:4) — esses são \
folgas normais de 2-3mm, não entalhes.

Arquétipo (da legenda DWG NO):
  codigo_painel  = sigla extraída do panel_id (PCT01K → PCT, PCK02K → PCK, PT01K → PT, etc.)
  e_tecto        = True se codigo_painel == "PT"
  e_pavimento    = True se codigo_painel == "PVB"
  e_porta        = True se codigo_painel == "PP"
  e_zona_humida  = True se codigo_painel ∈ {{"PCT", "PCK", "PCL"}}

Devolve APENAS o objecto JSON, sem prefácio, sem markdown, sem ```json``` fences. \
Inclui obrigatoriamente os 4 campos de identificação (`panel_id`, `is_id`, \
`project_id`, `drawing_revision`) e as 21 features."""


def build_user_prompt(panel_id: str, is_id: str, project_id: str, drawing_revision: str) -> str:
    return USER_PROMPT_TEMPLATE.format(
        panel_id=panel_id,
        is_id=is_id,
        project_id=project_id,
        drawing_revision=drawing_revision,
    )

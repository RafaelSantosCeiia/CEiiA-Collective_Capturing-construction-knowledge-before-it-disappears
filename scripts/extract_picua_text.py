"""Extracção determinística (PyMuPDF) de features dos PDFs PICUA.

Tudo o que sai do texto vectorial:
  - dimensões (FRENTE + Corte)
  - part codes (perfil section/thickness/length, placa dims)
  - QTYs (n_montantes, n_raias, n_placas)
  - drilling annotations (n_furos_raia)
  - placagem_dupla (título "1ª Placagem")
  - codigo_painel (do DWG NO)

Visual-only: tem_entalhes (precisa de inspecção da imagem).
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import fitz
import pandas as pd

from pipeline.extraction.schema import derive_archetype_booleans
from pipeline.extraction.splitter import split_pdf


# Painéis PICUA cronometrados
NEEDED = ['PCK01K','PCK02K','PCL01K','PCL02K','PCT01K','PG02K','PG03K','PG04K','PL01K','PS01K']


def _to_int(s: str) -> int | None:
    try:
        # "12,5" → 12.5 só para placas. Aqui ints puros.
        return int(s.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def _to_float(s: str) -> float | None:
    try:
        return float(s.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def parse_panel(text_by_page: list[str], panel_id: str, project_id: str, is_id: str, rev: str) -> dict:
    """text_by_page = list of page texts for the sub-panel (já filtradas)."""
    out: dict = {
        "panel_id": panel_id,
        "is_id": is_id,
        "project_id": project_id,
        "drawing_revision": rev,
    }

    all_text = "\n".join(text_by_page)

    # --- Part codes ---
    # Montante: M48-09-2171 OU M48-0,9-2222 OU M-48-09-2171
    mont_re = re.compile(r"M[-]?(\d+)[-]?(\d+,?\d*)[-]?(\d+)")
    raia_re = re.compile(r"R[-]?(\d+)[-]?(\d+,?\d*)[-]?(\d+)")
    placa_re = re.compile(r"GG[A-Z][-_](\d+)[-_](\d+)[-_](\d+,?\d*)")

    # Procurar Montante e Raia primeiro no contexto "Montante - WxTxL" ou no part code
    desc_mont = re.search(r"Montante\s*-?\s*(\d+)\s*x\s*(\d+,?\d*)\s*x\s*(\d+)", all_text, re.IGNORECASE)
    desc_raia = re.search(r"Raia\s*-?\s*(\d+)\s*x\s*(\d+,?\d*)\s*x\s*(\d+)", all_text, re.IGNORECASE)

    if desc_mont:
        out["largura_perfil_mm"] = int(desc_mont.group(1))
        out["espessura_perfil_mm"] = float(desc_mont.group(2).replace(",", "."))
        out["comprimento_montante_mm"] = int(desc_mont.group(3))
    else:
        # Fallback: part code do montante
        for m in mont_re.finditer(all_text):
            if not m.group(0).startswith("M"):
                continue
            out["largura_perfil_mm"] = int(m.group(1))
            esp = m.group(2).replace(",", ".")
            out["espessura_perfil_mm"] = float(esp) / 10 if len(esp) == 2 else float(esp)
            out["comprimento_montante_mm"] = int(m.group(3))
            break

    if desc_raia:
        # Raia largura igual ao montante (ou +2 mm de alma); confiar montante
        out["comprimento_raia_mm"] = int(desc_raia.group(3))
    else:
        for m in raia_re.finditer(all_text):
            out["comprimento_raia_mm"] = int(m.group(3))
            break

    # --- QTYs Montante / Raia (procurar "Montante" seguido de número, ou contexto da tabela) ---
    # A tabela tem padrão tipo "<QTY>\n<part_code>\n<DESCRIPTION>"
    # Procurar números pequenos (1-15) antes de "Montante" ou "Raia"
    lines = all_text.splitlines()
    # Pode haver MÚLTIPLAS linhas "Montante" ou "Raia" se há tipos
    # diferentes do mesmo perfil. Somar todos.
    num_montantes = 0
    num_raias = 0
    for i, ln in enumerate(lines):
        ln_clean = ln.strip()
        if "Montante -" in ln_clean:
            for j in range(i+1, min(len(lines), i+3)):
                v = lines[j].strip()
                if v.isdigit() and 1 <= int(v) <= 20:
                    num_montantes += int(v)
                    break
        elif ln_clean.startswith("Raia -"):
            for j in range(i+1, min(len(lines), i+3)):
                v = lines[j].strip()
                if v.isdigit() and 1 <= int(v) <= 20:
                    num_raias += int(v)
                    break

    out["num_montantes"] = num_montantes if num_montantes else None
    out["num_raias"] = num_raias if num_raias else None

    # --- Dimensões da vista FRENTE ---
    # Cotas do tipo "910 - 1", "2173 -1", "1062 -1"
    cota_re = re.compile(r"(\d{2,4})\s*-?\s*1\b")
    cotas = [int(m.group(1)) for m in cota_re.finditer(all_text)]
    cotas = [c for c in cotas if 100 < c < 4000]
    # As maiores são a altura e largura. Multiple "-1" mean tolerance.
    # Heuristic: largura = comprimento_raia, altura = mid-range
    if "comprimento_raia_mm" in out:
        out["largura_painel_mm"] = out["comprimento_raia_mm"]
    if "comprimento_montante_mm" in out:
        # altura é montante + 2x espessura raia ≈ montante + ~2-5mm
        out["altura_painel_mm"] = out["comprimento_montante_mm"] + 2

    # profundidade ≈ largura do perfil
    out["profundidade_painel_mm"] = out.get("largura_perfil_mm")

    # --- Furos nas raias: padrões tipo "2xØ35", "4xØ35", "3 x Ø40" ---
    furos_re = re.compile(r"(\d+)\s*x\s*[ØO]\s*(\d+)")
    total_furos = 0
    for m in furos_re.finditer(all_text):
        total_furos += int(m.group(1))
    out["num_furos_raia"] = total_furos

    # --- Placas: 1+ rows na tabela do Kit Placas ---
    placas: list[tuple[int, int, int, float]] = []
    # Procura por padrão: QTY (linha) seguida de part-code da placa
    placa_qty_re = re.compile(r"(\d+)\s*\n\s*(GG[A-Z][-_]\d+[-_]\d+[-_]\d+,?\d*)")
    for m in placa_qty_re.finditer(all_text):
        qty = int(m.group(1))
        if qty > 10:  # sanidade
            continue
        code = m.group(2)
        pm = placa_re.match(code)
        if pm:
            L, W, T = int(pm.group(1)), int(pm.group(2)), float(pm.group(3).replace(",", "."))
            placas.append((qty, L, W, T))
    if not placas:
        for m in placa_re.finditer(all_text):
            L, W, T = int(m.group(1)), int(m.group(2)), float(m.group(3).replace(",", "."))
            placas.append((1, L, W, T))

    # --- Placagem dupla PRIMEIRO (precisamos para escalar num_placas) ---
    out["placagem_dupla"] = bool(re.search(r"1\s*[ªa]\s*Placagem", all_text, re.IGNORECASE))

    if placas:
        total_qty = sum(p[0] for p in placas)
        # Se placagem dupla, total inclui ambas as faces; per_face = total/2
        out["num_placas_por_face"] = max(1, total_qty // 2) if out["placagem_dupla"] else total_qty
        out["perimetro_placa_total_mm"] = sum(qty * 2 * (L + W) for qty, L, W, _ in placas)
        biggest = max(placas, key=lambda p: p[1] * p[2])
        out["perimetro_placa_maior_mm"] = 2 * (biggest[1] + biggest[2])
        out["espessura_placa_mm"] = placas[0][3]

    # --- Entalhes: vista A(1:6) ou E(1:6) (escala alta) sugere ampliação de canto ---
    out["tem_entalhes"] = bool(re.search(r"\b[A-Z]\s*\(\s*1\s*:\s*[68]\s*\)", all_text))
    # também marcar se houver detalhe de canto não-rectangular (cotas pequenas em 1:8)
    # Esta heurística vai dar falsos positivos. Refinaremos visualmente.

    # --- Codigo painel ---
    code_match = re.match(r"^(P[A-Z]+)", panel_id)
    if code_match:
        out["codigo_painel"] = code_match.group(1)
    else:
        out["codigo_painel"] = panel_id[:3]
    out.update(derive_archetype_booleans(out["codigo_painel"]))

    return out


def main():
    panel_to_chunk = {}
    for pdf in sorted(Path("data/raw/Desenhos Técnicos - PICUA").glob("*PROCESSO*.pdf")):
        for c in split_pdf(pdf):
            if c.panel_id in NEEDED and c.panel_id not in panel_to_chunk:
                panel_to_chunk[c.panel_id] = c

    out_path = Path("data/training/picua_geometry.parquet")
    # Carregar PG02K do Gemini (se já lá está)
    existing = {}
    if out_path.exists():
        for _, r in pd.read_parquet(out_path).iterrows():
            existing[r["panel_id"]] = r.to_dict()

    rows = list(existing.values())
    for pid in NEEDED:
        if pid in existing:
            print(f"  {pid}  já tem (do Gemini)")
            continue
        c = panel_to_chunk[pid]
        doc = fitz.open(c.source_pdf)
        texts = [doc[pn - 1].get_text() for pn in c.page_numbers]
        doc.close()
        parsed = parse_panel(texts, pid, c.project_id, c.is_id, c.drawing_revision)
        rows.append(parsed)
        print(f"  {pid}  parsed: w={parsed.get('largura_painel_mm')}  h={parsed.get('altura_painel_mm')}  M={parsed.get('num_montantes')}  R={parsed.get('num_raias')}  furos={parsed.get('num_furos_raia')}  placas={parsed.get('num_placas_por_face')}  dupla={parsed.get('placagem_dupla')}  entalhes={parsed.get('tem_entalhes')}")

    df = pd.DataFrame(rows).sort_values("panel_id").reset_index(drop=True)
    df.to_parquet(out_path, index=False)
    print(f"\n✅ {out_path}  ({len(df)} painéis)")
    return df


if __name__ == "__main__":
    main()

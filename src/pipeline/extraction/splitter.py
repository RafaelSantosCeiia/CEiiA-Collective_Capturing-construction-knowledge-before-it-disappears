"""Split an ECOCIAF process PDF into per-sub-panel page groups.

Strategy: scan every page, find `ECOCIAF<N>_<PANEL>` in the page text (it appears
in the title block multiple times), group pages by panel.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


_DWG_RE = re.compile(
    r"(ECOCIAF|PICUALT|ROBIDOS)(\d*)[_ ]([A-Z]+\d+[A-Z]?)", re.IGNORECASE
)
_IS_RE = re.compile(r"\b(IS\d+[A-Z])\b")
_REV_RE = re.compile(r"\b([A-Z](?:\.\d+)?)\b\s+(?:Conforme|Produ[çc][ãa]o)", re.IGNORECASE)


@dataclass
class SubPanelChunk:
    """All pages of one sub-panel inside an IS PDF."""

    panel_id: str          # e.g. PCT01K
    project_id: str        # e.g. ECOCIAF01
    is_id: str             # e.g. IS01A
    drawing_revision: str  # e.g. A, A.1, B
    page_numbers: list[int]  # 1-indexed
    source_pdf: Path

    def extract_pdf_bytes(self) -> bytes:
        """Return a new PDF containing only this sub-panel's pages."""
        src = fitz.open(self.source_pdf)
        dst = fitz.open()
        for pn in self.page_numbers:
            dst.insert_pdf(src, from_page=pn - 1, to_page=pn - 1)
        out = dst.tobytes()
        dst.close()
        src.close()
        return out

    def render_pages_to_png(self, dpi: int = 150) -> list[bytes]:
        """Render each page to PNG. Needed by extractors that don't ingest PDF."""
        src = fitz.open(self.source_pdf)
        pngs: list[bytes] = []
        for pn in self.page_numbers:
            page = src[pn - 1]
            pix = page.get_pixmap(dpi=dpi)
            pngs.append(pix.tobytes("png"))
        src.close()
        return pngs


def _detect_is_id(doc: fitz.Document) -> str:
    """Find the IS id (IS01A / IS02A) — usually on page 1."""
    for page in doc:
        text = page.get_text()
        m = _IS_RE.search(text)
        if m:
            return m.group(1).upper()
    return "UNKNOWN"


def _detect_revision(doc: fitz.Document, panel_id: str, pages: list[int]) -> str:
    """Find the latest revision letter for this sub-panel."""
    revs: list[str] = []
    for pn in pages:
        text = doc[pn - 1].get_text()
        for line in text.splitlines():
            m = _REV_RE.match(line.strip())
            if m:
                revs.append(m.group(1))
    if not revs:
        return "A"
    # Prefer the highest revision (sorted alphabetically usually works)
    return sorted(revs, key=lambda r: (r[0], r[2:] or "0"))[-1]


def split_pdf(pdf_path: Path) -> list[SubPanelChunk]:
    """Split one IS process PDF into per-sub-panel chunks.

    The cover sheet ("KIT PERFIS" and "KIT PLACAS" overviews) gets attributed
    to the first sub-panel mentioned on it — that's fine for context.
    """
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    is_id = _detect_is_id(doc)

    pages_by_panel: dict[str, list[int]] = defaultdict(list)
    project_ids: dict[str, str] = {}

    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        matches = _DWG_RE.findall(text)
        # Filter out IS-prefix matches (those are not panel ids)
        matches = [(p, n, pid) for (p, n, pid) in matches
                   if not pid.upper().startswith(("IS", "MMBF", "PROCESSO"))]
        if not matches:
            continue
        counter = Counter(matches)
        (project_name, project_num, panel_id), _ = counter.most_common(1)[0]
        panel_id = panel_id.upper()
        pages_by_panel[panel_id].append(i)
        project_ids[panel_id] = f"{project_name.upper()}{project_num}"

    chunks: list[SubPanelChunk] = []
    for panel_id, pages in pages_by_panel.items():
        rev = _detect_revision(doc, panel_id, pages)
        chunks.append(
            SubPanelChunk(
                panel_id=panel_id,
                project_id=project_ids[panel_id],
                is_id=is_id,
                drawing_revision=rev,
                page_numbers=sorted(pages),
                source_pdf=pdf_path,
            )
        )
    doc.close()
    return sorted(chunks, key=lambda c: c.panel_id)


def split_many(pdf_paths: list[Path]) -> list[SubPanelChunk]:
    out: list[SubPanelChunk] = []
    for p in pdf_paths:
        out.extend(split_pdf(p))
    return out

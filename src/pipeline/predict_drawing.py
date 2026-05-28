"""Ingestão de um desenho técnico → previsão de tempos por micro-op, painel e projeto.

Fluxo:
  PDF de processo ──split──► sub-painéis ──geometria──► modelo ──► previsão + intervalo

A geometria de cada sub-painel vem de:
  - `--provider gemini` (live, precisa de GEMINI_API_KEY), ou
  - cache `panel_geometry.parquet` (offline; usa painéis já extraídos)

Saída: total do projeto, por painel, e por micro-operação — tudo com intervalo p10–p90.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import estimate as E
from .extraction.schema import FEATURE_COLUMNS
from .extraction.splitter import split_pdf


def _geometry_from_cache(panel_id: str, project_id: str, cache: pd.DataFrame) -> dict | None:
    """Procura geometria em cache pela chave (projeto, painel).

    Project-aware de propósito: o mesmo código (ex. PL01K) aparece em projetos
    diferentes com geometrias diferentes. NÃO devolvemos a geometria de um PL01K
    de outro projeto — isso seria usar dados de treino para "prever" um painel novo.
    """
    if cache.empty:
        return None
    if "project_id" in cache.columns and project_id and project_id != "?":
        hit = cache[(cache.panel_id == panel_id) & (cache.project_id == project_id)]
    else:
        hit = cache[cache.panel_id == panel_id]
    if hit.empty:
        return None
    row = hit.iloc[0].to_dict()
    row["panel_id"] = panel_id
    return row


def _geometry_live(chunk, provider: str) -> dict | None:
    from .extraction.base import get_extractor
    try:
        extractor = get_extractor(provider)  # pode falhar se faltar API key/SDK
    except Exception as e:
        print(f"    ⚠️  provider '{provider}' indisponível ({e}) — fallback para cache")
        return None
    res = extractor.extract(chunk)
    if res.error or res.geometry is None:
        print(f"    ⚠️  {chunk.panel_id}: extração falhou ({res.error})")
        return None
    return res.geometry.model_dump()


def predict_drawing(
    pdf_path: Path,
    provider: str = "cache",
    model_dir: Path = Path("data/training/model"),
    cache_path: Path = Path("data/training/panel_geometry.parquet"),
    micro_ops: list[int] | None = None,
    level: str = "q90",
) -> dict:
    """Devolve previsão estruturada (projeto → painéis → micro-ops) com intervalo conformal."""
    from .modeling import load_deployed
    deployed = load_deployed(model_dir)
    model, cols, conformal = deployed["model"], deployed["design_cols"], deployed["conformal"]

    chunks = split_pdf(pdf_path)
    cache = pd.read_parquet(cache_path) if cache_path.exists() else pd.DataFrame(columns=["panel_id"])

    panels, missing = [], []
    for c in chunks:
        if provider == "cache":
            geom = _geometry_from_cache(c.panel_id, c.project_id, cache)
        else:
            geom = _geometry_live(c, provider) or _geometry_from_cache(c.panel_id, c.project_id, cache)
        if geom is None:
            missing.append(c.panel_id)
            continue
        geom = {k: geom[k] for k in (*FEATURE_COLUMNS, "panel_id", "project_id") if k in geom}
        panel = E.predict_panel(model, cols, conformal, geom, micro_ops=micro_ops, level=level)
        panel["_geom"] = geom
        panels.append(panel)

    return {
        "project_id": chunks[0].project_id if chunks else "?",
        "source_pdf": str(pdf_path),
        "champion": deployed.get("champion"),
        "interval_level": level,
        "n_panels": len(panels),
        "project_total_sec": round(sum(p["total_sec"] for p in panels), 1),
        "project_total_lo_sec": round(sum(p["total_lo_sec"] for p in panels), 1),
        "project_total_hi_sec": round(sum(p["total_hi_sec"] for p in panels), 1),
        "panels": panels,
        "panels_without_geometry": missing,
    }


def print_prediction(out: dict) -> None:
    lvl = out.get("interval_level", "q90").replace("q", "") + "%"
    print(f"\n{'='*64}\n PROJETO {out['project_id']}  ·  modelo: {out['champion']}  "
          f"·  intervalo {lvl}\n{'='*64}")
    for p in out["panels"]:
        print(f"\n ▸ Painel {p['panel_id']}  —  {p['total_sec']:.0f}s "
              f"[{p['total_lo_sec']:.0f}–{p['total_hi_sec']:.0f}]")
        for it in p["micro_ops"]:
            print(f"     op{it['micro_op_num']:>2} {it['micro_op_name']:24} "
                  f"{it['point_sec']:6.0f}s  [{it['lo_sec']:.0f}–{it['hi_sec']:.0f}]")
    print(f"\n{'─'*64}")
    print(f" TOTAL DO PROJETO: {out['project_total_sec']:.0f}s "
          f"[{out['project_total_lo_sec']:.0f}–{out['project_total_hi_sec']:.0f}]  "
          f"(~{out['project_total_sec']/60:.0f} min)")
    if out["panels_without_geometry"]:
        print(f" ⚠️  sem geometria (não extraídos): {out['panels_without_geometry']}")

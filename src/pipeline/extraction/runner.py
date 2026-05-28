"""Orchestrate extraction across all sub-panels of one or more IS PDFs."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .base import ExtractionResult, get_extractor
from .splitter import SubPanelChunk, split_many


def run_extraction(
    pdf_paths: list[Path],
    provider: str,
    output_parquet: Path,
    skip_existing: bool = True,
    only_panels: list[str] | None = None,
) -> pd.DataFrame:
    """Run `provider` over every sub-panel and persist to `output_parquet`.

    Returns the resulting DataFrame.
    """
    extractor = get_extractor(provider)
    chunks = split_many(pdf_paths)
    if only_panels:
        wanted = {p.upper() for p in only_panels}
        chunks = [c for c in chunks if c.panel_id in wanted]

    existing: dict[str, dict] = {}
    if skip_existing and output_parquet.exists():
        existing_df = pd.read_parquet(output_parquet)
        for _, row in existing_df.iterrows():
            existing[row["panel_id"]] = row.to_dict()

    rows: list[dict] = []
    log: list[dict] = []
    for i, chunk in enumerate(chunks, 1):
        if chunk.panel_id in existing:
            print(f"[{i:>2}/{len(chunks)}] {chunk.panel_id}  skipped (already in parquet)")
            rows.append(existing[chunk.panel_id])
            continue
        print(f"[{i:>2}/{len(chunks)}] {chunk.panel_id}  extracting via {provider}…", end=" ", flush=True)
        result: ExtractionResult = extractor.extract(chunk)
        if result.error:
            print(f"❌ {result.error[:120]}")
            log.append({"panel_id": chunk.panel_id, "error": result.error, "raw": result.raw_response[:500]})
            continue
        cost = f"${result.cost_usd:.4f}" if result.cost_usd is not None else "n/a"
        print(f"✅ {result.latency_sec:.1f}s  cost={cost}")
        rows.append(result.geometry.model_dump())
        log.append({"panel_id": chunk.panel_id, "latency_sec": result.latency_sec,
                    "cost_usd": result.cost_usd, "provider": provider})

    df = pd.DataFrame(rows)
    if df.empty:
        print("No rows extracted.")
        return df
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, index=False)
    print(f"\nGuardado: {output_parquet}  ({len(df)} painéis × {len(df.columns)} cols)")

    log_path = output_parquet.with_suffix(".log.jsonl")
    with log_path.open("a") as f:
        for entry in log:
            f.write(json.dumps(entry, default=str) + "\n")
    return df

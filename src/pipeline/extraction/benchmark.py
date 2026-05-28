"""Compare multiple extractors on the same panels.

For each (provider × panel), record: extracted JSON, latency, cost.
For panels with manual ground truth, compute per-field accuracy.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .base import get_extractor
from .schema import FEATURE_COLUMNS, PanelGeometry
from .splitter import split_many


def _load_ground_truth(parquet: Path) -> dict[str, dict]:
    if not parquet.exists():
        return {}
    df = pd.read_parquet(parquet)
    out: dict[str, dict] = {}
    for _, row in df.iterrows():
        out[row["panel_id"]] = row.to_dict()
    return out


def _compare(predicted: dict, truth: dict) -> dict:
    diffs: dict[str, dict] = {}
    n_match = 0
    for f in FEATURE_COLUMNS:
        if f not in truth:
            continue
        p, t = predicted.get(f), truth.get(f)
        if isinstance(p, float) and isinstance(t, (int, float)):
            ok = abs(p - t) < 0.01
        else:
            ok = p == t
        if ok:
            n_match += 1
        diffs[f] = {"predicted": p, "truth": t, "match": ok}
    return {"n_match": n_match, "n_total": sum(1 for f in FEATURE_COLUMNS if f in truth),
            "fields": diffs}


def run_benchmark(
    pdf_paths: list[Path],
    providers: list[str],
    panels: list[str],
    output: Path,
    console,
) -> dict:
    truth = _load_ground_truth(Path("data/training/panel_geometry.parquet"))
    chunks = {c.panel_id: c for c in split_many(pdf_paths) if c.panel_id in set(panels)}
    missing = set(panels) - chunks.keys()
    if missing:
        console.print(f"[yellow]Warning:[/yellow] panels not found: {sorted(missing)}")

    report = {"providers": {}, "panels": panels}
    for provider_name in providers:
        console.print(f"\n[bold cyan]== {provider_name} ==[/bold cyan]")
        try:
            extractor = get_extractor(provider_name)
        except Exception as e:
            console.print(f"[red]{provider_name} unavailable:[/red] {e}")
            report["providers"][provider_name] = {"available": False, "error": str(e)}
            continue

        prov_report = {"available": True, "panels": {}}
        for panel_id in panels:
            chunk = chunks.get(panel_id)
            if not chunk:
                continue
            console.print(f"  {panel_id}…", end=" ")
            result = extractor.extract(chunk)
            if result.error:
                console.print(f"[red]error:[/red] {result.error[:100]}")
                prov_report["panels"][panel_id] = {
                    "error": result.error, "latency_sec": result.latency_sec,
                }
                continue
            cost_str = f"${result.cost_usd:.4f}" if result.cost_usd else "free"
            entry = {
                "latency_sec": round(result.latency_sec, 2),
                "cost_usd": result.cost_usd,
                "extracted": result.geometry.model_dump(),
            }
            if panel_id in truth:
                comp = _compare(entry["extracted"], truth[panel_id])
                entry["comparison"] = comp
                console.print(
                    f"{result.latency_sec:.1f}s  {cost_str}  "
                    f"match={comp['n_match']}/{comp['n_total']}"
                )
            else:
                console.print(f"{result.latency_sec:.1f}s  {cost_str}  (no ground truth)")
            prov_report["panels"][panel_id] = entry
        report["providers"][provider_name] = prov_report

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, default=str))
    console.print(f"\n[green]Report saved:[/green] {output}")
    return report

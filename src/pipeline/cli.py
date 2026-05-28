"""CLI minimal: extracção de geometria dos PDFs ECOCIAF + benchmark de providers."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True, help="ECOCIAF panel-geometry extraction pipeline.")
console = Console()


@app.command("extract-geometry")
def extract_geometry(
    provider: str = typer.Option("gemini", "--provider", help="gemini | claude | ollama (default: gemini)"),
    pdfs_dir: str = typer.Option(
        "data/raw/Desenhos Técnicos - ECOCIAF",
        "--pdfs-dir",
        help="Pasta com os PDFs de processo ECOCIAF",
    ),
    output: str = typer.Option(
        "data/training/panel_geometry.parquet",
        "--output",
        help="Onde escrever as 21 features por sub-painel",
    ),
    panels: str = typer.Option(
        "", "--panels", help="CSV de panel_ids para extrair (vazio = todos)"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Re-extrair painéis já presentes no parquet"
    ),
):
    """Extract the 21 geometry features from ECOCIAF process PDFs into panel_geometry.parquet."""
    from .extraction.runner import run_extraction

    pdf_paths = sorted(Path(pdfs_dir).glob("*PROCESSO*.pdf"))
    if not pdf_paths:
        raise typer.BadParameter(f"No PROCESSO PDFs found in {pdfs_dir}")
    only = [p.strip() for p in panels.split(",") if p.strip()] or None
    run_extraction(
        pdf_paths=pdf_paths,
        provider=provider,
        output_parquet=Path(output),
        skip_existing=not overwrite,
        only_panels=only,
    )


@app.command("benchmark-extractors")
def benchmark_extractors(
    providers: str = typer.Option(
        "gemini,claude,ollama", "--providers", help="CSV de providers a comparar"
    ),
    panels: str = typer.Option(
        "PG02K,PCT01K,PT01K", "--panels", help="CSV de panel_ids para benchmark"
    ),
    pdfs_dir: str = typer.Option(
        "data/raw/Desenhos Técnicos - ECOCIAF", "--pdfs-dir"
    ),
    output: str = typer.Option(
        "data/training/benchmark_extractors.json", "--output"
    ),
):
    """Compare providers field-by-field on the same panels. Writes a JSON report."""
    from .extraction.benchmark import run_benchmark

    provider_list = [p.strip() for p in providers.split(",") if p.strip()]
    panel_list = [p.strip().upper() for p in panels.split(",") if p.strip()]
    pdf_paths = sorted(Path(pdfs_dir).glob("*PROCESSO*.pdf"))
    run_benchmark(pdf_paths, provider_list, panel_list, Path(output), console)


@app.command("train")
def train_cmd(
    trials: int = typer.Option(20, "--trials", help="Optuna trials per booster"),
    output_dir: str = typer.Option("data/training/model", "--output-dir"),
):
    """Train CatBoost/LightGBM/XGBoost + ensemble on training_wide.csv with LOPO CV."""
    from .train import run
    run(trials=trials, output_dir=Path(output_dir))


@app.command("parse-times")
def parse_times(
    excels_dir: str = typer.Option(
        "data/raw/Excel - Tempos Micro Tarefas",
        "--excels-dir",
        help="Pasta com os Excels de tempos",
    ),
    output: str = typer.Option(
        "data/training/ecociaf_times_long.parquet",
        "--output",
    ),
    pattern: str = typer.Option(
        "Tempos_ECOCIAF_*.xlsx", "--pattern",
        help="Glob para filtrar os Excels (ex.: Tempos_ECOCIAF_*.xlsx)",
    ),
):
    """Parse Excel time files into the long times parquet."""
    import pandas as pd
    from .excel_times import parse_many, normalize_panel_ids

    paths = sorted(Path(excels_dir).glob(pattern))
    if not paths:
        raise typer.BadParameter(f"No Excels matching {pattern} in {excels_dir}")
    df = parse_many(paths)
    # Normalização conhecida: PCT01W (typo no Excel) → PCT01K
    df = normalize_panel_ids(df, {"PCT01W": "PCT01K"})
    df = df.dropna(subset=["duration_sec"])
    df = df[df["duration_sec"] > 0].reset_index(drop=True)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    console.print(f"[green]parsed:[/green] {len(df)} linhas → {output}")

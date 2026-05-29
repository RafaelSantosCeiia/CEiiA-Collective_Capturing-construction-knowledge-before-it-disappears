"""Pipeline CLI: PDF → geometry (Gemini) → model → time prediction.

End-to-end flow:
  extract-geometry  process PDFs → 21 features per sub-panel (Gemini)
  build-training    observed times ⨝ geometry → training_long / test_long
  train             multi-model benchmark + champion-gate + deploy (overnight retrain)
  evaluate          honest scorecard (human floor vs baselines vs model)
  predict-drawing   ingest a drawing → times per micro-op, panel and project
"""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

# Load credentials from .env (GEMINI_API_KEY, etc.) if present.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = typer.Typer(no_args_is_help=True, help="BluFab — per-panel production time estimation.")
console = Console()


@app.command("extract-geometry")
def extract_geometry(
    provider: str = typer.Option("gemini", "--provider", help="gemini | claude | ollama"),
    pdfs_dir: str = typer.Option("data/raw/Desenhos Técnicos - ECOCIAF", "--pdfs-dir"),
    output: str = typer.Option("data/training/panel_geometry.parquet", "--output"),
    panels: str = typer.Option("", "--panels", help="CSV of panel_ids (empty = all)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Re-extract panels already present"),
):
    """Extract the 21 geometry features from the process PDFs (default: Gemini 3.5 Flash)."""
    from .extraction.runner import run_extraction

    pdf_paths = sorted(Path(pdfs_dir).glob("*PROCESSO*.pdf"))
    if not pdf_paths:
        raise typer.BadParameter(f"No *PROCESSO* PDFs in {pdfs_dir}")
    only = [p.strip() for p in panels.split(",") if p.strip()] or None
    run_extraction(pdf_paths=pdf_paths, provider=provider, output_parquet=Path(output),
                   skip_existing=not overwrite, only_panels=only)


@app.command("build-training")
def build_training(
    regenerate_times: bool = typer.Option(False, "--regenerate-times",
        help="Re-parse the time Excels instead of using the parquets"),
):
    """Join observed times + geometry → training_long.parquet / test_long.parquet."""
    from .training_table import build_training_table
    build_training_table(regenerate_times=regenerate_times)


@app.command("train")
def train_cmd(
    trials: int = typer.Option(30, "--trials", help="Optuna trials per booster"),
    clean: bool = typer.Option(True, "--clean/--no-clean", help="Remove recording outliers"),
    require_improvement: bool = typer.Option(True, "--gate/--no-gate",
        help="Champion-gate: only deploy if it beats the smart baseline"),
    holdout: str = typer.Option("", "--holdout",
        help="CSV of panel_ids to EXCLUDE from training (e.g. panels to evaluate)"),
    output_dir: str = typer.Option("data/training/model", "--output-dir"),
):
    """Multi-model benchmark (CatBoost/LGBM/XGB/stacking/+AutoGluon) + champion deploy."""
    from .modeling import run
    hold = [h.strip() for h in holdout.split(",") if h.strip()] or None
    run(trials=trials, clean=clean, require_improvement=require_improvement,
        holdout=hold, output_dir=Path(output_dir))


@app.command("evaluate")
def evaluate_cmd(
    clean: bool = typer.Option(True, "--clean/--no-clean"),
    output: str = typer.Option("data/training/scorecard.json", "--output"),
):
    """Honest scorecard: human noise floor vs baselines vs model (LOPO), no deploy."""
    from . import estimate as E
    from .modeling import benchmark, _print_scorecard, _predict_fn_for
    d = E.load_data(clean=clean)
    floor = E.human_noise_floor(d)
    console.print(f"[cyan]Dataset:[/cyan] {len(d)} obs, {d[E.GROUP].nunique()} panels · floor {floor['mae']:.1f}s")
    lb = benchmark(d, trials=20)
    # geometry-aware champion (differentiates panels), same logic as deploy
    cand = {k: v for k, v in lb.items() if k not in ("baseline_global", "per_op_median")}
    champ = min(cand or lb, key=lambda k: lb[k]["mae"])
    coverage = E.conformal_coverage(_predict_fn_for(champ, lb[champ]["params"]), d)
    report = {"human_noise_floor": floor, "conformal_coverage": coverage,
              "leaderboard": {k: {"mae": v["mae"]} for k, v in lb.items()}, "champion": champ}
    _print_scorecard(report, lb)
    Path(output).write_text(json.dumps(report, indent=2))
    console.print(f"[green]scorecard →[/green] {output}")


@app.command("predict-drawing")
def predict_drawing_cmd(
    pdf: str = typer.Argument(..., help="Path of the process PDF to estimate"),
    provider: str = typer.Option("cache", "--provider",
        help="cache (offline) | gemini | claude | ollama"),
    level: str = typer.Option("q90", "--level", help="Interval level: q80 | q90"),
    model_dir: str = typer.Option("data/training/model", "--model-dir"),
    output: str = typer.Option("", "--output", help="Write JSON (optional)"),
):
    """Ingest a technical drawing and estimate times per micro-op, panel and project."""
    from .predict_drawing import predict_drawing, print_prediction
    out = predict_drawing(Path(pdf), provider=provider, model_dir=Path(model_dir), level=level)
    print_prediction(out)
    if output:
        Path(output).write_text(json.dumps(out, indent=2, ensure_ascii=False))
        console.print(f"[green]→[/green] {output}")


@app.command("future-build")
def future_build_cmd():
    """[Future vision · FICTITIOUS data] Generate the 4 synthetic datasets + train the models.

    Demonstrates actionable patterns (waste, temperature, experience, time of day)
    that richer data would unlock. Does not touch the real pipeline.
    """
    from .future.synth import build_all_synth
    from .future.train import train_all
    console.print("[cyan]=== Generating synthetic datasets (future) ===[/cyan]")
    build_all_synth()
    metas = train_all()

    # sanity-check: confirm the effect trends are correct
    from .future.predict import load_models, predict_future
    load_models.cache_clear()
    import pandas as pd
    g = pd.read_parquet("data/training/panel_geometry.parquet").iloc[0].to_dict()
    out = predict_future(g)
    console.print(f"\n[cyan]Sanity-check[/cyan] (panel {out['panel_id']}):")
    for key in ("temperature", "experience", "timeofday"):
        sc = out[key]["scenarios"]
        line = "  ".join(f"{s['label']}={s['total_sec']:.0f}s" for s in sc)
        console.print(f"  [bold]{key:11}[/bold] {line}")
    bd = out["general"]["breakdown"]
    console.print(f"  [bold]general    [/bold] productive={bd['productive_pct']}% · "
                  f"idle={bd['idle_no_value_pct']}% · material={bd['material_necessary_pct']}%")
    console.print("[green]✓ future-build done[/green]")


@app.command("parse-times")
def parse_times(
    excels_dir: str = typer.Option("data/raw/Excel - Tempos Micro Tarefas", "--excels-dir"),
):
    """Re-parse the time Excels (PICUA + ECOCIAF) into the long parquets."""
    from .picua_times import build_picua_times, build_ecociaf_times
    picua = build_picua_times()
    picua.to_parquet("data/training/picua_times_long.parquet", index=False)
    ecociaf = build_ecociaf_times()
    ecociaf.to_parquet("data/training/ecociaf_times_long.parquet", index=False)
    console.print(f"[green]PICUA:[/green] {len(picua)} · [green]ECOCIAF:[/green] {len(ecociaf)}")


if __name__ == "__main__":
    app()

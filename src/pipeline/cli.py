"""CLI da pipeline: PDF → geometria (Gemini) → modelo → previsão de tempos.

Fluxo end-to-end:
  extract-geometry  PDFs de processo → 21 features por sub-painel (Gemini)
  build-training    tempos observados ⨝ geometria → training_long / test_long
  train             benchmark multi-modelo + champion-gate + deploy (retreino noturno)
  evaluate          scorecard honesto (piso humano vs baselines vs modelo)
  predict-drawing   ingere um desenho → tempos por micro-op, painel e projeto
"""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

# Carrega credenciais de .env (GEMINI_API_KEY, etc.) se existir.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = typer.Typer(no_args_is_help=True, help="BluFab — estimativa de tempos de produção por painel.")
console = Console()


@app.command("extract-geometry")
def extract_geometry(
    provider: str = typer.Option("gemini", "--provider", help="gemini | claude | ollama"),
    pdfs_dir: str = typer.Option("data/raw/Desenhos Técnicos - ECOCIAF", "--pdfs-dir"),
    output: str = typer.Option("data/training/panel_geometry.parquet", "--output"),
    panels: str = typer.Option("", "--panels", help="CSV de panel_ids (vazio = todos)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Re-extrair painéis já presentes"),
):
    """Extrai as 21 features de geometria dos PDFs de processo (default: Gemini 3.5 Flash)."""
    from .extraction.runner import run_extraction

    pdf_paths = sorted(Path(pdfs_dir).glob("*PROCESSO*.pdf"))
    if not pdf_paths:
        raise typer.BadParameter(f"Sem PDFs *PROCESSO* em {pdfs_dir}")
    only = [p.strip() for p in panels.split(",") if p.strip()] or None
    run_extraction(pdf_paths=pdf_paths, provider=provider, output_parquet=Path(output),
                   skip_existing=not overwrite, only_panels=only)


@app.command("build-training")
def build_training(
    regenerate_times: bool = typer.Option(False, "--regenerate-times",
        help="Re-parsear os Excels de tempos em vez de usar os parquets"),
):
    """Junta tempos observados + geometria → training_long.parquet / test_long.parquet."""
    from .training_table import build_training_table
    build_training_table(regenerate_times=regenerate_times)


@app.command("train")
def train_cmd(
    trials: int = typer.Option(30, "--trials", help="Optuna trials por booster"),
    clean: bool = typer.Option(True, "--clean/--no-clean", help="Remover outliers de gravação"),
    require_improvement: bool = typer.Option(True, "--gate/--no-gate",
        help="Champion-gate: só faz deploy se bater a baseline esperta"),
    holdout: str = typer.Option("", "--holdout",
        help="CSV de panel_ids a EXCLUIR do treino (ex.: painéis a avaliar)"),
    output_dir: str = typer.Option("data/training/model", "--output-dir"),
):
    """Benchmark multi-modelo (CatBoost/LGBM/XGB/stacking/+AutoGluon) + deploy do campeão."""
    from .modeling import run
    hold = [h.strip() for h in holdout.split(",") if h.strip()] or None
    run(trials=trials, clean=clean, require_improvement=require_improvement,
        holdout=hold, output_dir=Path(output_dir))


@app.command("evaluate")
def evaluate_cmd(
    clean: bool = typer.Option(True, "--clean/--no-clean"),
    output: str = typer.Option("data/training/scorecard.json", "--output"),
):
    """Scorecard honesto: piso de ruído humano vs baselines vs modelo (LOPO), sem deploy."""
    from . import estimate as E
    from .modeling import benchmark, _print_scorecard, _predict_fn_for
    d = E.load_data(clean=clean)
    floor = E.human_noise_floor(d)
    console.print(f"[cyan]Dataset:[/cyan] {len(d)} obs, {d[E.GROUP].nunique()} painéis · piso {floor['mae']:.1f}s")
    lb = benchmark(d, trials=20)
    # campeão geometry-aware (diferencia painéis), igual à lógica do deploy
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
    pdf: str = typer.Argument(..., help="Caminho do PDF de processo a estimar"),
    provider: str = typer.Option("cache", "--provider",
        help="cache (offline) | gemini | claude | ollama"),
    level: str = typer.Option("q90", "--level", help="Nível do intervalo: q80 | q90"),
    model_dir: str = typer.Option("data/training/model", "--model-dir"),
    output: str = typer.Option("", "--output", help="Gravar JSON (opcional)"),
):
    """Ingere um desenho técnico e estima tempos por micro-op, painel e projeto."""
    from .predict_drawing import predict_drawing, print_prediction
    out = predict_drawing(Path(pdf), provider=provider, model_dir=Path(model_dir), level=level)
    print_prediction(out)
    if output:
        Path(output).write_text(json.dumps(out, indent=2, ensure_ascii=False))
        console.print(f"[green]→[/green] {output}")


@app.command("future-build")
def future_build_cmd():
    """[Visão de futuro · dados FICTÍCIOS] Gera os 4 datasets sintéticos + treina os modelos.

    Demonstra padrões acionáveis (desperdício, temperatura, experiência, hora do dia)
    que dados mais ricos desbloqueiam. Não toca no pipeline real.
    """
    from .future.synth import build_all_synth
    from .future.train import train_all
    console.print("[cyan]=== Geração de datasets sintéticos (future) ===[/cyan]")
    build_all_synth()
    metas = train_all()

    # sanity-check: confirma que as tendências dos efeitos estão corretas
    from .future.predict import load_models, predict_future
    load_models.cache_clear()
    import pandas as pd
    g = pd.read_parquet("data/training/panel_geometry.parquet").iloc[0].to_dict()
    out = predict_future(g)
    console.print(f"\n[cyan]Sanity-check[/cyan] (painel {out['panel_id']}):")
    for key in ("temperature", "experience", "timeofday"):
        sc = out[key]["scenarios"]
        line = "  ".join(f"{s['label']}={s['total_sec']:.0f}s" for s in sc)
        console.print(f"  [bold]{key:11}[/bold] {line}")
    bd = out["general"]["breakdown"]
    console.print(f"  [bold]general    [/bold] productive={bd['productive_pct']}% · "
                  f"idle={bd['idle_no_value_pct']}% · material={bd['material_necessary_pct']}%")
    console.print("[green]✓ future-build concluído[/green]")


@app.command("parse-times")
def parse_times(
    excels_dir: str = typer.Option("data/raw/Excel - Tempos Micro Tarefas", "--excels-dir"),
):
    """Re-parsear os Excels de tempos (PICUA + ECOCIAF) para os parquets long."""
    from .picua_times import build_picua_times, build_ecociaf_times
    picua = build_picua_times()
    picua.to_parquet("data/training/picua_times_long.parquet", index=False)
    ecociaf = build_ecociaf_times()
    ecociaf.to_parquet("data/training/ecociaf_times_long.parquet", index=False)
    console.print(f"[green]PICUA:[/green] {len(picua)} · [green]ECOCIAF:[/green] {len(ecociaf)}")


if __name__ == "__main__":
    app()

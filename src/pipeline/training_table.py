"""Constrói a tabela de treino: tempos observados ⨝ geometria extraída do PDF.

Cadeia reprodutível (raw → treino):
  Excels de tempos  ──parse──►  *_times_long.parquet  ─┐
                                                        ├─ ⨝ panel_id ─► *_long.parquet
  PDFs de processo  ──Gemini──►  panel_geometry.parquet ┘

  - training_long = tempos PICUA   ⨝ geometria   (dados de treino)
  - test_long     = tempos ECOCIAF ⨝ geometria   (held-out, observado por 2 pessoas)

A limpeza de outliers NÃO é feita aqui — os ficheiros em disco ficam com os dados
crus (honestos). A remoção de erros de gravação é uma decisão de modelação,
aplicada em memória por `clean_observations()` e registada num log.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# join keys da geometria que não são features
_GEOM_DROP = ["is_id", "project_id", "drawing_revision"]


def build_training_table(
    train_dir: Path = Path("data/training"),
    regenerate_times: bool = False,
) -> dict[str, pd.DataFrame]:
    """Junta tempos + geometria e escreve training_long.parquet / test_long.parquet."""
    geom = pd.read_parquet(train_dir / "panel_geometry.parquet")
    geom = geom.drop(columns=[c for c in _GEOM_DROP if c in geom.columns])

    if regenerate_times:
        from .picua_times import build_picua_times, build_ecociaf_times
        picua = build_picua_times()
        ecociaf = build_ecociaf_times()
    else:
        picua = pd.read_parquet(train_dir / "picua_times_long.parquet")
        ecociaf = pd.read_parquet(train_dir / "ecociaf_times_long.parquet")

    out = {}
    for name, times in (("training_long", picua), ("test_long", ecociaf)):
        merged = times.merge(geom, on="panel_id", how="inner")
        path = train_dir / f"{name}.parquet"
        merged.to_parquet(path, index=False)
        out[name] = merged
        print(f"  {name}: {len(merged)} linhas × {merged.shape[1]} cols → {path}")
    return out


def clean_observations(
    d: pd.DataFrame,
    n_mad: float = 3.5,
    log_path: Path | None = Path("data/training/removed_observations.csv"),
) -> pd.DataFrame:
    """Remove observações claramente mal gravadas (> n_mad MAD da sua (painel, micro-op)).

    Conservador: só apanha erros grosseiros. Regista o que removeu para auditoria.
    Baixa o piso de ruído ~20s→13s sem inventar nada.
    """
    keep_parts, removed_parts = [], []
    for _, g in d.groupby(["panel_id", "micro_op_num"]):
        v = g["duration_sec"].to_numpy(float)
        med = np.median(v)
        mad = np.median(np.abs(v - med)) + 1e-9
        mask = np.abs(v - med) <= n_mad * mad
        keep_parts.append(g[mask])
        if (~mask).any():
            r = g[~mask].copy()
            r["median_da_tarefa"] = med
            removed_parts.append(r)
    kept = pd.concat(keep_parts).reset_index(drop=True)
    removed = pd.concat(removed_parts).reset_index(drop=True) if removed_parts else pd.DataFrame()
    if log_path is not None and not removed.empty:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        cols = ["panel_id", "micro_op_num", "observation_id", "source",
                "duration_sec", "median_da_tarefa"]
        removed[[c for c in cols if c in removed.columns]].to_csv(log_path, index=False)
    print(f"  cleaning: {len(d)} → {len(kept)} obs ({len(removed)} removed, log → {log_path})")
    return kept

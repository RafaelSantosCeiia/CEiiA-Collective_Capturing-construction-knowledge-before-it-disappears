"""Parser dos Excels de tempos por micro-tarefa.

Lê `Tempos_<PROJECTO>_Tirados_por_<Observador>.xlsx` e produz uma tabela longa
(`times_long.parquet`) com schema fonte-agnóstico:

    panel_id        str
    micro_op_num    int
    duration_sec    float
    source          str   ('excel' | 'cv' | 'manual')
    source_ref      str   (path do ficheiro de origem)

Estrutura esperada dos Excels:
  - Linha 1: cabeçalho do projecto (ignorado)
  - Linha 2 (idx 1): IDs dos painéis nas colunas 1, 4, 7, 10, ...
  - Linha 3 (idx 2): "Início / Fim / Duração" repetido
  - Linhas 4-17 (idx 3-16): cada uma é uma micro-tarefa numerada "N. ..."
"""
from __future__ import annotations

from datetime import datetime, time
from pathlib import Path

import pandas as pd


def _parse_time_cell(val) -> int | None:
    """Converte uma célula de tempo (HH:MM:SS) em segundos."""
    if pd.isna(val):
        return None
    if isinstance(val, time):
        return val.hour * 3600 + val.minute * 60 + val.second
    if isinstance(val, datetime):
        return val.hour * 3600 + val.minute * 60 + val.second
    if isinstance(val, str):
        try:
            h, m, s = map(int, val.split(":"))
            return h * 3600 + m * 60 + s
        except ValueError:
            return None
    return None


def parse_excel(path: Path | str) -> pd.DataFrame:
    """Lê um Excel de tempos e devolve linhas (panel_id, micro_op_num, duration_sec)."""
    path = Path(path)
    df = pd.read_excel(path, sheet_name=0, header=None)

    # Identificar colunas com IDs de painel na linha 1 (skipping headers like "Início")
    panel_cols: list[tuple[int, str]] = []
    for c in range(1, df.shape[1]):
        v = df.iloc[1, c]
        if pd.notna(v) and isinstance(v, str) and v.strip() != "Início":
            panel_cols.append((c, v.strip()))

    rows: list[dict] = []
    for row_idx in range(3, df.shape[0]):
        op_name_pt = df.iloc[row_idx, 0]
        if pd.isna(op_name_pt):
            continue
        op_num_str = str(op_name_pt).split(".")[0].strip()
        try:
            op_num = int(op_num_str)
        except ValueError:
            continue

        for obs_idx, (col_start, panel_id) in enumerate(panel_cols, 1):
            start = _parse_time_cell(df.iloc[row_idx, col_start])
            end = _parse_time_cell(df.iloc[row_idx, col_start + 1])
            duration = _parse_time_cell(df.iloc[row_idx, col_start + 2])
            if duration is None and start is not None and end is not None:
                duration = end - start
            rows.append({
                "panel_id": panel_id,
                "micro_op_num": op_num,
                "duration_sec": duration,
                "source": "excel",
                "source_ref": f"{path.name}#obs{obs_idx}",
            })
    return pd.DataFrame(rows)


def parse_many(paths: list[Path | str]) -> pd.DataFrame:
    """Lê vários Excels e concatena."""
    parts = [parse_excel(p) for p in paths]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def normalize_panel_ids(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Normaliza IDs (ex.: 'PCT01W' → 'PCT01K')."""
    df = df.copy()
    df["panel_id"] = df["panel_id"].replace(mapping)
    return df

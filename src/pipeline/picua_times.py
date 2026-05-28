"""Parser dos Excels PICUA (Inês + Beatriz) com mapping para 14 ops canónicas.

Cada observação produz 14 linhas (uma por micro-tarefa atómica), com:
  panel_id, source, observation_id, date, micro_op_num, duration_sec

Regra: tarefas repetidas dentro da mesma observação são SOMADAS na atómica
correspondente (ex.: PICUA Inês op 6 + op 9 → atomic 6 "pegar placa(s)").
"""
from __future__ import annotations

import re
from datetime import datetime, time
from pathlib import Path

import pandas as pd


# Vocabulário canónico
ATOMIC_VOCAB = {
    1: "Pegar nos perfis",
    2: "Colocar os perfis na bancada",
    3: "Fixar a estrutura com fixadores",
    4: "Medições e alinhamentos prévios",
    5: "Cravação 1 (antes de placar)",
    6: "Pegar e colocar placa(s)",
    7: "Medições e ajustes placa(s)",
    8: "Aparafusar placa(s)",
    9: "Remover fixadores",
    10: "Virar estrutura",
    11: "Cravação 2 (depois de placar)",
    12: "Imprimir + colar etiqueta",
    13: "Palete + transportar",
    14: "Transportar mesa para início",  # ECOCIAF distinct; Beatriz/Inês PICUA fold to 13
}


# Mapping PICUA Inês (17 ops) → 14 atómicas
PICUA_INES_MAP: dict[int, int] = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
    6: 6,    # primeira placa
    9: 6,    # segunda placa → atomic 6
    7: 7,    # medições placa 1
    10: 7,   # medições placa 2 → atomic 7
    8: 8,    # aparafusar parcialmente
    11: 8,   # aparafusar tudo → atomic 8
    12: 9,   # remover fixadores
    13: 10,  # virar
    14: 11,  # cravação 2
    15: 12,  # etiqueta
    16: 13,  # palete
    17: 14,  # transportar
}


def _parse_time(val) -> float | None:
    if pd.isna(val):
        return None
    if isinstance(val, time):
        return val.hour * 3600 + val.minute * 60 + val.second
    if isinstance(val, datetime):
        return val.hour * 3600 + val.minute * 60 + val.second
    if isinstance(val, str):
        try:
            parts = val.split(":")
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        except (ValueError, IndexError):
            return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None
    return None


def _norm_panel(p: str) -> str:
    """PCL01 K → PCL01K · PCK02_K → PCK02K · 'PCT01 K' → 'PCT01K'."""
    p = re.sub(r"\s+", "", p.strip())
    p = p.replace("_", "")
    # Garantir sufixo K se acabar em número
    if re.match(r"^P[A-Z]+\d+$", p):
        p = p + "K"
    return p.upper()


# ---------- PICUA Inês ----------

def parse_picua_ines(path: Path) -> pd.DataFrame:
    """17 ops × 8 observações. Cada coluna é uma observação."""
    df = pd.read_excel(path, sheet_name=0, header=None)

    # Header row 0: "(DD/MM) PCL01 K", etc.
    obs_cols: list[tuple[int, str, str]] = []
    for c in range(1, df.shape[1]):
        v = df.iloc[0, c]
        if not isinstance(v, str):
            continue
        m = re.match(r"\(([\d/]+)\)\s*(P[A-Z]+\s*\d+\s*\w?)", v)
        if not m:
            continue
        date_str = m.group(1)
        panel_id = _norm_panel(m.group(2))
        obs_cols.append((c, date_str, panel_id))

    rows: list[dict] = []
    obs_counter: dict[tuple[str, str], int] = {}
    for col, date, panel_id in obs_cols:
        key = (panel_id, date)
        obs_counter[key] = obs_counter.get(key, 0) + 1
        obs_id = f"PICUA_INES_{panel_id}_{date.replace('/', '')}_{obs_counter[key]}"

        for row_idx in range(1, 18):
            op_name = df.iloc[row_idx, 0]
            if pd.isna(op_name):
                continue
            try:
                picua_op = int(str(op_name).split(".")[0].strip())
            except ValueError:
                continue
            dur = _parse_time(df.iloc[row_idx, col])
            if dur is None or dur <= 0:
                continue
            canonical = PICUA_INES_MAP.get(picua_op)
            if canonical is None:
                continue
            rows.append({
                "panel_id": panel_id,
                "source": "picua_ines",
                "observation_id": obs_id,
                "date": date,
                "raw_op_num": picua_op,
                "atomic_op_num": canonical,
                "duration_sec": dur,
            })
    return pd.DataFrame(rows)


# ---------- PICUA Beatriz ----------

# As primeiras 26 linhas têm o breakdown de alto nível
# (rows 3-26 = ops da bancada).
BEATRIZ_PICUA_MAP: dict[int, int] = {
    3: 1,    # ir buscar perfis
    4: 2,    # colocação de montantes e raias
    5: 3,    # fixar a estrutura
    8: 4,    # medições e ajustes (prévios)
    11: 5,   # clinching 1
    12: 6,   # pegar e colocar placa 1
    13: 7,   # medições placa 1
    14: 8,   # aparafusar placa 1
    15: 6,   # pegar e colocar placa 2 → atomic 6
    16: 7,   # medições placa 2 → atomic 7
    17: 8,   # aparafusar placa 2 → atomic 8
    18: 9,   # desapertar/remover fixadores
    21: 10,  # virar
    22: 11,  # clinching 2
    23: 12,  # etiqueta
    25: 13,  # palete
    26: 13,  # transportar mesa → fold com palete
    # rows 6,7,9,10,19,20 são sub-tarefas (ignoradas — duracoes ficam nos pais)
}


def parse_picua_beatriz(path: Path) -> pd.DataFrame:
    """Cada coluna a partir de col 1 é uma observação (painel × data)."""
    df = pd.read_excel(path, sheet_name=0, header=None)

    # Procurar cabeçalho de observações. Pode estar em row 1 ou 2.
    # Beatriz PICUA: header com painel e data nas cols 1+.
    # Vamos varrer a primeira linha e identificar cells que parecem painel.
    obs_cols: list[tuple[int, str]] = []
    header_row = None
    for r in range(0, 3):
        candidates = []
        for c in range(1, df.shape[1]):
            v = df.iloc[r, c]
            if isinstance(v, str) and re.search(r"P[A-Z]+\d+", v):
                candidates.append((c, v))
        if len(candidates) >= 3:
            obs_cols = [(c, _norm_panel(re.search(r"P[A-Z]+\s*\d+\s*\w?", v).group(0)))
                        for c, v in candidates]
            header_row = r
            break

    if not obs_cols:
        # Fallback: not parseable
        return pd.DataFrame()

    rows: list[dict] = []
    obs_seen: dict[str, int] = {}
    for col, panel_id in obs_cols:
        obs_seen[panel_id] = obs_seen.get(panel_id, 0) + 1
        obs_id = f"PICUA_BEA_{panel_id}_obs{obs_seen[panel_id]}"

        for raw_row, canonical in BEATRIZ_PICUA_MAP.items():
            dur = _parse_time(df.iloc[raw_row, col])
            if dur is None or dur <= 0:
                continue
            rows.append({
                "panel_id": panel_id,
                "source": "picua_beatriz",
                "observation_id": obs_id,
                "date": None,  # Beatriz não tem datas claras em todas
                "raw_op_num": raw_row,
                "atomic_op_num": canonical,
                "duration_sec": dur,
            })
    return pd.DataFrame(rows)


# ---------- aggregate to canonical 14 ----------

def aggregate_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Soma duração dentro de cada (observation, atomic_op)."""
    if df.empty:
        return df
    g = (
        df.groupby(["panel_id", "source", "observation_id", "atomic_op_num"], as_index=False)
        .agg({"duration_sec": "sum", "date": "first"})
    )
    g = g.rename(columns={"atomic_op_num": "micro_op_num"})
    return g.sort_values(["observation_id", "micro_op_num"]).reset_index(drop=True)


def build_picua_times(excels_dir: Path = Path("data/raw/Excel - Tempos Micro Tarefas")) -> pd.DataFrame:
    ines_path = excels_dir / "Tempos_PICUA_Tirados_por_Inês.xlsx"
    bea_path = excels_dir / "Tempos_PICUA_Tirado_por_(Beatriz).xlsx"
    parts = []
    if ines_path.exists():
        parts.append(parse_picua_ines(ines_path))
    if bea_path.exists():
        parts.append(parse_picua_beatriz(bea_path))
    raw = pd.concat([p for p in parts if not p.empty], ignore_index=True) if parts else pd.DataFrame()
    return aggregate_to_canonical(raw)


# ---------- ECOCIAF (test set, no aggregation needed — 14 ops 1:1) ----------

ECOCIAF_MAP = {i: i for i in range(1, 15)}  # 14 → 14 identity


def parse_ecociaf_wide(path: Path, observer: str) -> pd.DataFrame:
    """Excel ECOCIAF: row 1 = panel ids em cols 1,4,7…; row 3-16 = 14 ops."""
    df = pd.read_excel(path, sheet_name=0, header=None)
    panel_cols: list[tuple[int, str]] = []
    for c in range(1, df.shape[1]):
        v = df.iloc[1, c]
        if isinstance(v, str) and v.strip() != "Início":
            panel_cols.append((c, _norm_panel(v)))

    rows: list[dict] = []
    obs_seen: dict[str, int] = {}
    for col, panel_id in panel_cols:
        obs_seen[panel_id] = obs_seen.get(panel_id, 0) + 1
        obs_id = f"ECOCIAF_{observer}_{panel_id}_obs{obs_seen[panel_id]}"
        # Cols [Início | Fim | Duração] consecutivas
        for row_idx in range(3, 17):
            v = df.iloc[row_idx, 0]
            if pd.isna(v):
                continue
            try:
                op_num = int(str(v).split(".")[0].strip())
            except ValueError:
                continue
            dur = _parse_time(df.iloc[row_idx, col + 2])
            if dur is None or dur <= 0:
                # tentar derivar do início/fim
                start = _parse_time(df.iloc[row_idx, col])
                end = _parse_time(df.iloc[row_idx, col + 1])
                if start is not None and end is not None and end > start:
                    dur = end - start
                else:
                    continue
            rows.append({
                "panel_id": panel_id,
                "source": f"ecociaf_{observer.lower()}",
                "observation_id": obs_id,
                "date": "26/05",
                "raw_op_num": op_num,
                "atomic_op_num": ECOCIAF_MAP[op_num],
                "duration_sec": dur,
            })
    return pd.DataFrame(rows)


def build_ecociaf_times(excels_dir: Path = Path("data/raw/Excel - Tempos Micro Tarefas")) -> pd.DataFrame:
    bea = parse_ecociaf_wide(excels_dir / "Tempos_ECOCIAF_Tirados_Por_Beatriz.xlsx", "Beatriz")
    ines = parse_ecociaf_wide(excels_dir / "Tempos_ECOCIAF_Tirados_por_Inês.xlsx", "Ines")
    raw = pd.concat([bea, ines], ignore_index=True)
    # Normalizar typo PCT01W → PCT01K
    raw["panel_id"] = raw["panel_id"].replace({"PCT01W": "PCT01K"})
    return aggregate_to_canonical(raw)

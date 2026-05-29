"""Previsão com os 4 modelos future, para uma geometria de painel.

Devolve a previsão CENTRAL (modelo general, com breakdown produtivo vs
desperdício) e os CENÁRIOS dos modelos de temperatura / experiência / hora,
para o utilizador analisar como cada variável afeta os tempos.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .. import estimate as E
from . import FUTURE_DIR, OP_IDLE, OP_MATERIAL
from .synth import WASTE_NAMES
from .train import fdesign

PRODUCTIVE_OPS = list(range(1, 15))
GENERAL_OPS = list(range(1, 17))  # 1–14 produtivas + 15 idle + 16 material

# Cenários expostos na página (valor + label legível) — destaques em cartões.
TEMP_SCENARIOS = [(10, "10°C — cold"), (20, "20°C — mild"), (30, "30°C — hot")]
EXP_SCENARIOS = [(2, "Novice (2 mo)"), (18, "Mid (18 mo)"), (48, "Senior (48 mo)")]
HOUR_SCENARIOS = [(9, "09h — morning"), (12, "12h — pre-lunch"),
                  (14, "14h — post-lunch"), (17, "17h — end of day")]

# Grelhas finas para o gráfico (curva suave que mostra a forma da relação).
TEMP_CURVE = list(range(8, 33, 2))                       # 8,10,…,32 °C
EXP_CURVE = [1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]   # meses
HOUR_CURVE = list(range(8, 18))                          # 8h…17h


def _op_name(op: int) -> str:
    return E.MICRO_OP_NAMES.get(op) or WASTE_NAMES.get(op, f"op{op}")


@lru_cache(maxsize=1)
def load_models(model_root: str = str(FUTURE_DIR)) -> dict:
    """Carrega os 4 modelos future (meta + joblib). Cacheado."""
    import joblib
    root = Path(model_root)
    models = {}
    for name in ("general", "temperature", "experience", "timeofday"):
        meta_p, mdl_p = root / name / "meta.json", root / name / "champion.joblib"
        if not (meta_p.exists() and mdl_p.exists()):
            raise FileNotFoundError(f"Modelo future '{name}' não treinado. Corre `pipeline future-build`.")
        meta = json.loads(meta_p.read_text())
        meta["model"] = joblib.load(mdl_p)
        models[name] = meta
    return models


def _predict_ops(m: dict, geom: dict, ops: list[int], extra: dict, level: str) -> list[dict]:
    """Itens {micro_op_num, name, point/lo/hi} para um modelo, com intervalo conformal."""
    base = {c: geom.get(c) for c in E.GEOM}
    rows = pd.DataFrame([{**base, **extra, "micro_op_num": op} for op in ops])
    X = E.align(pd.DataFrame(columns=m["design_cols"]), fdesign(rows, m["extra_cols"]))
    point = m["model"].predict(X)
    qmap = m["conformal"].get(level, {})
    qg = qmap.get("__global__", 0.0)
    items = []
    for op, p in zip(ops, point):
        p = max(0.0, float(p))
        q = float(qmap.get(str(op), qg))
        items.append({"micro_op_num": int(op), "micro_op_name": _op_name(op),
                      "point_sec": round(p, 1),
                      "lo_sec": round(max(0.0, p * (1 - q)), 1),
                      "hi_sec": round(p * (1 + q), 1)})
    return items


def _total(items: list[dict]) -> dict:
    return {"total_sec": round(sum(i["point_sec"] for i in items), 1),
            "total_lo_sec": round(sum(i["lo_sec"] for i in items), 1),
            "total_hi_sec": round(sum(i["hi_sec"] for i in items), 1)}


def _scenarios(m: dict, geom: dict, feature: str, scenarios, level: str) -> list[dict]:
    out = []
    for value, label in scenarios:
        items = _predict_ops(m, geom, PRODUCTIVE_OPS, {feature: value}, level)
        out.append({"value": value, "label": label, **_total(items)})
    return out


def _curve(m: dict, geom: dict, feature: str, values: list, level: str) -> list[dict]:
    """Curva fina (produtivo, ops 1–14) ao longo da grelha da variável."""
    out = []
    for v in values:
        items = _predict_ops(m, geom, PRODUCTIVE_OPS, {feature: v}, level)
        out.append({"value": v, "total_sec": round(sum(i["point_sec"] for i in items), 1)})
    return out


def predict_future(geom: dict, level: str = "q80") -> dict:
    """Previsão central (general) + cenários de temperatura/experiência/hora."""
    models = load_models()

    # --- modelo central: general (produtivo + desperdício) ---
    g_items = _predict_ops(models["general"], geom, GENERAL_OPS, {}, level)
    productive = sum(i["point_sec"] for i in g_items if i["micro_op_num"] <= 14)
    idle = sum(i["point_sec"] for i in g_items if i["micro_op_num"] == OP_IDLE)
    material = sum(i["point_sec"] for i in g_items if i["micro_op_num"] == OP_MATERIAL)
    grand = productive + idle + material
    pct = lambda x: round(100 * x / grand, 1) if grand else 0.0
    general = {
        "items": g_items,
        **_total(g_items),
        "breakdown": {
            "productive_sec": round(productive, 1), "productive_pct": pct(productive),
            "idle_no_value_sec": round(idle, 1), "idle_no_value_pct": pct(idle),
            "material_necessary_sec": round(material, 1), "material_necessary_pct": pct(material),
        },
    }

    return {
        "panel_id": geom.get("panel_id", "?"),
        "interval_level": level,
        "general": general,
        "temperature": {
            "feature": "temperatura_c", "unit": "°C", "optimal_label": "20°C — mild",
            "note": "Operators are most productive at mild temperatures; hot is much worse than cold.",
            "scenarios": _scenarios(models["temperature"], geom, "temperatura_c", TEMP_SCENARIOS, level),
            "curve": _curve(models["temperature"], geom, "temperatura_c", TEMP_CURVE, level),
        },
        "experience": {
            "feature": "experiencia_meses", "unit": "months", "optimal_label": "Senior (48 mo)",
            "note": "More experience → faster, consistently.",
            "scenarios": _scenarios(models["experience"], geom, "experiencia_meses", EXP_SCENARIOS, level),
            "curve": _curve(models["experience"], geom, "experiencia_meses", EXP_CURVE, level),
        },
        "timeofday": {
            "feature": "hora_do_dia", "unit": "h", "optimal_label": "09h — morning",
            "note": "Most productive early; slumps after lunch and at end of day.",
            "scenarios": _scenarios(models["timeofday"], geom, "hora_do_dia", HOUR_SCENARIOS, level),
            "curve": _curve(models["timeofday"], geom, "hora_do_dia", HOUR_CURVE, level),
        },
    }


def predict_future_project(geoms: list[dict], level: str = "q80") -> dict:
    """Agrega vários painéis (PDF multi-painel) num único resultado future.

    Soma item-a-item os tempos do modelo general e os totais de cada cenário.
    """
    results = [predict_future(g, level=level) for g in geoms]
    if len(results) == 1:
        return {**results[0], "n_panels": 1, "panel_ids": [results[0]["panel_id"]]}

    agg = results[0]
    out = {"panel_id": "PROJECT", "n_panels": len(results),
           "panel_ids": [r["panel_id"] for r in results], "interval_level": level}

    # general: soma por micro_op_num
    by_op: dict[int, dict] = {}
    for r in results:
        for it in r["general"]["items"]:
            op = it["micro_op_num"]
            cur = by_op.setdefault(op, {"micro_op_num": op, "micro_op_name": it["micro_op_name"],
                                        "point_sec": 0.0, "lo_sec": 0.0, "hi_sec": 0.0})
            for k in ("point_sec", "lo_sec", "hi_sec"):
                cur[k] = round(cur[k] + it[k], 1)
    items = [by_op[op] for op in sorted(by_op)]
    productive = sum(i["point_sec"] for i in items if i["micro_op_num"] <= 14)
    idle = sum(i["point_sec"] for i in items if i["micro_op_num"] == OP_IDLE)
    material = sum(i["point_sec"] for i in items if i["micro_op_num"] == OP_MATERIAL)
    grand = productive + idle + material
    pct = lambda x: round(100 * x / grand, 1) if grand else 0.0
    out["general"] = {"items": items, **_total(items), "breakdown": {
        "productive_sec": round(productive, 1), "productive_pct": pct(productive),
        "idle_no_value_sec": round(idle, 1), "idle_no_value_pct": pct(idle),
        "material_necessary_sec": round(material, 1), "material_necessary_pct": pct(material)}}

    # cenários + curva: soma totais por índice
    for key in ("temperature", "experience", "timeofday"):
        scen = []
        for i, base in enumerate(agg[key]["scenarios"]):
            tot = {"value": base["value"], "label": base["label"], "total_sec": 0.0,
                   "total_lo_sec": 0.0, "total_hi_sec": 0.0}
            for r in results:
                s = r[key]["scenarios"][i]
                for k in ("total_sec", "total_lo_sec", "total_hi_sec"):
                    tot[k] = round(tot[k] + s[k], 1)
            scen.append(tot)
        curve = []
        for i, base in enumerate(agg[key]["curve"]):
            tot = round(sum(r[key]["curve"][i]["total_sec"] for r in results), 1)
            curve.append({"value": base["value"], "total_sec": tot})
        out[key] = {**agg[key], "scenarios": scen, "curve": curve}
    return out


def models_meta() -> list[dict]:
    """Metadados leves dos 4 modelos (para GET /future/models)."""
    models = load_models()
    return [{"name": n, "champion": m["champion"], "lopo_mae": m["lopo_mae"],
             "noise_floor_mae": m["noise_floor"]["mae"], "extra_cols": m["extra_cols"],
             "n_train_obs": m["n_train_obs"]} for n, m in models.items()]

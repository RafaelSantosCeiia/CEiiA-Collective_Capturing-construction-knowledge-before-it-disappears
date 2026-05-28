"""API HTTP para o frontend: upload de desenho → extração → previsão.

Endpoints (compatíveis com o frontend em frontend/):
  GET  /health            liveness
  GET  /model             metadados do campeão (model_name + cobertura conformal)
  POST /predict/pdf       upload de PDF → previsão (multipart, campo `file`)
  POST /predict           previsão por código de painel já em cache ({key})
  POST /predict-drawing   forma "crua" (igual ao CLI), para uso próprio

O que a API devolve reaproveita exatamente o pipeline `predict_drawing`.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

import pandas as pd
from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import estimate as E
from .modeling import load_deployed
from .predict_drawing import predict_drawing

app = FastAPI(title="BluFab — Estimativa de tempos", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


def require_token(x_api_key: str | None = Header(default=None)):
    """Auth opcional: se API_KEY estiver definido (.env), exige header X-API-Key.

    Sem API_KEY definido → sem auth (dev local). Com API_KEY → protege o túnel
    público (n8n e frontend têm de enviar o header). Confidencialidade Casais.
    """
    expected = os.environ.get("API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(401, "X-API-Key em falta ou inválido.")

MODEL_DIR = Path("data/training/model")
CACHE = Path("data/training/panel_geometry.parquet")


# --- mapeamento para a forma que o frontend renderiza ----------------------

def _to_frontend(out: dict) -> dict:
    """predict_drawing → {key, predictions:[{op_id,op_order,predicted_duration_sec}], total_sec, ...}."""
    multi = out["n_panels"] > 1
    preds, order = [], 1
    for p in out["panels"]:
        for op in p["micro_ops"]:
            name = op["micro_op_name"]
            preds.append({
                "op_id": f"{p['panel_id']} · {name}" if multi else name,
                "op_order": order,
                "predicted_duration_sec": op["point_sec"],
                "lo_sec": op["lo_sec"], "hi_sec": op["hi_sec"],  # intervalo conformal
            })
            order += 1
    warnings = []
    if out.get("panels_without_geometry"):
        warnings.append("Sem geometria (precisa extração live): "
                        + ", ".join(out["panels_without_geometry"]))
    if multi:
        warnings.append(f"{out['n_panels']} painéis neste desenho — total do projeto agregado.")
    res = {
        "key": out.get("project_id"),
        "predictions": preds,  # plano (CSV / painel único)
        "total_sec": out["project_total_sec"],
        "total_lo_sec": out["project_total_lo_sec"],
        "total_hi_sec": out["project_total_hi_sec"],
        "interval_level": out.get("interval_level"),
        "warnings": warnings,
        # estrutura por painel (para a UI agrupar em dropdowns)
        "panels": [
            {
                "panel_id": p["panel_id"],
                "total_sec": p["total_sec"],
                "total_lo_sec": p["total_lo_sec"],
                "total_hi_sec": p["total_hi_sec"],
                "micro_ops": [
                    {"op_order": op["micro_op_num"], "op_id": op["micro_op_name"],
                     "predicted_duration_sec": op["point_sec"],
                     "lo_sec": op["lo_sec"], "hi_sec": op["hi_sec"]}
                    for op in p["micro_ops"]
                ],
            }
            for p in out["panels"]
        ],
    }
    # "Detected from PDF" para painel único
    if out["n_panels"] == 1 and out["panels"][0].get("_geom"):
        g = out["panels"][0]["_geom"]
        res["extracted"] = {
            "panel_id": out["panels"][0]["panel_id"],
            "largura_mm": g.get("largura_painel_mm"),
            "altura_mm": g.get("altura_painel_mm"),
            "espessura_mm": g.get("espessura_placa_mm"),
            "montantes": g.get("num_montantes"),
            "raias": g.get("num_raias"),
        }
    return res


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model")
def model_info(_auth=Depends(require_token)):
    try:
        m = load_deployed(MODEL_DIR)
    except FileNotFoundError:
        raise HTTPException(503, "Sem modelo deployado. Corre `pipeline train`.")
    return {
        "model_name": m["champion"],
        "champion": m["champion"],
        "cv_mae_sec": m.get("cv_mae"),
        "n_train_obs": m.get("n_train_obs"),
        "conformal_coverage": m.get("conformal_coverage"),
        "features": m.get("features"),
    }


@app.post("/predict/pdf")
async def predict_pdf(
    file: UploadFile = File(...),
    provider: str = Query("gemini", description="gemini | cache | claude | ollama"),
    level: str = Query("q80", description="q80 | q90"),
    _auth=Depends(require_token),
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(415, "Envia um ficheiro .pdf")
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(data); tmp.flush()
        try:
            out = predict_drawing(Path(tmp.name), provider=provider, model_dir=MODEL_DIR, level=level)
        except FileNotFoundError:
            raise HTTPException(503, "Sem modelo deployado. Corre `pipeline train`.")
        except Exception as e:
            raise HTTPException(500, f"{type(e).__name__}: {e}")
    if out["n_panels"] == 0:
        raise HTTPException(422, "Sem geometria neste PDF (se provider=cache e o projeto "
                                 "não está em cache, usa provider=gemini).")
    res = _to_frontend(out)
    res["filename"] = file.filename
    return res


@app.post("/predict")
def predict_by_key(body: dict = Body(...), _auth=Depends(require_token)):
    """Previsão rápida por código de painel já presente na cache de geometria."""
    key = (body.get("key") or "").strip().upper()
    level = body.get("level", "q80")
    if not key:
        raise HTTPException(422, "Falta 'key' (código do painel, ex.: PG02K).")
    if not CACHE.exists():
        raise HTTPException(503, "Sem cache de geometria.")
    cache = pd.read_parquet(CACHE)
    hit = cache[cache.panel_id.str.upper() == key]
    if hit.empty:
        raise HTTPException(404, f"Painel '{key}' não está em cache. Usa upload de PDF (/predict/pdf).")
    geom = hit.iloc[0].to_dict(); geom["panel_id"] = key
    dep = load_deployed(MODEL_DIR)
    panel = E.predict_panel(dep["model"], dep["design_cols"], dep["conformal"], geom, level=level)
    panel["_geom"] = geom
    out = {"project_id": geom.get("project_id", key), "n_panels": 1, "panels": [panel],
           "interval_level": level, "panels_without_geometry": [],
           "project_total_sec": panel["total_sec"], "project_total_lo_sec": panel["total_lo_sec"],
           "project_total_hi_sec": panel["total_hi_sec"]}
    res = _to_frontend(out); res["key"] = key
    return res


@app.post("/predict-drawing")
async def predict_drawing_raw(
    file: UploadFile = File(...),
    provider: str = Query("gemini"), level: str = Query("q80"),
    _auth=Depends(require_token),
):
    """Forma crua (estrutura projeto→painéis→micro-ops), igual ao CLI."""
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(data); tmp.flush()
        return predict_drawing(Path(tmp.name), provider=provider, model_dir=MODEL_DIR, level=level)

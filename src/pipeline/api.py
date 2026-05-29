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

import contextlib
import io
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import json
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


@app.get("/metrics")
def metrics(_auth=Depends(require_token)):
    """Métricas longitudinais (curva de aprendizagem, histórico, calibração, projeção)."""
    p = Path("data/training/metrics.json")
    if not p.exists():
        raise HTTPException(404, "Sem metrics.json. Corre `pipeline train`.")
    return json.loads(p.read_text())


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


# ===========================================================================
# RETRAIN — jobs assíncronos (n8n: POST /retrain → poll GET /retrain/{job_id})
# ===========================================================================
JOBS: dict[str, dict] = {}              # estado em memória (polling)
_JOBS_LOCK = threading.Lock()
LOG_PATH = Path("data/training/retrain_jobs.json")
SCHED_PATH = Path("data/training/schedule.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_log(job: dict) -> None:
    """Persiste o job terminado em retrain_jobs.json (últimos 100)."""
    try:
        log = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else []
    except Exception:
        log = []
    log = [j for j in log if j.get("job_id") != job["job_id"]]
    log.append(job)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(log[-100:], indent=2, default=str))


def _set(job_id: str, **patch) -> None:
    with _JOBS_LOCK:
        JOBS[job_id].update(patch)


def _run_retrain(job_id: str, params: dict) -> None:
    """Corre o retreino real (ou simulado) em background."""
    buf = io.StringIO()
    started = JOBS[job_id]["started_at"]
    try:
        if params.get("dry_run"):
            secs = max(1, min(int(params.get("dry_run_seconds", 15)), 120))
            time.sleep(secs)
            outcome = (params.get("dry_run_outcome") or "deployed").lower()
            if outcome == "failed":
                raise RuntimeError("Simulated failure (dry run).")
            _set(job_id, status=outcome, deployed=(outcome == "deployed"),
                 train_report={"model_name": "catboost (simulated)", "mae": 16.5},
                 finished_at=_now_iso())
        else:
            from .modeling import run as run_training
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                report = run_training(
                    trials=int(params.get("trials", 30)),
                    require_improvement=bool(params.get("require_improvement", True)),
                    timestamp=started,
                )
            champ = report["champion"]
            mae = report["deployed"]["cv_mae"]
            _set(job_id, status="deployed", deployed=True,
                 train_report={"model_name": champ, "mae": mae},
                 leaderboard=report.get("leaderboard"),
                 stdout_tail=buf.getvalue()[-4000:], finished_at=_now_iso())
    except Exception as e:
        _set(job_id, status="failed", deployed=False, error=f"{type(e).__name__}: {e}",
             stderr_tail=buf.getvalue()[-4000:], finished_at=_now_iso())
    finally:
        with _JOBS_LOCK:
            _append_log(JOBS[job_id])


@app.post("/retrain")
@app.post("/train")
def retrain(body: dict = Body(default={}), _auth=Depends(require_token)):
    """Arranca um retreino (assíncrono). Devolve job_id; faz poll em /retrain/{job_id}.

    Body (tudo opcional): {dry_run, dry_run_outcome, dry_run_seconds,
    trials, require_improvement, skip_benchmark, skip_tests}.
    """
    with _JOBS_LOCK:
        active = [j for j in JOBS.values() if j["status"] == "running"]
        if active:
            raise HTTPException(409, f"Já há um retreino a correr ({active[0]['job_id']}).")
        job_id = "job_" + uuid.uuid4().hex[:12]
        job = {
            "job_id": job_id, "status": "running", "deployed": None,
            "started_at": _now_iso(), "finished_at": None,
            "params": {k: body.get(k) for k in (
                "dry_run", "dry_run_outcome", "dry_run_seconds", "trials",
                "require_improvement", "skip_benchmark", "skip_tests")},
        }
        JOBS[job_id] = job
    threading.Thread(target=_run_retrain, args=(job_id, body), daemon=True).start()
    return job


@app.get("/retrain/log")
def retrain_log(limit: int = Query(20, ge=1, le=100), _auth=Depends(require_token)):
    """Histórico dos retreinos (mais recentes primeiro)."""
    try:
        log = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else []
    except Exception:
        log = []
    # inclui jobs em memória ainda a correr
    seen = {j.get("job_id") for j in log}
    live = [j for j in JOBS.values() if j["job_id"] not in seen]
    items = sorted(log + live, key=lambda j: j.get("started_at") or "", reverse=True)
    return {"items": items[:limit], "count": len(items)}


@app.get("/retrain/{job_id}")
def retrain_status(job_id: str, _auth=Depends(require_token)):
    """Estado de um job (para o n8n fazer poll até terminar)."""
    job = JOBS.get(job_id)
    if job is None:
        try:
            log = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else []
            job = next((j for j in log if j.get("job_id") == job_id), None)
        except Exception:
            job = None
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' não encontrado.")
    return job


# ===========================================================================
# SCHEDULE — próximo retreino automático (mensal, madrugada)
# ===========================================================================
def _next_monthly(hour: int = 3) -> datetime:
    now = datetime.now(timezone.utc)
    ny, nm = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    return datetime(ny, nm, 1, hour, 0, tzinfo=timezone.utc)


def _cron_field(field: str, lo: int, hi: int) -> set[int]:
    vals: set[int] = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/"); step = int(s)
        if part == "*":
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-"); start, end = int(a), int(b)
        else:
            start = end = int(part)
        vals.update(range(start, end + 1, step))
    return vals


def _cron_next(expr: str, after: datetime) -> datetime | None:
    """Próxima ocorrência de um cron de 5 campos (min hora dia-mês mês dia-semana), em UTC."""
    f = expr.split()
    if len(f) != 5:
        raise ValueError("cron expression must have 5 fields")
    mins, hours = _cron_field(f[0], 0, 59), _cron_field(f[1], 0, 23)
    doms, months = _cron_field(f[2], 1, 31), _cron_field(f[3], 1, 12)
    dows = {v % 7 for v in _cron_field(f[4], 0, 7)}  # 0 e 7 = domingo
    dom_r, dow_r = f[2] != "*", f[4] != "*"
    t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(366 * 24 * 60):
        if t.minute in mins and t.hour in hours and t.month in months:
            dom_ok, dow_ok = t.day in doms, ((t.weekday() + 1) % 7) in dows
            day_ok = (dom_ok or dow_ok) if (dom_r and dow_r) else (
                dom_ok if dom_r else dow_ok if dow_r else True)
            if day_ok:
                return t
        t += timedelta(minutes=1)
    return None


def _resolve_next(cron: str | None, explicit: str | None) -> str | None:
    if explicit:
        return str(explicit)
    if cron:
        try:
            nxt = _cron_next(cron, datetime.now(timezone.utc))
            if nxt:
                return nxt.isoformat()
        except Exception:
            return None
    return None


@app.get("/schedule")
def schedule(_auth=Depends(require_token)):
    """Estado do agendamento. Lê schedule.json (recalcula do cron); senão o mensal."""
    if SCHED_PATH.exists():
        try:
            data = json.loads(SCHED_PATH.read_text())
            # recalcula sempre a próxima execução a partir do cron guardado (não fica obsoleto)
            nxt = _resolve_next(data.get("cron"), None) or data.get("next_run_utc")
            if nxt:
                data["next_run_utc"] = nxt
                return data
        except Exception:
            pass
    nxt = _next_monthly()
    return {
        "next_run_utc": nxt.isoformat(), "cron": "0 3 1 * *", "cadence": "monthly",
        "source": "overnight retrain (n8n)", "timezone": "UTC", "updated_at": _now_iso(),
    }


@app.post("/schedule")
def set_schedule(body: dict = Body(...), _auth=Depends(require_token)):
    """n8n regista aqui o agendamento. Aceita `cron` (calcula a próxima) e/ou `next_run_utc`."""
    cron = body.get("cron")
    explicit = body.get("next_run_utc") or body.get("next_run_at") or body.get("next_run")
    nxt = _resolve_next(cron, explicit)
    if not nxt:
        raise HTTPException(
            422, "Envia 'cron' (ex.: '0 0 1 * *') ou 'next_run_utc' (ISO 8601). "
                 "Se enviaste cron, confirma que tem 5 campos.")
    data = {
        "next_run_utc": nxt,
        "cron": cron or "0 3 1 * *",
        "cadence": body.get("cadence", "monthly"),
        "source": body.get("source", "n8n"),
        "timezone": body.get("timezone", "UTC"),
        "updated_at": _now_iso(),
    }
    SCHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHED_PATH.write_text(json.dumps(data, indent=2))
    return data

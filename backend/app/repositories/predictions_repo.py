import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from app.utils.config import settings
from app.utils.io_utils import read_json, write_json

JOBS = settings.STORE_DIR / "prediction_jobs.json"

def _load_jobs():
    return read_json(JOBS, default={"jobs": []})

def _save_jobs(data):
    write_json(JOBS, data)

def save_run(filtros: Dict[str, Any], preds: List[Dict[str, Any]], summary: Dict[str, int]) -> Tuple[str, Path]:
    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    # guardar filas en json por job
    job_file = settings.STORE_DIR / f"preds_{job_id}.json"
    write_json(job_file, preds)

    jobs = _load_jobs()
    jobs["jobs"].append({
        "id": job_id,
        "created_at": created_at,
        "filters": filtros or {},
        "summary": summary,
        "total_items": len(preds),
        "mae": None
    })
    _save_jobs(jobs)
    return job_id, job_file

def list_jobs() -> list[dict]:
    return _load_jobs()["jobs"][::-1]

def get_job(job_id: str) -> dict:
    for j in _load_jobs()["jobs"]:
        if j["id"] == job_id:
            return j
    raise KeyError("job_id no existe")

def get_job_rows(job_id: str) -> List[Dict[str, Any]]:
    path = settings.STORE_DIR / f"preds_{job_id}.json"
    return read_json(path, default=[])

def set_job_mae(job_id: str, mae: float):
    data = _load_jobs()
    for j in data["jobs"]:
        if j["id"] == job_id:
            j["mae"] = mae
            break
    _save_jobs(data)

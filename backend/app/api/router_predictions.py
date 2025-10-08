from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Response
from io import StringIO
import csv
from datetime import datetime
import pandas as pd
from uuid import UUID
from app.schemas import PredictionRunResponse, HistoryItem, SummaryResponse
from app.services.predict_service import predict_from_df
from app.repositories import predictions_repo
from app.utils.deps import pagination_params
from app.utils.paginate import paginate
from app.utils.config import settings

router = APIRouter()

@router.post("/predictions/run", response_model=PredictionRunResponse)
async def run_prediction(
    file: UploadFile = File(...),
    tienda: str | None = None,
    campania: str | None = None,
    categoria: str | None = None
):
    filtros = {"tienda": tienda, "campania": campania, "categoria": categoria}
    df = pd.read_csv(StringIO((await file.read()).decode("utf-8")), low_memory=False)
    summary, preds = predict_from_df(df, filtros)
    job_id, _ = predictions_repo.save_run(filtros, preds, summary)

    return {
        "job_id": job_id,
        "summary": summary,
        "predictions": preds,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/predictions/history", response_model=list[HistoryItem])
def list_history(p=Depends(pagination_params)):
    jobs = predictions_repo.list_jobs()
    page_items, total = paginate(jobs, p["page"], p["size"])
    return [
        {
            "job_id": j["id"],
            "created_at": j["created_at"],
            "filtros": j.get("filters", {}),
            "mae": j.get("mae"),
            "total_items": j.get("total_items", 0)
        }
        for j in page_items
    ]

@router.get("/predictions/summary", response_model=SummaryResponse)
def get_summary():
    jobs = predictions_repo.list_jobs()
    total = sum(j.get("total_items", 0) for j in jobs)
    estados: dict[str,int] = {}
    for j in jobs:
        for k,v in (j.get("summary") or {}).items():
            estados[k] = estados.get(k,0) + v
    return {"total": total, "estados": estados}

@router.get("/predictions/{job_id}", response_model=PredictionRunResponse)
def get_job(job_id: UUID):
    j = predictions_repo.get_job(str(job_id))
    rows = predictions_repo.get_job_rows(str(job_id))
    return {
        "job_id": j["id"],
        "summary": j.get("summary", {}),
        "predictions": rows,
        "generated_at": j["created_at"]
    }

@router.get("/predictions/export")
def export_job(job_id: str):
    rows = predictions_repo.get_job_rows(job_id)
    if not rows:
        raise HTTPException(status_code=404, detail="job_id sin contenido")

    export_path = settings.EXPORT_DIR / f"predictions_{job_id}.csv"
    with export_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # descarga directa
    content = export_path.read_text(encoding="utf-8")
    return Response(content, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={export_path.name}"})

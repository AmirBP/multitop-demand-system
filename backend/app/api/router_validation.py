from fastapi import APIRouter, HTTPException
from app.schemas import CompareRequest, CompareResponse
from app.services.compare_service import compare_with_real

router = APIRouter()

@router.post("/validation/compare-real", response_model=CompareResponse)
def compare_real(body: CompareRequest):
    if not body.job_id:
        raise HTTPException(status_code=400, detail="job_id es requerido")
    try:
        result = compare_with_real(
            job_id=body.job_id,
            ventas_real_csv_base64=body.ventas_real_csv_base64,
            nivel=body.nivel
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

    # pydantic alias para "global"
    return CompareResponse(**{"global": result["global"], "por_sku": result["por_sku"], "observaciones": result["observaciones"]})

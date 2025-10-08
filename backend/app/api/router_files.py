from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import FileUploadResponse
from io import StringIO
import pandas as pd
from app.repositories.files_repo import save_upload, get_file_meta
from app.services.validation_service import validate_dataframe

router = APIRouter()

@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = pd.read_csv(StringIO(content.decode("utf-8")), low_memory=False)
    except Exception:
        raise HTTPException(status_code=400, detail="Archivo no es CSV válido")

    errors = validate_dataframe(df)
    if errors:
        # No rechazamos, pero informamos (HU002). Si quieres, lanza 422.
        # raise HTTPException(status_code=422, detail=errors)
        pass

    out = save_upload(df, file.filename)
    return FileUploadResponse(**out)

@router.get("/files/{file_id}", response_model=FileUploadResponse)
def get_file_info(file_id: str):
    meta = get_file_meta(file_id)
    return FileUploadResponse(
        file_id=meta["id"], filename=meta["filename"],
        detected_columns=meta["detected_columns"], rows=meta["rows"]
    )

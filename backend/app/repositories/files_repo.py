import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime
from app.utils.config import settings
from app.utils.io_utils import write_json, read_json

MANIFEST = settings.STORE_DIR / "files_manifest.json"

def _load_manifest():
    return read_json(MANIFEST, default={"files": []})

def _save_manifest(data):
    write_json(MANIFEST, data)

def save_upload(df: pd.DataFrame, filename: str) -> dict:
    file_id = str(uuid.uuid4())
    csv_path = settings.STORE_DIR / f"{file_id}.csv"
    df.to_csv(csv_path, index=False)

    manifest = _load_manifest()
    manifest["files"].append({
        "id": file_id,
        "filename": filename,
        "rows": len(df),
        "detected_columns": list(df.columns),
        "created_at": datetime.utcnow().isoformat()
    })
    _save_manifest(manifest)

    return {
        "file_id": file_id,
        "filename": filename,
        "rows": len(df),
        "detected_columns": list(df.columns)
    }

def get_file(file_id: str) -> Path:
    p = settings.STORE_DIR / f"{file_id}.csv"
    if not p.exists():
        raise FileNotFoundError("file_id no existe")
    return p

def get_file_meta(file_id: str) -> dict:
    m = _load_manifest()
    for f in m["files"]:
        if f["id"] == file_id:
            return f
    raise FileNotFoundError("file_id no existe")

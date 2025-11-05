from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# Files
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    detected_columns: List[str]
    rows: int

# Train
class TrainResponse(BaseModel):
    mae: float
    mape: float
    wape: float
    smape: float
    bias: float
    precision: float
    importancia: List[Dict[str, Any]]
    alerta: List[Dict[str, Any]]
    plot_data: List[Dict[str, Any]]

# Predictions
class PredictionItem(BaseModel):
    CodArticulo: str
    d_media: float
    d_sigma: float
    StockMes: float
    horizon: float
    seguridad: float
    stock_objetivo: float
    dias_cobertura: float
    porcentaje_sobrestock: float
    indice_riesgo_quiebre: float
    Estado: str
    Accion: str

class PredictionRunResponse(BaseModel):
    job_id: str
    summary: Dict[str, int]
    predictions: List[PredictionItem]
    generated_at: str

class HistoryItem(BaseModel):
    job_id: str
    created_at: str
    filtros: Dict[str, Any]
    mae: Optional[float] = None
    total_items: int

class SummaryResponse(BaseModel):
    total: int
    estados: Dict[str, int]

# Validation
class CompareRequest(BaseModel):
    job_id: str
    ventas_real_csv_base64: Optional[str] = None
    nivel: Literal["SKU", "Categoria", "Global"] = "SKU"   # ← en lugar de regex
    desde: Optional[str] = None
    hasta: Optional[str] = None

class CompareResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)       # ← para usar alias al serializar
    global_: Dict[str, float] = Field(..., alias="global")
    por_sku: List[Dict[str, Any]]
    observaciones: Optional[str] = None
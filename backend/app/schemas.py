"""
Schemas actualizados para soportar validación mejorada y métricas avanzadas del modelo
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# ============================================================================
# FILES - Schemas mejorados para HU001 y HU002
# ============================================================================

class ValidationIssue(BaseModel):
    """Representa un problema encontrado en la validación"""
    type: str = Field(..., description="Tipo de problema (ej: 'missing_columns', 'invalid_dates')")
    column: Optional[str] = Field(None, description="Columna afectada")
    message: str = Field(..., description="Descripción del problema")
    severity: Literal["error", "warning", "info"] = Field(..., description="Severidad")
    affected_rows: int = Field(0, description="Número de filas afectadas")
    sample_rows: List[int] = Field(default_factory=list, description="Muestra de filas afectadas")


class ValidationResult(BaseModel):
    """Resultado de validación de un archivo"""
    executed: bool = Field(..., description="Si se ejecutó la validación")
    is_valid: bool = Field(True, description="Si el archivo es válido")
    total_issues: int = Field(0, description="Total de problemas encontrados")
    errors: int = Field(0, description="Número de errores bloqueantes")
    warnings: int = Field(0, description="Número de advertencias")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Lista de problemas")


class FileUploadResponse(BaseModel):
    """Respuesta mejorada de carga de archivo"""
    file_id: str
    filename: str
    detected_columns: List[str]
    rows: int
    validation: ValidationResult = Field(
        default_factory=lambda: ValidationResult(executed=False, is_valid=True)
    )


class FileValidationResponse(BaseModel):
    """Respuesta de solo validación (sin guardar archivo)"""
    filename: str
    total_rows: int
    total_columns: int
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    info: List[Dict[str, Any]]
    summary: Dict[str, int]


# ============================================================================
# MODEL TRAINING - Métricas mejoradas para HU017
# ============================================================================

class ModelMetrics(BaseModel):
    """Métricas completas del modelo (HU017)"""
    # Métricas básicas de error
    mae: float = Field(..., description="Mean Absolute Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error (%)")
    wape: float = Field(..., description="Weighted Absolute Percentage Error (%)")
    smape: float = Field(..., description="Symmetric Mean Absolute Percentage Error (%)")
    rmse: float = Field(..., description="Root Mean Square Error")
    
    # Métricas de sesgo
    bias: float = Field(..., description="Forecast Bias (%)")
    
    # Métricas de precisión
    precision: float = Field(..., description="Precisión (100 - MAPE) (%)")
    
    # Métricas adicionales
    r2_score: Optional[float] = Field(None, description="Coeficiente de determinación R²")
    tracking_signal: Optional[float] = Field(None, description="Tracking Signal")
    
    # Información del set de prueba
    test_size: int = Field(..., description="Tamaño del conjunto de prueba")
    test_date_range: Dict[str, str] = Field(..., description="Rango de fechas del test")


class FeatureImportance(BaseModel):
    """Importancia de features"""
    feature: str
    importance: float
    rank: int


class TrainResponse(BaseModel):
    """Respuesta mejorada de entrenamiento (HU017)"""
    # Métricas del modelo
    metrics: ModelMetrics
    
    # Importancia de features
    feature_importance: List[FeatureImportance] = Field(
        ..., 
        description="Top features por importancia"
    )
    
    # Alertas de stock
    stock_alerts: List[Dict[str, Any]] = Field(
        ..., 
        description="Alertas de stock generadas"
    )
    
    # Datos para visualización
    plot_data: List[Dict[str, Any]] = Field(
        ...,
        description="Datos para gráfico real vs predicho"
    )
    
    # Metadatos del entrenamiento
    training_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Información adicional del entrenamiento"
    )
    
    # Backward compatibility (deprecated)
    mae: Optional[float] = None
    mape: Optional[float] = None
    importancia: Optional[List[Dict[str, Any]]] = None
    alerta: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# HYPERPARAMETERS - Nuevo para HU009
# ============================================================================

class HyperparametersConfig(BaseModel):
    """Configuración de hiperparámetros del modelo (HU009)"""
    # XGBoost parameters
    n_estimators: int = Field(500, ge=10, le=2000, description="Número de árboles")
    learning_rate: float = Field(0.03, gt=0, le=1, description="Tasa de aprendizaje")
    max_depth: int = Field(6, ge=1, le=20, description="Profundidad máxima de árboles")
    subsample: float = Field(0.85, gt=0, le=1, description="Fracción de samples para entrenamiento")
    colsample_bytree: float = Field(0.85, gt=0, le=1, description="Fracción de features por árbol")
    reg_lambda: float = Field(1.0, ge=0, description="L2 regularization")
    reg_alpha: float = Field(0.5, ge=0, description="L1 regularization")
    
    # Training parameters
    random_state: int = Field(42, description="Semilla para reproducibilidad")
    objective: str = Field("reg:squarederror", description="Función objetivo")
    
    # Metadata
    config_name: Optional[str] = Field(None, description="Nombre de esta configuración")
    description: Optional[str] = Field(None, description="Descripción de la configuración")


class HyperparametersResponse(BaseModel):
    """Respuesta de consulta de hiperparámetros"""
    current_config: HyperparametersConfig
    config_id: str
    last_updated: Optional[str] = None
    available_configs: List[str] = Field(default_factory=list)


class HyperparameterSearchRequest(BaseModel):
    """Solicitud de búsqueda de hiperparámetros"""
    search_type: Literal["grid", "random", "bayesian"] = "random"
    n_iterations: int = Field(10, ge=1, le=100)
    cv_folds: int = Field(3, ge=2, le=10)
    
    # Rangos de búsqueda
    n_estimators_range: List[int] = Field([100, 500, 1000])
    learning_rate_range: List[float] = Field([0.01, 0.05, 0.1])
    max_depth_range: List[int] = Field([3, 6, 9])


# ============================================================================
# PREDICTIONS - Schemas existentes con mejoras
# ============================================================================

class PredictionItem(BaseModel):
    """Item de predicción mejorado con clasificación de riesgo"""
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
    
    # Nuevos campos para HU016
    nivel_riesgo: Optional[Literal["CRITICO", "ALTO", "MEDIO", "BAJO", "OK"]] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5, description="1=Más urgente, 5=Menos urgente")


class PredictionRunResponse(BaseModel):
    """Respuesta de ejecución de predicción"""
    job_id: str
    summary: Dict[str, int]
    predictions: List[PredictionItem]
    generated_at: str
    
    # Nuevos campos
    filters_applied: Optional[Dict[str, Any]] = None
    total_skus: Optional[int] = None
    risk_distribution: Optional[Dict[str, int]] = None  # Distribución por nivel de riesgo


class HistoryItem(BaseModel):
    """Item de historial con más información"""
    job_id: str
    created_at: str
    filtros: Dict[str, Any]
    mae: Optional[float] = None
    total_items: int
    
    # Nuevos campos
    risk_summary: Optional[Dict[str, int]] = None
    execution_time: Optional[float] = None


class SummaryResponse(BaseModel):
    """Respuesta de resumen mejorada"""
    total: int
    estados: Dict[str, int]
    
    # Nuevos campos
    risk_levels: Optional[Dict[str, int]] = None
    urgent_actions: Optional[int] = None


# ============================================================================
# VALIDATION (comparación con reales) - Mejorado para HU012
# ============================================================================

class CompareRequest(BaseModel):
    """Solicitud de comparación mejorada"""
    job_id: str
    ventas_real_csv_base64: Optional[str] = None
    nivel: Literal["SKU", "Categoria", "Global"] = "SKU"
    desde: Optional[str] = None
    hasta: Optional[str] = None
    
    # Nuevos filtros
    sku_filter: Optional[List[str]] = None
    categoria_filter: Optional[List[str]] = None


class SKUComparison(BaseModel):
    """Comparación individual por SKU"""
    CodArticulo: str
    Pred: float
    Real: float
    MAE: float
    APE: Optional[float] = None
    Bias: float
    Categoria: Optional[str] = None


class CompareResponse(BaseModel):
    """Respuesta mejorada de comparación"""
    model_config = ConfigDict(populate_by_name=True)
    
    # Métricas globales
    global_: Dict[str, float] = Field(..., alias="global")
    
    # Comparaciones por SKU
    por_sku: List[SKUComparison]
    
    # Observaciones y análisis
    observaciones: Optional[str] = None
    
    # Nuevos campos para HU012
    mejores_skus: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Top 10 SKUs con mejor precisión"
    )
    peores_skus: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Top 10 SKUs con peor precisión"
    )
    distribucion_errores: Optional[Dict[str, int]] = Field(
        None,
        description="Distribución de errores por rangos"
    )


# ============================================================================
# MONITORING - Nuevo para HU014
# ============================================================================

class SystemHealthResponse(BaseModel):
    """Estado de salud del sistema (HU014)"""
    status: Literal["healthy", "degraded", "down"]
    timestamp: str
    uptime: float  # segundos
    
    components: Dict[str, Any] = Field(
        ...,
        description="Estado de componentes individuales"
    )
    
    metrics: Dict[str, float] = Field(
        ...,
        description="Métricas del sistema"
    )


class LogEntry(BaseModel):
    """Entrada de log"""
    timestamp: str
    level: str
    logger: str
    message: str
    extra: Optional[Dict[str, Any]] = None


class LogsResponse(BaseModel):
    """Respuesta de consulta de logs"""
    logs: List[LogEntry]
    total: int
    page: int
    page_size: int


# ============================================================================
# CAMPAIGNS - Nuevo para HU015
# ============================================================================

class CampaignInfo(BaseModel):
    """Información de campaña"""
    campania_id: str
    nombre: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    total_skus: int
    ventas_totales: float


class CampaignImpactResponse(BaseModel):
    """Análisis de impacto de campaña (HU015)"""
    campania_id: str
    periodo_analizado: Dict[str, str]
    
    # Métricas de impacto
    incremento_ventas: float  # % respecto a baseline
    skus_afectados: int
    ventas_totales: float
    
    # Comparación con/sin campaña
    ventas_con_campania: float
    ventas_sin_campania_estimado: float
    
    # Top productos impactados
    top_skus: List[Dict[str, Any]]


# ============================================================================
# SCHEDULER - Nuevo para HU013
# ============================================================================

class TrainingScheduleConfig(BaseModel):
    """Configuración de reentrenamiento automático (HU013)"""
    enabled: bool = Field(True, description="Activar/desactivar scheduler")
    frequency: Literal["daily", "weekly", "monthly"] = Field("monthly")
    day_of_month: Optional[int] = Field(None, ge=1, le=28)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    hour: int = Field(2, ge=0, le=23, description="Hora del día (24h)")
    
    auto_deploy: bool = Field(False, description="Desplegar modelo automáticamente")
    notification_email: Optional[str] = None


class TrainingHistoryItem(BaseModel):
    """Item de historial de entrenamientos"""
    training_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: Literal["running", "completed", "failed"]
    metrics: Optional[ModelMetrics] = None
    error_message: Optional[str] = None
    triggered_by: Literal["manual", "scheduled", "api"]


class SchedulerStatusResponse(BaseModel):
    """Estado del scheduler"""
    enabled: bool
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    last_run_status: Optional[str] = None
    configuration: TrainingScheduleConfig
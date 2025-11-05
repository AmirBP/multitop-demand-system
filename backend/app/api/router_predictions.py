"""
Router de Predicciones - Doble fuente (CSV + BD)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
from datetime import datetime
import pandas as pd
from io import StringIO
import tempfile
import os
import logging

from app.schemas import PredictionRunResponse
from app.services.predict_service import predict_from_df
from app.services.data_source_service import DataSourceService
from app.repositories import predictions_repo

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predictions/run", response_model=PredictionRunResponse)
async def run_prediction(
    file: Optional[UploadFile] = File(None),
    source: str = Query("csv", description="'csv' o 'database'"),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    tienda: Optional[str] = Query(None),
    campania: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None)
):
    """
    HU003: Ejecuta predicción desde CSV o BD
    
    Ejemplos:
    
    1. Desde CSV:
       POST /api/predictions/run
       - file: archivo.csv
       - source: "csv"
    
    2. Desde BD:
       POST /api/predictions/run?source=database&fecha_desde=2024-01-01&fecha_hasta=2024-12-31
    """
    logger.info(f"🚀 Predicción desde: {source}")
    
    try:
        service = DataSourceService()
        
        # ============================================================
        # CARGAR DATOS SEGÚN ORIGEN
        # ============================================================
        if source.lower() == 'csv':
            if not file:
                raise HTTPException(400, "Archivo requerido con source='csv'")
            
            # Leer CSV
            content = await file.read()
            csv_text = content.decode("utf-8")
            
            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
                tmp.write(csv_text)
                tmp_path = tmp.name
            
            try:
                df, metadata = service.load_from_csv(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        elif source.lower() == 'database':
            if not fecha_desde or not fecha_hasta:
                raise HTTPException(400, "fecha_desde y fecha_hasta requeridos con source='database'")
            
            df, metadata = service.load_from_database(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                tienda=tienda,
                categoria=categoria
            )
        
        else:
            raise HTTPException(400, f"Source inválido: {source}")
        
        # Validar datos
        df = service.validate_data(df)
        
        # ============================================================
        # EJECUTAR PREDICCIÓN
        # ============================================================
        filtros = {k: v for k, v in {
            "tienda": tienda,
            "campania": campania,
            "categoria": categoria
        }.items() if v}
        
        summary, preds = predict_from_df(df, filtros)
        
        # ============================================================
        # GUARDAR RESULTADOS
        # ============================================================
        job_id, _ = predictions_repo.save_run(filtros, preds, summary)
        predictions_repo.save_data_source(job_id, metadata)
        
        logger.info(f"✅ Job completado: {job_id}")
        
        return {
            "job_id": job_id,
            "summary": summary,
            "predictions": preds,
            "generated_at": datetime.utcnow().isoformat(),
            "data_source": {
                "type": metadata["source_type"],
                "name": metadata["source_name"],
                "total_rows": metadata["total_rows"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/predictions/data-sources/info")
def get_sources_info():
    """Info de fuentes disponibles"""
    return {
        "csv": {
            "available": True,
            "description": "Carga manual de archivos CSV"
        },
        "database": {
            "available": False,  # Cambiar a True cuando configures MULTITOP_DATABASE_URL
            "message": "Configurar MULTITOP_DATABASE_URL para habilitar"
        }
    }


@router.get("/predictions/history")
def list_history(page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=100)):
    """Lista historial de predicciones"""
    try:
        jobs = predictions_repo.list_jobs()
        start = (page - 1) * size
        end = start + size
        
        return {
            "jobs": jobs[start:end],
            "total": len(jobs),
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/predictions/{job_id}")
def get_job_details(job_id: str):
    """Obtiene detalles de un job"""
    try:
        job = predictions_repo.get_job(job_id)
        rows = predictions_repo.get_job_rows(job_id)
        return {
            "job": job,
            "predictions": rows
        }
    except KeyError:
        raise HTTPException(404, f"Job {job_id} no encontrado")
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
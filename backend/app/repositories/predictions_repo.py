"""
Repositorio de predicciones - SQL Server
"""
from typing import List, Dict, Any, Tuple
from app.database import get_results_db
import json
import logging

logger = logging.getLogger(__name__)


def save_run(filtros: Dict[str, Any], preds: List[Dict], summary: Dict[str, int]) -> Tuple[str, None]:
    """Guarda job de predicción"""
    db = get_results_db()
    
    query_job = """
        INSERT INTO prediction_jobs 
        (filters, summary, total_items, metadata)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?)
    """
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query_job, (
            json.dumps(filtros or {}),
            json.dumps(summary),
            len(preds),
            json.dumps({})
        ))
        job_id = str(cursor.fetchone()[0])
    
    if preds:
        _save_rows(job_id, preds)
    
    logger.info(f"Job guardado: {job_id}")
    return job_id, None


def _save_rows(job_id: str, rows: List[Dict]) -> int:
    """Guarda filas de predicción"""
    if not rows:
        return 0
    
    db = get_results_db()
    
    query = """
        INSERT INTO prediction_rows 
        (job_id, cod_articulo, d_media, d_sigma, stock_mes, horizon,
         seguridad, stock_objetivo, dias_cobertura, porcentaje_sobrestock,
         indice_riesgo_quiebre, estado, accion, nivel_riesgo, prioridad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    data = [
        (
            job_id,
            r.get("CodArticulo"),
            r.get("d_media"),
            r.get("d_sigma"),
            r.get("StockMes"),
            r.get("horizon"),
            r.get("seguridad"),
            r.get("stock_objetivo"),
            r.get("dias_cobertura"),
            r.get("porcentaje_sobrestock"),
            r.get("indice_riesgo_quiebre"),
            r.get("Estado"),
            r.get("Accion"),
            r.get("nivel_riesgo"),
            r.get("prioridad")
        )
        for r in rows
    ]
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, data)
    
    logger.info(f"Guardadas {len(rows)} filas")
    return len(rows)


def save_data_source(job_id: str, metadata: Dict):
    """Guarda origen de datos"""
    db = get_results_db()
    
    query = """
        INSERT INTO data_sources 
        (job_id, source_type, source_name, total_rows, metadata)
        VALUES (?, ?, ?, ?, ?)
    """
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            job_id,
            metadata.get("source_type", "CSV"),
            metadata.get("source_name", "unknown"),
            metadata.get("total_rows", 0),
            json.dumps(metadata)
        ))
    
    logger.info(f"Data source guardado: {metadata['source_type']}")


def list_jobs(limit: int = 50, offset: int = 0) -> List[Dict]:
    """Lista jobs con origen"""
    db = get_results_db()
    
    query = """
        SELECT 
            j.id, j.created_at, j.filters, j.summary, j.total_items, j.mae,
            ds.source_type, ds.source_name
        FROM prediction_jobs j
        LEFT JOIN data_sources ds ON j.id = ds.job_id
        ORDER BY j.created_at DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    
    results = db.execute_query(query, (offset, limit))
    
    return [
        {
            "id": str(r['id']),
            "created_at": r['created_at'].isoformat(),
            "filters": json.loads(r['filters']) if r['filters'] else {},
            "summary": json.loads(r['summary']) if r['summary'] else {},
            "total_items": r['total_items'],
            "mae": float(r['mae']) if r['mae'] else None,
            "source_type": r['source_type'],
            "source_name": r['source_name']
        }
        for r in results
    ]


def get_job(job_id: str) -> Dict:
    """Obtiene job específico"""
    db = get_results_db()
    
    query = """
        SELECT 
            j.id, j.created_at, j.filters, j.summary, j.total_items, j.mae,
            ds.source_type, ds.source_name
        FROM prediction_jobs j
        LEFT JOIN data_sources ds ON j.id = ds.job_id
        WHERE j.id = ?
    """
    
    results = db.execute_query(query, (job_id,))
    if not results:
        raise KeyError(f"Job {job_id} no encontrado")
    
    r = results[0]
    return {
        "id": str(r['id']),
        "created_at": r['created_at'].isoformat(),
        "filters": json.loads(r['filters']) if r['filters'] else {},
        "summary": json.loads(r['summary']) if r['summary'] else {},
        "total_items": r['total_items'],
        "mae": float(r['mae']) if r['mae'] else None,
        "source_type": r.get('source_type'),
        "source_name": r.get('source_name')
    }


def get_job_rows(job_id: str, limit: int = None, offset: int = 0) -> List[Dict]:
    """Obtiene filas de predicción"""
    db = get_results_db()
    
    query = """
        SELECT 
            cod_articulo, d_media, d_sigma, stock_mes, horizon,
            seguridad, stock_objetivo, dias_cobertura, porcentaje_sobrestock,
            indice_riesgo_quiebre, estado, accion, nivel_riesgo, prioridad
        FROM prediction_rows
        WHERE job_id = ?
        ORDER BY id
    """
    
    if limit:
        query += f" OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
    
    results = db.execute_query(query, (job_id,))
    
    return [
        {
            "CodArticulo": r['cod_articulo'],
            "d_media": float(r['d_media']),
            "d_sigma": float(r['d_sigma']),
            "StockMes": float(r['stock_mes']),
            "horizon": int(r['horizon']),
            "seguridad": float(r['seguridad']),
            "stock_objetivo": float(r['stock_objetivo']),
            "dias_cobertura": float(r['dias_cobertura']) if r['dias_cobertura'] else None,
            "porcentaje_sobrestock": float(r['porcentaje_sobrestock']) if r['porcentaje_sobrestock'] else None,
            "indice_riesgo_quiebre": float(r['indice_riesgo_quiebre']) if r['indice_riesgo_quiebre'] else None,
            "Estado": r['estado'],
            "Accion": r['accion'],
            "nivel_riesgo": r['nivel_riesgo'],
            "prioridad": r['prioridad']
        }
        for r in results
    ]


def set_job_mae(job_id: str, mae: float):
    """Actualiza MAE"""
    db = get_results_db()
    query = "UPDATE prediction_jobs SET mae = ? WHERE id = ?"
    db.execute_non_query(query, (mae, job_id))
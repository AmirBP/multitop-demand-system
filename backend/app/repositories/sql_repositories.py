"""
Implementación SQL de los repositorios
Compatible con PostgreSQL y SQL Server (con ajustes menores)
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from app.repositories.data_layer import (
    IFilesRepository, 
    IPredictionsRepository, 
    IConfigRepository
)

logger = logging.getLogger(__name__)


class SQLFilesRepository(IFilesRepository):
    """Implementación SQL para archivos"""
    
    def __init__(self, connection_string: str):
        """
        Args:
            connection_string: URL de conexión SQLAlchemy
                PostgreSQL: postgresql://user:pass@host:5432/dbname
                SQL Server: mssql+pyodbc://user:pass@host/dbname?driver=ODBC+Driver+17+for+SQL+Server
        """
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20
        )
        logger.info("SQLFilesRepository inicializado")
    
    def save_file(self, df_info: Dict[str, Any]) -> str:
        query = text("""
            INSERT INTO uploaded_files 
            (filename, rows, detected_columns, validation, file_path)
            VALUES (:filename, :rows, :columns, :validation, :path)
            RETURNING id
        """)
        
        with self.engine.begin() as conn:
            result = conn.execute(query, {
                "filename": df_info.get("filename", "unknown.csv"),
                "rows": df_info.get("rows", 0),
                "columns": json.dumps(df_info.get("detected_columns", [])),
                "validation": json.dumps(df_info.get("validation", {})),
                "path": df_info.get("file_path")
            })
            file_id = str(result.fetchone()[0])
        
        logger.info(f"Archivo guardado en BD: {file_id}")
        return file_id
    
    def get_file(self, file_id: str) -> Dict[str, Any]:
        query = text("""
            SELECT id, filename, rows, detected_columns, validation, 
                   file_path, created_at
            FROM uploaded_files
            WHERE id = :file_id AND deleted_at IS NULL
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"file_id": file_id}).fetchone()
        
        if not result:
            raise FileNotFoundError(f"Archivo {file_id} no encontrado")
        
        return {
            "id": str(result[0]),
            "filename": result[1],
            "rows": result[2],
            "detected_columns": json.loads(result[3]) if result[3] else [],
            "validation": json.loads(result[4]) if result[4] else {},
            "file_path": result[5],
            "created_at": result[6].isoformat()
        }
    
    def list_files(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        # Obtener total
        count_query = text("""
            SELECT COUNT(*) FROM uploaded_files WHERE deleted_at IS NULL
        """)
        
        # Obtener datos
        data_query = text("""
            SELECT id, filename, rows, detected_columns, validation, 
                   file_path, created_at
            FROM uploaded_files
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        with self.engine.connect() as conn:
            total = conn.execute(count_query).scalar()
            results = conn.execute(data_query, {"limit": limit, "offset": offset}).fetchall()
        
        files = [
            {
                "id": str(r[0]),
                "filename": r[1],
                "rows": r[2],
                "detected_columns": json.loads(r[3]) if r[3] else [],
                "validation": json.loads(r[4]) if r[4] else {},
                "file_path": r[5],
                "created_at": r[6].isoformat()
            }
            for r in results
        ]
        
        return files, total
    
    def delete_file(self, file_id: str) -> bool:
        # Soft delete
        query = text("""
            UPDATE uploaded_files
            SET deleted_at = NOW()
            WHERE id = :file_id AND deleted_at IS NULL
        """)
        
        with self.engine.begin() as conn:
            result = conn.execute(query, {"file_id": file_id})
        
        return result.rowcount > 0


class SQLPredictionsRepository(IPredictionsRepository):
    """Implementación SQL para predicciones"""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20
        )
        logger.info("SQLPredictionsRepository inicializado")
    
    def save_prediction_job(self, job_data: Dict[str, Any]) -> str:
        query = text("""
            INSERT INTO prediction_jobs 
            (filters, summary, total_items, mae, metadata)
            VALUES (:filters, :summary, :total_items, :mae, :metadata)
            RETURNING id
        """)
        
        with self.engine.begin() as conn:
            result = conn.execute(query, {
                "filters": json.dumps(job_data.get("filters", {})),
                "summary": json.dumps(job_data.get("summary", {})),
                "total_items": job_data.get("total_items", 0),
                "mae": job_data.get("mae"),
                "metadata": json.dumps(job_data.get("metadata", {}))
            })
            job_id = str(result.fetchone()[0])
        
        logger.info(f"Job guardado en BD: {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        query = text("""
            SELECT id, created_at, updated_at, filters, summary, 
                   total_items, mae, metadata
            FROM prediction_jobs
            WHERE id = :job_id
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"job_id": job_id}).fetchone()
        
        if not result:
            raise KeyError(f"Job {job_id} no encontrado")
        
        return {
            "id": str(result[0]),
            "created_at": result[1].isoformat(),
            "updated_at": result[2].isoformat() if result[2] else None,
            "filters": json.loads(result[3]) if result[3] else {},
            "summary": json.loads(result[4]) if result[4] else {},
            "total_items": result[5],
            "mae": float(result[6]) if result[6] else None,
            "metadata": json.loads(result[7]) if result[7] else {}
        }
    
    def save_prediction_rows(self, job_id: str, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0
        
        # Batch insert
        query = text("""
            INSERT INTO prediction_rows 
            (job_id, cod_articulo, d_media, d_sigma, stock_mes, horizon,
             seguridad, stock_objetivo, dias_cobertura, porcentaje_sobrestock,
             indice_riesgo_quiebre, estado, accion, nivel_riesgo, prioridad)
            VALUES 
            (:job_id, :cod_articulo, :d_media, :d_sigma, :stock_mes, :horizon,
             :seguridad, :stock_objetivo, :dias_cobertura, :porcentaje_sobrestock,
             :indice_riesgo_quiebre, :estado, :accion, :nivel_riesgo, :prioridad)
        """)
        
        # Preparar datos
        insert_data = [
            {
                "job_id": job_id,
                "cod_articulo": row.get("CodArticulo"),
                "d_media": row.get("d_media"),
                "d_sigma": row.get("d_sigma"),
                "stock_mes": row.get("StockMes"),
                "horizon": row.get("horizon"),
                "seguridad": row.get("seguridad"),
                "stock_objetivo": row.get("stock_objetivo"),
                "dias_cobertura": row.get("dias_cobertura"),
                "porcentaje_sobrestock": row.get("porcentaje_sobrestock"),
                "indice_riesgo_quiebre": row.get("indice_riesgo_quiebre"),
                "estado": row.get("Estado"),
                "accion": row.get("Accion"),
                "nivel_riesgo": row.get("nivel_riesgo"),
                "prioridad": row.get("prioridad")
            }
            for row in rows
        ]
        
        with self.engine.begin() as conn:
            conn.execute(query, insert_data)
        
        logger.info(f"Guardadas {len(rows)} filas en BD para job {job_id}")
        return len(rows)
    
    def get_prediction_rows(
        self, 
        job_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        
        query_template = """
            SELECT cod_articulo, d_media, d_sigma, stock_mes, horizon,
                   seguridad, stock_objetivo, dias_cobertura, porcentaje_sobrestock,
                   indice_riesgo_quiebre, estado, accion, nivel_riesgo, prioridad
            FROM prediction_rows
            WHERE job_id = :job_id
            ORDER BY id
        """
        
        if limit is not None:
            query_template += " LIMIT :limit OFFSET :offset"
            params = {"job_id": job_id, "limit": limit, "offset": offset}
        else:
            query_template += " OFFSET :offset"
            params = {"job_id": job_id, "offset": offset}
        
        query = text(query_template)
        
        with self.engine.connect() as conn:
            results = conn.execute(query, params).fetchall()
        
        return [
            {
                "CodArticulo": r[0],
                "d_media": float(r[1]),
                "d_sigma": float(r[2]),
                "StockMes": float(r[3]),
                "horizon": int(r[4]),
                "seguridad": float(r[5]),
                "stock_objetivo": float(r[6]),
                "dias_cobertura": float(r[7]) if r[7] else None,
                "porcentaje_sobrestock": float(r[8]) if r[8] else None,
                "indice_riesgo_quiebre": float(r[9]) if r[9] else None,
                "Estado": r[10],
                "Accion": r[11],
                "nivel_riesgo": r[12],
                "prioridad": r[13]
            }
            for r in results
        ]
    
    def list_jobs(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        # Similar a list_files
        count_query = text("SELECT COUNT(*) FROM prediction_jobs")
        
        data_query = text("""
            SELECT id, created_at, filters, summary, total_items, mae
            FROM prediction_jobs
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        with self.engine.connect() as conn:
            total = conn.execute(count_query).scalar()
            results = conn.execute(data_query, {"limit": limit, "offset": offset}).fetchall()
        
        jobs = [
            {
                "id": str(r[0]),
                "created_at": r[1].isoformat(),
                "filters": json.loads(r[2]) if r[2] else {},
                "summary": json.loads(r[3]) if r[3] else {},
                "total_items": r[4],
                "mae": float(r[5]) if r[5] else None
            }
            for r in results
        ]
        
        return jobs, total
    
    def update_job_mae(self, job_id: str, mae: float) -> bool:
        query = text("""
            UPDATE prediction_jobs
            SET mae = :mae, updated_at = NOW()
            WHERE id = :job_id
        """)
        
        with self.engine.begin() as conn:
            result = conn.execute(query, {"job_id": job_id, "mae": mae})
        
        return result.rowcount > 0


class SQLConfigRepository(IConfigRepository):
    """Implementación SQL para configuraciones"""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        logger.info("SQLConfigRepository inicializado")
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> str:
        query = text("""
            INSERT INTO configurations 
            (config_type, config_name, config_data, is_current, description)
            VALUES (:type, :name, :data, TRUE, :desc)
            RETURNING id
        """)
        
        with self.engine.begin() as conn:
            result = conn.execute(query, {
                "type": config_type,
                "name": config_data.get("config_name"),
                "data": json.dumps(config_data),
                "desc": config_data.get("description")
            })
            config_id = str(result.fetchone()[0])
        
        logger.info(f"Configuración guardada: {config_id}")
        return config_id
    
    def get_current_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        query = text("""
            SELECT id, config_data, created_at
            FROM configurations
            WHERE config_type = :type AND is_current = TRUE
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"type": config_type}).fetchone()
        
        if not result:
            return None
        
        return {
            "id": str(result[0]),
            "config": json.loads(result[1]),
            "created_at": result[2].isoformat()
        }
    
    def get_config_by_id(self, config_id: str) -> Optional[Dict[str, Any]]:
        query = text("""
            SELECT id, config_type, config_data, created_at
            FROM configurations
            WHERE id = :id
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"id": config_id}).fetchone()
        
        if not result:
            return None
        
        return {
            "id": str(result[0]),
            "config_type": result[1],
            "config": json.loads(result[2]),
            "created_at": result[3].isoformat()
        }
    
    def list_configs(self, config_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        query = text("""
            SELECT id, config_name, config_data, is_current, created_at
            FROM configurations
            WHERE config_type = :type
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        with self.engine.connect() as conn:
            results = conn.execute(query, {"type": config_type, "limit": limit}).fetchall()
        
        return [
            {
                "id": str(r[0]),
                "config_name": r[1],
                "config": json.loads(r[2]),
                "is_current": r[3],
                "created_at": r[4].isoformat()
            }
            for r in results
        ]
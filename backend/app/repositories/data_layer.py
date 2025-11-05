"""
Capa de Abstracción de Datos (Data Access Layer)
Implementación local con archivos JSON, preparada para migración a SQL

Este módulo proporciona una interfaz unificada para acceso a datos que puede
usar archivos JSON (desarrollo/MVP) o base de datos SQL (producción) sin
cambiar el código del resto de la aplicación.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import uuid
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# INTERFACES ABSTRACTAS (Contratos que deben cumplir todas las implementaciones)
# ============================================================================

class IFilesRepository(ABC):
    """Interfaz para repositorio de archivos cargados"""
    
    @abstractmethod
    def save_file(self, df_info: Dict[str, Any]) -> str:
        """Guarda información de un archivo cargado. Retorna ID."""
        pass
    
    @abstractmethod
    def get_file(self, file_id: str) -> Dict[str, Any]:
        """Obtiene información de un archivo por ID."""
        pass
    
    @abstractmethod
    def list_files(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        """Lista archivos con paginación. Retorna (lista, total)."""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo. Retorna True si exitoso."""
        pass


class IPredictionsRepository(ABC):
    """Interfaz para repositorio de predicciones"""
    
    @abstractmethod
    def save_prediction_job(self, job_data: Dict[str, Any]) -> str:
        """Guarda un job de predicción. Retorna job_id."""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Obtiene información de un job."""
        pass
    
    @abstractmethod
    def save_prediction_rows(self, job_id: str, rows: List[Dict[str, Any]]) -> int:
        """Guarda filas de predicción. Retorna cantidad guardada."""
        pass
    
    @abstractmethod
    def get_prediction_rows(
        self, 
        job_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Obtiene filas de predicción con paginación."""
        pass
    
    @abstractmethod
    def list_jobs(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        """Lista jobs con paginación."""
        pass
    
    @abstractmethod
    def update_job_mae(self, job_id: str, mae: float) -> bool:
        """Actualiza el MAE de un job."""
        pass


class IConfigRepository(ABC):
    """Interfaz para repositorio de configuraciones"""
    
    @abstractmethod
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> str:
        """Guarda una configuración. Retorna config_id."""
        pass
    
    @abstractmethod
    def get_current_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración actual de un tipo."""
        pass
    
    @abstractmethod
    def get_config_by_id(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una configuración específica por ID."""
        pass
    
    @abstractmethod
    def list_configs(self, config_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Lista configuraciones de un tipo."""
        pass


# ============================================================================
# IMPLEMENTACIÓN LOCAL CON JSON
# ============================================================================

class JSONFilesRepository(IFilesRepository):
    """Implementación local usando archivos JSON"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.manifest_file = self.storage_dir / "files_manifest.json"
    
    def _load_manifest(self) -> Dict:
        if not self.manifest_file.exists():
            return {"files": []}
        with open(self.manifest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_manifest(self, data: Dict):
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_file(self, df_info: Dict[str, Any]) -> str:
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        manifest = self._load_manifest()
        manifest["files"].append({
            "id": file_id,
            "filename": df_info.get("filename", "unknown.csv"),
            "rows": df_info.get("rows", 0),
            "detected_columns": df_info.get("detected_columns", []),
            "validation": df_info.get("validation", {}),
            "created_at": timestamp,
            "file_path": str(self.storage_dir / f"{file_id}.csv")
        })
        self._save_manifest(manifest)
        
        logger.info(f"Archivo guardado con ID: {file_id}")
        return file_id
    
    def get_file(self, file_id: str) -> Dict[str, Any]:
        manifest = self._load_manifest()
        for file_info in manifest["files"]:
            if file_info["id"] == file_id:
                return file_info
        raise FileNotFoundError(f"Archivo {file_id} no encontrado")
    
    def list_files(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        manifest = self._load_manifest()
        files = manifest["files"]
        total = len(files)
        
        # Ordenar por fecha descendente
        files_sorted = sorted(files, key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Paginación
        paginated = files_sorted[offset:offset + limit]
        
        return paginated, total
    
    def delete_file(self, file_id: str) -> bool:
        manifest = self._load_manifest()
        original_length = len(manifest["files"])
        
        # Filtrar archivo
        manifest["files"] = [f for f in manifest["files"] if f["id"] != file_id]
        
        if len(manifest["files"]) < original_length:
            self._save_manifest(manifest)
            
            # Eliminar archivo físico si existe
            file_path = self.storage_dir / f"{file_id}.csv"
            if file_path.exists():
                file_path.unlink()
            
            logger.info(f"Archivo eliminado: {file_id}")
            return True
        
        return False


class JSONPredictionsRepository(IPredictionsRepository):
    """Implementación local de predicciones usando JSON"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.jobs_file = self.storage_dir / "prediction_jobs.json"
    
    def _load_jobs(self) -> Dict:
        if not self.jobs_file.exists():
            return {"jobs": []}
        with open(self.jobs_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_jobs(self, data: Dict):
        with open(self.jobs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_prediction_job(self, job_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        jobs = self._load_jobs()
        jobs["jobs"].append({
            "id": job_id,
            "created_at": timestamp,
            "filters": job_data.get("filters", {}),
            "summary": job_data.get("summary", {}),
            "total_items": job_data.get("total_items", 0),
            "mae": job_data.get("mae"),
            "metadata": job_data.get("metadata", {})
        })
        self._save_jobs(jobs)
        
        logger.info(f"Job de predicción guardado: {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        jobs = self._load_jobs()
        for job in jobs["jobs"]:
            if job["id"] == job_id:
                return job
        raise KeyError(f"Job {job_id} no encontrado")
    
    def save_prediction_rows(self, job_id: str, rows: List[Dict[str, Any]]) -> int:
        rows_file = self.storage_dir / f"predictions_{job_id}.json"
        with open(rows_file, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Guardadas {len(rows)} filas para job {job_id}")
        return len(rows)
    
    def get_prediction_rows(
        self, 
        job_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        rows_file = self.storage_dir / f"predictions_{job_id}.json"
        
        if not rows_file.exists():
            return []
        
        with open(rows_file, 'r', encoding='utf-8') as f:
            rows = json.load(f)
        
        # Paginación
        if limit is not None:
            return rows[offset:offset + limit]
        return rows[offset:]
    
    def list_jobs(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        jobs = self._load_jobs()
        jobs_list = jobs["jobs"]
        total = len(jobs_list)
        
        # Ordenar por fecha descendente
        jobs_sorted = sorted(jobs_list, key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Paginación
        paginated = jobs_sorted[offset:offset + limit]
        
        return paginated, total
    
    def update_job_mae(self, job_id: str, mae: float) -> bool:
        jobs = self._load_jobs()
        
        for job in jobs["jobs"]:
            if job["id"] == job_id:
                job["mae"] = mae
                job["updated_at"] = datetime.utcnow().isoformat()
                self._save_jobs(jobs)
                logger.info(f"MAE actualizado para job {job_id}: {mae}")
                return True
        
        return False


class JSONConfigRepository(IConfigRepository):
    """Implementación local de configuraciones usando JSON"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_config_file(self, config_type: str) -> Path:
        return self.storage_dir / f"config_{config_type}.json"
    
    def _load_config_file(self, config_type: str) -> Dict:
        config_file = self._get_config_file(config_type)
        if not config_file.exists():
            return {"configs": [], "current": None}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_config_file(self, config_type: str, data: Dict):
        config_file = self._get_config_file(config_type)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> str:
        config_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        data = self._load_config_file(config_type)
        
        config_entry = {
            "id": config_id,
            "config": config_data,
            "created_at": timestamp
        }
        
        data["configs"].append(config_entry)
        data["current"] = config_id  # El más reciente es el actual
        
        self._save_config_file(config_type, data)
        
        logger.info(f"Configuración {config_type} guardada: {config_id}")
        return config_id
    
    def get_current_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        data = self._load_config_file(config_type)
        
        if not data.get("current"):
            return None
        
        current_id = data["current"]
        for config in data["configs"]:
            if config["id"] == current_id:
                return config
        
        return None
    
    def get_config_by_id(self, config_id: str) -> Optional[Dict[str, Any]]:
        # Buscar en todos los tipos de configuración
        for config_file in self.storage_dir.glob("config_*.json"):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for config in data.get("configs", []):
                if config["id"] == config_id:
                    return config
        
        return None
    
    def list_configs(self, config_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        data = self._load_config_file(config_type)
        configs = data.get("configs", [])
        
        # Ordenar por fecha descendente
        configs_sorted = sorted(configs, key=lambda x: x.get("created_at", ""), reverse=True)
        
        return configs_sorted[:limit]


# ============================================================================
# FACTORY PARA CREAR REPOSITORIOS
# ============================================================================

class RepositoryFactory:
    """Factory para crear repositorios según configuración"""
    
    @staticmethod
    def create_files_repository(backend: str = "json", **kwargs) -> IFilesRepository:
        """
        Crea un repositorio de archivos
        
        Args:
            backend: Tipo de backend ('json' o 'sql')
            **kwargs: Parámetros específicos del backend
        
        Returns:
            Instancia de IFilesRepository
        """
        if backend == "json":
            from backend.app.utils.config import settings
            return JSONFilesRepository(settings.STORE_DIR)
        
        elif backend == "sql":
            # TODO: Implementar cuando se migre a SQL
            # from app.repositories.sql_repositories import SQLFilesRepository
            # return SQLFilesRepository(**kwargs)
            raise NotImplementedError("Backend SQL aún no implementado. Ver documentación de migración.")
        
        else:
            raise ValueError(f"Backend desconocido: {backend}")
    
    @staticmethod
    def create_predictions_repository(backend: str = "json", **kwargs) -> IPredictionsRepository:
        """Crea un repositorio de predicciones"""
        if backend == "json":
            from backend.app.utils.config import settings
            return JSONPredictionsRepository(settings.STORE_DIR)
        
        elif backend == "sql":
            raise NotImplementedError("Backend SQL aún no implementado. Ver documentación de migración.")
        
        else:
            raise ValueError(f"Backend desconocido: {backend}")
    
    @staticmethod
    def create_config_repository(backend: str = "json", **kwargs) -> IConfigRepository:
        """Crea un repositorio de configuraciones"""
        if backend == "json":
            from backend.app.utils.config import settings
            return JSONConfigRepository(settings.OUTPUT_DIR / "configs")
        
        elif backend == "sql":
            raise NotImplementedError("Backend SQL aún no implementado. Ver documentación de migración.")
        
        else:
            raise ValueError(f"Backend desconocido: {backend}")


# ============================================================================
# INSTANCIAS GLOBALES (Singleton Pattern)
# ============================================================================

# Estas variables se inicializan una vez y se reutilizan
_files_repo = None
_predictions_repo = None
_config_repo = None


def get_files_repository() -> IFilesRepository:
    """Obtiene instancia singleton del repositorio de archivos"""
    global _files_repo
    if _files_repo is None:
        # TODO: Leer desde configuración o variable de entorno
        backend = "json"  # En producción: os.getenv("DB_BACKEND", "json")
        _files_repo = RepositoryFactory.create_files_repository(backend)
    return _files_repo


def get_predictions_repository() -> IPredictionsRepository:
    """Obtiene instancia singleton del repositorio de predicciones"""
    global _predictions_repo
    if _predictions_repo is None:
        backend = "json"
        _predictions_repo = RepositoryFactory.create_predictions_repository(backend)
    return _predictions_repo


def get_config_repository() -> IConfigRepository:
    """Obtiene instancia singleton del repositorio de configuraciones"""
    global _config_repo
    if _config_repo is None:
        backend = "json"
        _config_repo = RepositoryFactory.create_config_repository(backend)
    return _config_repo


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def reset_repositories():
    """
    Resetea las instancias singleton (útil para testing)
    """
    global _files_repo, _predictions_repo, _config_repo
    _files_repo = None
    _predictions_repo = None
    _config_repo = None


def configure_backend(backend: str):
    """
    Configura el backend a usar
    
    Args:
        backend: 'json' o 'sql'
    """
    reset_repositories()
    # Las próximas llamadas a get_*_repository() usarán el nuevo backend
    logger.info(f"Backend configurado a: {backend}")
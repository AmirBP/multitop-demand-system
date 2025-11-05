"""
Repositorio para gestión de configuraciones del modelo
Almacena y recupera hiperparámetros y otras configuraciones
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from backend.app.utils.config import settings
from app.utils.io_utils import read_json, write_json
from app.schemas import HyperparametersConfig

# Archivos de configuración
CONFIGS_DIR = settings.OUTPUT_DIR / "configs"
CONFIGS_DIR.mkdir(exist_ok=True, parents=True)

CURRENT_CONFIG_FILE = CONFIGS_DIR / "current_hyperparameters.json"
CONFIGS_HISTORY_FILE = CONFIGS_DIR / "hyperparameters_history.json"


def get_hyperparameters() -> Dict[str, Any]:
    """
    Obtiene la configuración actual de hiperparámetros
    
    Returns:
        Configuración actual con metadata
    """
    if not CURRENT_CONFIG_FILE.exists():
        # Crear configuración por defecto
        default = _get_default_config()
        save_hyperparameters(default)
    
    return read_json(CURRENT_CONFIG_FILE, default=None)


def save_hyperparameters(config: HyperparametersConfig) -> str:
    """
    Guarda una nueva configuración de hiperparámetros
    
    Args:
        config: Configuración a guardar
    
    Returns:
        ID de la configuración guardada
    """
    config_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Preparar documento
    config_doc = {
        "id": config_id,
        "config": config.dict(),
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # Guardar como configuración actual
    write_json(CURRENT_CONFIG_FILE, config_doc)
    
    # Agregar al historial
    _add_to_history(config_doc)
    
    # Si tiene nombre, guardar también como named config
    if config.config_name:
        _save_named_config(config.config_name, config_doc)
    
    return config_id


def list_configs() -> List[str]:
    """
    Lista todas las configuraciones guardadas por nombre
    
    Returns:
        Lista de nombres de configuraciones
    """
    configs = []
    
    # Buscar archivos de configuración nombrados
    for file_path in CONFIGS_DIR.glob("config_*.json"):
        try:
            config = read_json(file_path, default=None)
            if config and "config" in config:
                name = config["config"].get("config_name")
                if name:
                    configs.append(name)
        except Exception:
            continue
    
    return sorted(configs)


def get_config_by_name(config_name: str) -> Dict[str, Any]:
    """
    Obtiene una configuración por nombre
    
    Args:
        config_name: Nombre de la configuración
    
    Returns:
        Configuración solicitada
    
    Raises:
        FileNotFoundError: Si la configuración no existe
    """
    # Buscar archivo de configuración
    config_file = CONFIGS_DIR / f"config_{config_name}.json"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuración '{config_name}' no encontrada")
    
    return read_json(config_file, default=None)


def get_config_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de configuraciones
    
    Args:
        limit: Número máximo de configuraciones a retornar
    
    Returns:
        Lista de configuraciones históricas
    """
    history = read_json(CONFIGS_HISTORY_FILE, default={"configs": []})
    configs = history.get("configs", [])
    
    # Retornar las más recientes
    return configs[-limit:][::-1]


def _add_to_history(config_doc: Dict[str, Any]):
    """
    Agrega una configuración al historial
    
    Args:
        config_doc: Documento de configuración
    """
    history = read_json(CONFIGS_HISTORY_FILE, default={"configs": []})
    
    # Agregar nueva configuración
    history["configs"].append(config_doc)
    
    # Mantener solo últimas 50
    if len(history["configs"]) > 50:
        history["configs"] = history["configs"][-50:]
    
    write_json(CONFIGS_HISTORY_FILE, history)


def _save_named_config(name: str, config_doc: Dict[str, Any]):
    """
    Guarda una configuración con nombre
    
    Args:
        name: Nombre de la configuración
        config_doc: Documento de configuración
    """
    config_file = CONFIGS_DIR / f"config_{name}.json"
    write_json(config_file, config_doc)


def _get_default_config() -> HyperparametersConfig:
    """
    Obtiene la configuración por defecto
    
    Returns:
        Configuración por defecto
    """
    return HyperparametersConfig(
        n_estimators=500,
        learning_rate=0.03,
        max_depth=6,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        reg_alpha=0.5,
        random_state=42,
        objective="reg:squarederror",
        config_name="default",
        description="Configuración por defecto del sistema"
    )


def apply_config_to_model(model_class, config: HyperparametersConfig):
    """
    Aplica una configuración a una instancia de modelo
    
    Args:
        model_class: Clase del modelo (ej: XGBRegressor)
        config: Configuración de hiperparámetros
    
    Returns:
        Instancia del modelo configurada
    """
    return model_class(
        n_estimators=config.n_estimators,
        learning_rate=config.learning_rate,
        max_depth=config.max_depth,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        reg_lambda=config.reg_lambda,
        reg_alpha=config.reg_alpha,
        objective=config.objective,
        random_state=config.random_state
    )
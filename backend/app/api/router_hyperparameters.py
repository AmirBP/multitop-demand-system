"""
Router para gestión de hiperparámetros del modelo (HU009)
Permite consultar y actualizar la configuración del modelo
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import logging
from typing import Optional

from app.schemas import (
    HyperparametersConfig,
    HyperparametersResponse,
    HyperparameterSearchRequest
)
from app.repositories.config_repo import (
    get_hyperparameters,
    save_hyperparameters,
    list_configs,
    get_config_by_name
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/model/hyperparameters", response_model=HyperparametersResponse)
def get_current_hyperparameters():
    """
    HU009: Obtiene la configuración actual de hiperparámetros
    
    Returns:
        Configuración actual del modelo
    """
    try:
        config = get_hyperparameters()
        available = list_configs()
        
        return HyperparametersResponse(
            current_config=config["config"],
            config_id=config["id"],
            last_updated=config.get("updated_at"),
            available_configs=available
        )
    except Exception as e:
        logger.error(f"Error al obtener hiperparámetros: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener configuración: {str(e)}"
        )


@router.post("/model/hyperparameters", response_model=HyperparametersResponse)
def update_hyperparameters(config: HyperparametersConfig):
    """
    HU009: Actualiza la configuración de hiperparámetros
    
    Args:
        config: Nueva configuración de hiperparámetros
    
    Returns:
        Configuración actualizada
    
    Raises:
        HTTPException 400: Configuración inválida
    """
    try:
        # Validar rangos
        _validate_config(config)
        
        # Guardar configuración
        config_id = save_hyperparameters(config)
        
        logger.info(f"Hiperparámetros actualizados: {config_id}")
        
        return HyperparametersResponse(
            current_config=config,
            config_id=config_id,
            last_updated=datetime.utcnow().isoformat(),
            available_configs=list_configs()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar hiperparámetros: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar configuración: {str(e)}"
        )


@router.get("/model/hyperparameters/configs")
def list_hyperparameter_configs():
    """
    Lista todas las configuraciones guardadas
    
    Returns:
        Lista de nombres de configuraciones disponibles
    """
    try:
        configs = list_configs()
        return {
            "total": len(configs),
            "configs": configs
        }
    except Exception as e:
        logger.error(f"Error al listar configuraciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar configuraciones: {str(e)}"
        )


@router.get("/model/hyperparameters/configs/{config_name}", response_model=HyperparametersResponse)
def get_hyperparameter_config(config_name: str):
    """
    Obtiene una configuración específica por nombre
    
    Args:
        config_name: Nombre de la configuración
    
    Returns:
        Configuración solicitada
    
    Raises:
        HTTPException 404: Configuración no encontrada
    """
    try:
        config = get_config_by_name(config_name)
        
        return HyperparametersResponse(
            current_config=config["config"],
            config_id=config["id"],
            last_updated=config.get("updated_at"),
            available_configs=list_configs()
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Configuración '{config_name}' no encontrada"
        )
    except Exception as e:
        logger.error(f"Error al obtener configuración: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener configuración: {str(e)}"
        )


@router.post("/model/hyperparameters/reset")
def reset_to_default():
    """
    Restablece los hiperparámetros a valores por defecto
    
    Returns:
        Configuración por defecto
    """
    try:
        default_config = HyperparametersConfig(
            n_estimators=500,
            learning_rate=0.03,
            max_depth=6,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            reg_alpha=0.5,
            config_name="default",
            description="Configuración por defecto del sistema"
        )
        
        config_id = save_hyperparameters(default_config)
        
        logger.info("Hiperparámetros restablecidos a valores por defecto")
        
        return HyperparametersResponse(
            current_config=default_config,
            config_id=config_id,
            last_updated=datetime.utcnow().isoformat(),
            available_configs=list_configs()
        )
    
    except Exception as e:
        logger.error(f"Error al restablecer configuración: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al restablecer configuración: {str(e)}"
        )


@router.post("/model/hyperparameters/search")
async def search_hyperparameters(
    request: HyperparameterSearchRequest,
    background_tasks: BackgroundTasks
):
    """
    HU009: Inicia una búsqueda automática de hiperparámetros
    
    Args:
        request: Configuración de la búsqueda
        background_tasks: Para ejecución en segundo plano
    
    Returns:
        ID de la búsqueda iniciada
    
    Note:
        Esta es una implementación futura. Por ahora retorna 501 Not Implemented.
    """
    # TODO: Implementar búsqueda de hiperparámetros con GridSearch/RandomSearch
    # Requiere:
    # 1. Carga de datos de entrenamiento
    # 2. Cross-validation
    # 3. Ejecución en background
    # 4. Almacenamiento de resultados
    
    raise HTTPException(
        status_code=501,
        detail="Búsqueda automática de hiperparámetros en desarrollo. "
               "Por ahora, configure manualmente con POST /model/hyperparameters"
    )


def _validate_config(config: HyperparametersConfig):
    """
    Valida que la configuración sea razonable
    
    Args:
        config: Configuración a validar
    
    Raises:
        ValueError: Si la configuración es inválida
    """
    # Validaciones adicionales de negocio
    if config.n_estimators < 50:
        raise ValueError("n_estimators muy bajo (mínimo recomendado: 50)")
    
    if config.learning_rate > 0.3:
        raise ValueError("learning_rate muy alto (máximo recomendado: 0.3)")
    
    if config.max_depth > 15:
        raise ValueError("max_depth muy alto (máximo recomendado: 15)")
    
    # Validar combinaciones
    if config.subsample < 0.5:
        raise ValueError("subsample muy bajo (mínimo recomendado: 0.5)")
    
    if config.colsample_bytree < 0.5:
        raise ValueError("colsample_bytree muy bajo (mínimo recomendado: 0.5)")


@router.get("/model/hyperparameters/presets")
def get_preset_configs():
    """
    Obtiene configuraciones preset recomendadas
    
    Returns:
        Lista de configuraciones preset
    """
    presets = {
        "default": HyperparametersConfig(
            n_estimators=500,
            learning_rate=0.03,
            max_depth=6,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            reg_alpha=0.5,
            config_name="default",
            description="Configuración balanceada por defecto"
        ),
        "high_accuracy": HyperparametersConfig(
            n_estimators=1000,
            learning_rate=0.01,
            max_depth=8,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=0.5,
            reg_alpha=0.3,
            config_name="high_accuracy",
            description="Maximiza precisión (más lento)"
        ),
        "fast_training": HyperparametersConfig(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=4,
            subsample=0.7,
            colsample_bytree=0.7,
            reg_lambda=2.0,
            reg_alpha=1.0,
            config_name="fast_training",
            description="Entrenamiento rápido (menos preciso)"
        ),
        "balanced": HyperparametersConfig(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            reg_alpha=0.5,
            config_name="balanced",
            description="Balance entre velocidad y precisión"
        )
    }
    
    return {
        "presets": {name: config.dict() for name, config in presets.items()},
        "recommended": "default"
    }
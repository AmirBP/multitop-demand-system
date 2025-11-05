"""
Router mejorado para carga de archivos (HU001 y HU002)
Implementa validación robusta y manejo de errores detallado
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from io import StringIO
import pandas as pd
import logging

from app.schemas import FileUploadResponse, FileValidationResponse
from app.repositories.files_repo import save_upload, get_file_meta
from app.services.validation_service import validate_dataframe

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    validate: bool = Query(True, description="Ejecutar validaciones"),
    strict: bool = Query(True, description="Rechazar archivo si hay errores")
):
    """
    HU001: Carga manual de datos CSV
    HU002: Validación de estructura de datos
    
    Args:
        file: Archivo CSV a cargar
        validate: Si True, ejecuta validaciones
        strict: Si True, rechaza archivos con errores
    
    Returns:
        Información del archivo cargado y resultados de validación
    
    Raises:
        HTTPException 400: Archivo no es CSV válido
        HTTPException 422: Errores de validación encontrados (si strict=True)
    """
    logger.info(f"Iniciando carga de archivo: {file.filename}")
    
    # Leer contenido
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode("utf-8")), low_memory=False)
        logger.info(f"CSV parseado exitosamente: {len(df)} filas, {len(df.columns)} columnas")
    except UnicodeDecodeError:
        logger.error("Error de codificación en archivo")
        raise HTTPException(
            status_code=400, 
            detail="Archivo no tiene codificación UTF-8 válida. Intente guardar el archivo con codificación UTF-8."
        )
    except pd.errors.EmptyDataError:
        logger.error("Archivo CSV vacío")
        raise HTTPException(
            status_code=400,
            detail="El archivo CSV está vacío o no contiene datos válidos."
        )
    except Exception as e:
        logger.error(f"Error al parsear CSV: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Archivo no es un CSV válido: {str(e)}"
        )
    
    # Validar estructura (HU002)
    validation_issues = []
    is_valid = True
    
    if validate:
        logger.info("Ejecutando validaciones...")
        validation_issues, is_valid = validate_dataframe(df, strict_mode=strict)
        
        errors = [i for i in validation_issues if i["severity"] == "error"]
        warnings = [i for i in validation_issues if i["severity"] == "warning"]
        
        logger.info(f"Validación completada: {len(errors)} errores, {len(warnings)} warnings")
        
        # Si strict y hay errores, rechazar
        if strict and errors:
            logger.warning(f"Archivo rechazado por errores de validación: {len(errors)}")
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Validación fallida. El archivo contiene errores que deben corregirse.",
                    "errors": errors,
                    "warnings": warnings,
                    "total_errors": len(errors),
                    "total_warnings": len(warnings)
                }
            )
    
    # Guardar archivo
    try:
        file_info = save_upload(df, file.filename)
        logger.info(f"Archivo guardado con ID: {file_info['file_id']}")
        
        # Agregar información de validación a la respuesta
        response = {
            **file_info,
            "validation": {
                "executed": validate,
                "is_valid": is_valid,
                "total_issues": len(validation_issues),
                "errors": len([i for i in validation_issues if i["severity"] == "error"]),
                "warnings": len([i for i in validation_issues if i["severity"] == "warning"]),
                "issues": validation_issues if validation_issues else []
            }
        }
        
        return FileUploadResponse(**response)
    
    except Exception as e:
        logger.error(f"Error al guardar archivo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar archivo: {str(e)}"
        )


@router.post("/files/validate", response_model=FileValidationResponse)
async def validate_file_only(
    file: UploadFile = File(...),
    strict: bool = Query(True, description="Modo estricto de validación")
):
    """
    Valida un archivo CSV sin guardarlo
    Útil para pre-validación antes de carga definitiva
    
    Args:
        file: Archivo CSV a validar
        strict: Modo estricto
    
    Returns:
        Resultados detallados de validación
    """
    logger.info(f"Validando archivo (sin guardar): {file.filename}")
    
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode("utf-8")), low_memory=False)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al leer archivo: {str(e)}"
        )
    
    validation_issues, is_valid = validate_dataframe(df, strict_mode=strict)
    
    errors = [i for i in validation_issues if i["severity"] == "error"]
    warnings = [i for i in validation_issues if i["severity"] == "warning"]
    info = [i for i in validation_issues if i["severity"] == "info"]
    
    return FileValidationResponse(
        filename=file.filename,
        total_rows=len(df),
        total_columns=len(df.columns),
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        info=info,
        summary={
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "total_info": len(info),
            "blocking_errors": len(errors) if strict else 0
        }
    )


@router.get("/files/{file_id}", response_model=FileUploadResponse)
def get_file_info(file_id: str):
    """
    Obtiene información de un archivo previamente cargado
    
    Args:
        file_id: ID del archivo
    
    Returns:
        Información del archivo
    
    Raises:
        HTTPException 404: Archivo no encontrado
    """
    try:
        meta = get_file_meta(file_id)
        return FileUploadResponse(
            file_id=meta["id"],
            filename=meta["filename"],
            detected_columns=meta["detected_columns"],
            rows=meta["rows"],
            validation=meta.get("validation", {"executed": False})
        )
    except FileNotFoundError:
        logger.warning(f"Archivo no encontrado: {file_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Archivo con ID {file_id} no encontrado"
        )
    except Exception as e:
        logger.error(f"Error al obtener info de archivo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener información del archivo: {str(e)}"
        )


@router.get("/files/{file_id}/validation")
def get_file_validation(file_id: str):
    """
    Obtiene los resultados de validación de un archivo
    
    Args:
        file_id: ID del archivo
    
    Returns:
        Resultados de validación almacenados
    """
    try:
        meta = get_file_meta(file_id)
        validation = meta.get("validation")
        
        if not validation:
            raise HTTPException(
                status_code=404,
                detail="No hay información de validación para este archivo"
            )
        
        return validation
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo con ID {file_id} no encontrado"
        )
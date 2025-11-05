"""
Configuración de la aplicación - SQL Server
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Directorios
    OUTPUT_DIR: Path = Path("outputs")
    STORE_DIR: Path = OUTPUT_DIR / "store"
    EXPORT_DIR: Path = OUTPUT_DIR / "exports"
    LOG_DIR: Path = OUTPUT_DIR / "logs"
    
    # CORS
    ALLOW_ORIGINS: list[str] = ["*"]
    
    # ============================================================================
    # SQL SERVER
    # ============================================================================
    DATABASE_URL: str  # OBLIGATORIO
    MULTITOP_DATABASE_URL: Optional[str] = None  # OPCIONAL
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    
    # Aplicación
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "MultiTop Demand System"
    VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Crear carpetas
settings.OUTPUT_DIR.mkdir(exist_ok=True)
settings.STORE_DIR.mkdir(exist_ok=True, parents=True)
settings.EXPORT_DIR.mkdir(exist_ok=True, parents=True)
settings.LOG_DIR.mkdir(exist_ok=True, parents=True)
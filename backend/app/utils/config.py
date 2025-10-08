from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OUTPUT_DIR: Path = Path("outputs")
    STORE_DIR: Path = OUTPUT_DIR / "store"          # simulación DB
    EXPORT_DIR: Path = OUTPUT_DIR / "exports"
    LOG_DIR: Path = OUTPUT_DIR / "logs"
    ALLOW_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"

settings = Settings()

# asegurar carpetas
settings.OUTPUT_DIR.mkdir(exist_ok=True)
settings.STORE_DIR.mkdir(exist_ok=True, parents=True)
settings.EXPORT_DIR.mkdir(exist_ok=True, parents=True)
settings.LOG_DIR.mkdir(exist_ok=True, parents=True)

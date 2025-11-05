import logging
from logging.handlers import RotatingFileHandler
from backend.app.utils.config import settings
from pathlib import Path

def setup_logging():
    log_file: Path = settings.LOG_DIR / "app.log"
    handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # evitar duplicar handlers en hot-reload
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(handler)

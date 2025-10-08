from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router_health import router as health_router
from app.api.router_files import router as files_router
from app.api.router_model import router as model_router
from app.api.router_predictions import router as predictions_router
from app.api.router_validation import router as validation_router
from app.utils.logging_conf import setup_logging
from app.utils.config import settings

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="MultiTop Demand System API", version="0.3.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, tags=["Health"])
    app.include_router(files_router, prefix="/api", tags=["Files"])
    app.include_router(model_router, prefix="/api", tags=["Model"])
    app.include_router(predictions_router, prefix="/api", tags=["Predictions"])
    app.include_router(validation_router, prefix="/api", tags=["Validation"])

    return app

app = create_app()

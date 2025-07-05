import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import motor.motor_asyncio
import beanie
from api.router import router
from core.config import logger, mongo_config
from core.connection_manager import get_connection_registry
from models.models import StoredVideo

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing application...")
    
    connection_registry = get_connection_registry()
    
    try:
        logger.info("Initializing database...")
        mongodb_client = await connection_registry.mongodb.get_client()
        await beanie.init_beanie(
            database=mongodb_client[mongo_config.db_name],
            document_models=[StoredVideo],
        )
        logger.info("Database initialized successfully.")
        
        logger.info("Warming up connections...")
        health_status = await connection_registry.health_check_all(use_cache=False)
        for service, is_healthy in health_status.items():
            logger.info(f"{service}: {'healthy' if is_healthy else 'unhealthy'}")
        
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        # Don't fail startup, readiness probe will handle it
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down application...")
    try:
        await connection_registry.close_all()
        logger.info("Connection cleanup completed.")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    logger.info("Application shutdown complete.")

class HealthCheckFilter(logging.Filter):
    """Filter out health check requests from logs when debug is disabled."""
    def filter(self, record):
        debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
        if debug_enabled:
            return True
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if "/health/" in message or "GET /health" in message:
                return False
        return True

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Upload Service", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addFilter(HealthCheckFilter())
    
    logger.info("FastAPI application initialized")
    return app

app = create_app()

def run_server() -> None:
    """Run the FastAPI application using Uvicorn."""
    reload = os.environ.get("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8200,
        reload=reload,
        workers=1,
    )
    logger.info("Uvicorn server started on 0.0.0.0:8200")

if __name__ == "__main__":
    run_server()

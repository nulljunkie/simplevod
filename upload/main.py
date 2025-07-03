import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import motor.motor_asyncio
import beanie
from api.router import router
from core.config import logger, mongo_config
from models.models import StoredVideo

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing database...")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_config.url)
    await beanie.init_beanie(
        database=client[mongo_config.db_name],
        document_models=[StoredVideo],
    )
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down application...")

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

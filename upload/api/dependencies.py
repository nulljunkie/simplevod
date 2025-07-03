from typing import Annotated
from fastapi import Depends, HTTPException, status
from core.minio import MinioClient
from core.redis import RedisClient
from core.database import MongoDBClient
from services.storage import StorageService
from services.session import SessionService
from services.video import VideoService
from core.config import logger

async def get_minio_client() -> MinioClient:
    """Provide a MinIO client dependency."""
    client = MinioClient()
    if not client._client:
        logger.error("MinIO client not initialized")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MinIO service unavailable")
    return client

async def get_redis_client() -> RedisClient:
    """Provide a Redis client dependency."""
    client = RedisClient()
    if not client._client:
        logger.error("Redis client not initialized")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis service unavailable")
    return client

async def get_mongo_client() -> MongoDBClient:
    """Provide a MongoDB client dependency."""
    client = MongoDBClient()
    # MongoDB health check - fixed implementation
    if client._db is None:
        logger.error("MongoDB client not initialized")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB service unavailable")
    try:
        # Proper way to test MongoDB connection
        await client._db.command('ping')
    except Exception:
        logger.error("MongoDB client not initialized")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB service unavailable")
    return client

async def get_storage_service(minio: Annotated[MinioClient, Depends(get_minio_client)]) -> StorageService:
    """Provide a storage service dependency."""
    return StorageService(minio)

async def get_session_service(redis: Annotated[RedisClient, Depends(get_redis_client)]) -> SessionService:
    """Provide a session service dependency."""
    return SessionService(redis)

async def get_video_service(
    mongo: Annotated[MongoDBClient, Depends(get_mongo_client)]
) -> VideoService:
    """Provide a video service dependency."""
    return VideoService(mongo)

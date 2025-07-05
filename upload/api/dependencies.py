from typing import Annotated
from fastapi import Depends, HTTPException, status
from core.minio import MinioClient
from core.redis import RedisClient
from core.database import MongoDBClient
from core.client_wrappers import ManagedMinioClient, ManagedRedisClient, ManagedMongoDBClient
from core.connection_manager import get_connection_registry
from services.storage import StorageService
from services.session import SessionService
from services.video import VideoService
from core.config import logger

async def get_minio_client() -> ManagedMinioClient:
    """Provide a managed MinIO client dependency."""
    connection_registry = get_connection_registry()
    
    if not await connection_registry.minio.health_check():
        logger.error("MinIO service is not healthy")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="MinIO service unavailable"
        )
    
    return ManagedMinioClient()

async def get_redis_client() -> ManagedRedisClient:
    """Provide a managed Redis client dependency."""
    connection_registry = get_connection_registry()
    
    if not await connection_registry.redis.health_check():
        logger.error("Redis service is not healthy")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Redis service unavailable"
        )
    
    return ManagedRedisClient()

async def get_mongo_client() -> ManagedMongoDBClient:
    """Provide a managed MongoDB client dependency."""
    connection_registry = get_connection_registry()
    
    if not await connection_registry.mongodb.health_check():
        logger.error("MongoDB service is not healthy")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="MongoDB service unavailable"
        )
    
    return ManagedMongoDBClient()

async def get_storage_service(minio: Annotated[ManagedMinioClient, Depends(get_minio_client)]) -> StorageService:
    """Provide a storage service dependency."""
    return StorageService(minio)

async def get_session_service(redis: Annotated[ManagedRedisClient, Depends(get_redis_client)]) -> SessionService:
    """Provide a session service dependency."""
    return SessionService(redis)

async def get_video_service(
    mongo: Annotated[ManagedMongoDBClient, Depends(get_mongo_client)]
) -> VideoService:
    """Provide a video service dependency."""
    return VideoService(mongo)

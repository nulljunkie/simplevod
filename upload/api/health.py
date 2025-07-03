from typing import Annotated, Any, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from .dependencies import get_redis_client, get_mongo_client, get_minio_client
from core.redis import RedisClient
from core.database import MongoDBClient
from core.minio import MinioClient
from core.config import logger

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/liveness")
async def liveness_probe() -> Dict[str, str]:
    """Check if the application is running."""
    return {"status": "ok"}

@router.get("/readiness")
async def readiness_probe(
    redis: Annotated[RedisClient, Depends(get_redis_client)],
    mongo: Annotated[MongoDBClient, Depends(get_mongo_client)],
    minio: Annotated[MinioClient, Depends(get_minio_client)],
) -> Dict[str, Any]:
    """Check if all services are ready."""
    services = {
        "minio": "ok" if minio._client else "error",
        "redis": "ok" if await redis.ping() else "error",
        "mongodb": "ok" if await mongo.ping() else "error",
    }
    if all(status == "ok" for status in services.values()):
        return {"status": "ok", "services": services}
    logger.warning(f"Readiness check failed: {services}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="One or more services are unavailable",
        headers={"X-Services-Status": str(services)},
    )

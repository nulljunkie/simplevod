from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from core.connection_manager import get_connection_registry
from core.config import logger

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/liveness")
async def liveness_probe() -> Dict[str, str]:
    """Check if the application is running."""
    return {"status": "ok"}

@router.get("/readiness")
async def readiness_probe() -> Dict[str, Any]:
    """Check if all services are ready using cached health checks."""
    connection_registry = get_connection_registry()
    
    # Use cached health checks for efficiency
    health_status = await connection_registry.health_check_all(use_cache=True)
    
    services = {
        service: "ok" if is_healthy else "error"
        for service, is_healthy in health_status.items()
    }
    
    if all(status == "ok" for status in services.values()):
        return {"status": "ok", "services": services}
    
    logger.warning(f"Readiness check failed: {services}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="One or more services are unavailable",
        headers={"X-Services-Status": str(services)},
    )


@router.get("/readiness/fresh")
async def readiness_probe_fresh() -> Dict[str, Any]:
    """Check if all services are ready with fresh health checks (bypasses cache)."""
    connection_registry = get_connection_registry()
    
    # Force fresh health checks (useful for debugging)
    health_status = await connection_registry.health_check_all(use_cache=False)
    
    services = {
        service: "ok" if is_healthy else "error"
        for service, is_healthy in health_status.items()
    }
    
    if all(status == "ok" for status in services.values()):
        return {"status": "ok", "services": services}
    
    logger.warning(f"Fresh readiness check failed: {services}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="One or more services are unavailable",
        headers={"X-Services-Status": str(services)},
    )

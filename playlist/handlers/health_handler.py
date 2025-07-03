import logging
from typing import Optional
from aiohttp import web
from aiohttp.web_runner import AppRunner
from models import HealthStatus
from services.health import HealthService
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)

class HealthHandler:
    def __init__(self, health_service: HealthService) -> None:
        self.health_service = health_service
        
    async def handle_health_check(self, request: web.Request) -> web.Response:
        """
        Handles comprehensive health check requests for all service dependencies.
        Performs full health validation including Redis, MinIO, and RabbitMQ connectivity.
        Returns JSON response with component-level health details and appropriate HTTP status.
        """
        try:
            health_response = await self.health_service.check_full_health()
            status_code = self._determine_status_code(health_response.status)
            
            return web.json_response(
                health_response.model_dump(mode='json'),
                status=status_code
            )
        except Exception as e:
            logger.error(f'Health check failed: {e}')
            return web.json_response(
                {'status': 'unhealthy', 'error': str(e)},
                status=503
            )
    
    async def handle_readiness_check(self, request: web.Request) -> web.Response:
        """
        Handles Kubernetes readiness probe requests.
        Performs same comprehensive health check as main health endpoint.
        Used by Kubernetes to determine if pod is ready to receive traffic.
        """
        return await self.handle_health_check(request)
    
    async def handle_liveness_check(self, request: web.Request) -> web.Response:
        """
        Handles Kubernetes liveness probe requests.
        Performs basic application health check without external dependencies.
        Used by Kubernetes to determine if pod should be restarted.
        """
        try:
            health_response = self.health_service.check_liveness()
            
            return web.json_response(
                health_response.model_dump(mode='json'),
                status=200
            )
        except Exception as e:
            logger.error(f'Liveness check failed: {e}')
            return web.json_response(
                {'status': 'unhealthy', 'error': str(e)},
                status=503
            )
    
    def _determine_status_code(self, health_status: HealthStatus) -> int:
        """
        Maps health status to appropriate HTTP status code.
        Returns 200 for healthy services, 503 for unhealthy services.
        """
        return 200 if health_status == HealthStatus.HEALTHY else 503

def create_health_app(redis_client: RedisClient, minio_client: MinioClient, rabbitmq_client: RabbitMQClient) -> web.Application:
    """
    Creates aiohttp application with health check endpoints.
    Sets up routes for health, readiness, and liveness probes.
    """
    health_service = HealthService(redis_client, minio_client, rabbitmq_client)
    health_handler = HealthHandler(health_service)
    
    app = web.Application()
    app.router.add_get('/health', health_handler.handle_health_check)
    app.router.add_get('/health/ready', health_handler.handle_readiness_check)
    app.router.add_get('/health/live', health_handler.handle_liveness_check)
    
    return app

async def start_health_server(app: web.Application, port: int) -> AppRunner:
    """
    Starts HTTP server for health check endpoints.
    Returns runner for graceful shutdown management.
    """
    runner = AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f'Health server started on port {port}')
    return runner

async def stop_health_server(runner: Optional[AppRunner]) -> None:
    """
    Gracefully stops health server and cleans up resources.
    """
    if runner:
        await runner.cleanup()
        logger.info('Health server stopped')

def determine_status_code(health_status: HealthStatus) -> int:
    """
    Helper function for tests - maps health status to HTTP status code.
    """
    return 200 if health_status == HealthStatus.HEALTHY else 503
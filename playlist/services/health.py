import time
import logging
from typing import Dict
from models import HealthStatus, ComponentHealth, HealthResponse
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)

class HealthService:
    def __init__(self, redis_client: RedisClient, minio_client: MinioClient, rabbitmq_client: RabbitMQClient) -> None:
        self.redis_client = redis_client
        self.minio_client = minio_client
        self.rabbitmq_client = rabbitmq_client
        
    async def check_full_health(self) -> HealthResponse:
        """
        Performs comprehensive health check of all service dependencies.
        Tests connectivity and responsiveness of Redis, MinIO, and RabbitMQ.
        Returns aggregated health status with component-level details and timestamp.
        """
        timestamp = time.time()
        components = {}
        
        components['redis'] = await self._check_redis_health()
        components['minio'] = await self._check_minio_health()
        components['rabbitmq'] = await self._check_rabbitmq_health()
        
        overall_status = self._determine_overall_status(components)
        
        return HealthResponse(
            status=overall_status,
            components=components,
            timestamp=timestamp
        )
    
    async def _check_redis_health(self) -> ComponentHealth:
        """
        Performs Redis health check by testing connection and responsiveness.
        Attempts to ping Redis server and handles potential connection issues.
        Returns component health with appropriate status and diagnostic message.
        """
        try:
            is_healthy = await self.redis_client.check_health()
            
            if is_healthy:
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message='Redis connection successful',
                    last_checked=time.time()
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    message='Redis connection failed',
                    last_checked=time.time()
                )
                
        except Exception as e:
            logger.error(f'Redis health check failed: {e}')
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                message=f'Redis error: {str(e)}',
                last_checked=time.time()
            )
    
    async def _check_minio_health(self) -> ComponentHealth:
        """
        Performs MinIO health check by testing object storage connectivity.
        Attempts to list buckets to verify MinIO service accessibility.
        Returns component health with connection status and diagnostic information.
        """
        try:
            is_healthy = await self.minio_client.check_health()
            
            if is_healthy:
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message='MinIO connection successful',
                    last_checked=time.time()
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    message='MinIO connection failed',
                    last_checked=time.time()
                )
                
        except Exception as e:
            logger.error(f'MinIO health check failed: {e}')
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                message=f'MinIO error: {str(e)}',
                last_checked=time.time()
            )
    
    async def _check_rabbitmq_health(self) -> ComponentHealth:
        """
        Performs RabbitMQ health check by verifying connection status.
        Checks if RabbitMQ connection is established and not closed.
        Returns component health with connection state and diagnostic message.
        """
        try:
            is_healthy = self.rabbitmq_client.check_health()
            
            if is_healthy:
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message='RabbitMQ connection active',
                    last_checked=time.time()
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    message='RabbitMQ connection closed',
                    last_checked=time.time()
                )
                
        except Exception as e:
            logger.error(f'RabbitMQ health check failed: {e}')
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                message=f'RabbitMQ error: {str(e)}',
                last_checked=time.time()
            )
    
    def _determine_overall_status(self, components: Dict[str, ComponentHealth]) -> HealthStatus:
        """
        Determines overall service health based on individual component status.
        Returns HEALTHY only if all components are healthy, otherwise UNHEALTHY.
        """
        return (HealthStatus.HEALTHY 
                if all(component.status == HealthStatus.HEALTHY for component in components.values())
                else HealthStatus.UNHEALTHY)
    
    def check_liveness(self) -> HealthResponse:
        """
        Performs basic liveness check indicating application is running.
        Returns healthy status for Kubernetes liveness probe without external dependencies.
        """
        return HealthResponse(
            status=HealthStatus.HEALTHY,
            components={
                'application': ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message='Application is running',
                    last_checked=time.time()
                )
            },
            timestamp=time.time()
        )
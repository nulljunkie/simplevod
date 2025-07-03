import unittest
from unittest.mock import AsyncMock, Mock
from services.health import HealthService
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient
from models import HealthStatus

class TestHealthService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.redis_client = Mock(spec=RedisClient)
        self.minio_client = Mock(spec=MinioClient)
        self.rabbitmq_client = Mock(spec=RabbitMQClient)
        self.health_service = HealthService(
            self.redis_client,
            self.minio_client,
            self.rabbitmq_client
        )
    
    async def test_all_healthy(self):
        self.redis_client.check_health.return_value = True
        self.minio_client.check_health.return_value = True
        self.rabbitmq_client.check_health.return_value = True
        
        result = await self.health_service.check_full_health()
        
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertIn('redis', result.components)
        self.assertIn('minio', result.components)
        self.assertIn('rabbitmq', result.components)
        self.assertEqual(result.components['redis'].status, HealthStatus.HEALTHY)
        self.assertEqual(result.components['minio'].status, HealthStatus.HEALTHY)
        self.assertEqual(result.components['rabbitmq'].status, HealthStatus.HEALTHY)
    
    async def test_redis_unhealthy(self):
        self.redis_client.check_health.return_value = False
        self.minio_client.check_health.return_value = True
        self.rabbitmq_client.check_health.return_value = True
        
        result = await self.health_service.check_full_health()
        
        self.assertEqual(result.status, HealthStatus.UNHEALTHY)
        self.assertEqual(result.components['redis'].status, HealthStatus.UNHEALTHY)
        self.assertEqual(result.components['minio'].status, HealthStatus.HEALTHY)
        self.assertEqual(result.components['rabbitmq'].status, HealthStatus.HEALTHY)
    
    def test_liveness_always_healthy(self):
        result = self.health_service.check_liveness()
        
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertIn('application', result.components)
        self.assertEqual(result.components['application'].status, HealthStatus.HEALTHY)

if __name__ == '__main__':
    unittest.main()
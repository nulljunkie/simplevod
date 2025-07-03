import unittest
from unittest.mock import AsyncMock, Mock, patch
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient

class TestRedisClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config = {'host': 'localhost', 'port': 6379, 'db': 0, 'password': 'secret'}
        self.redis_client = RedisClient(config)
    
    def test_build_redis_url_with_password(self):
        url = self.redis_client._build_redis_url()
        self.assertEqual(url, 'redis://:secret@localhost:6379/0')
    
    def test_build_redis_url_without_password(self):
        config = {'host': 'localhost', 'port': 6379, 'db': 0, 'password': None}
        redis_client = RedisClient(config)
        url = redis_client._build_redis_url()
        self.assertEqual(url, 'redis://localhost:6379/0')
    
    async def test_check_health_no_client(self):
        result = await self.redis_client.check_health()
        self.assertFalse(result)

class TestMinioClient(unittest.TestCase):
    def setUp(self):
        config = {
            'endpoint': 'localhost:9000',
            'access_key': 'test',
            'secret_key': 'test',
            'use_ssl': False,
            'bucket': 'test-bucket'
        }
        self.minio_client = MinioClient(config)
    
    async def test_check_health_no_client(self):
        result = await self.minio_client.check_health()
        self.assertFalse(result)

class TestRabbitMQClient(unittest.TestCase):
    def setUp(self):
        config = {
            'host': 'localhost',
            'port': 5672,
            'user': 'test',
            'password': 'test',
            'vhost': '/',
            'exchange': 'test',
            'queue': 'test',
            'routing_key': 'test'
        }
        self.rabbitmq_client = RabbitMQClient(config)
    
    def test_check_health_no_connection(self):
        result = self.rabbitmq_client.check_health()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
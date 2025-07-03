import unittest
import json
from unittest.mock import AsyncMock, Mock, patch
from aiohttp.test_utils import AioHTTPTestCase
from handlers.health_handler import create_health_app, determine_status_code
from services.health import HealthService
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient
from models import HealthStatus, PlaylistMessage

class TestPlaylistMessage(unittest.TestCase):
    def test_parse_message_data(self):
        data = {'video_id': 'test', 'resolution': '720'}
        playlist_msg = PlaylistMessage(**data)
        
        self.assertEqual(playlist_msg.video_id, 'test')
        self.assertEqual(playlist_msg.resolution, '720')

class TestHealthHandler(AioHTTPTestCase):
    async def get_application(self):
        redis_client = Mock(spec=RedisClient)
        minio_client = Mock(spec=MinioClient)
        rabbitmq_client = Mock(spec=RabbitMQClient)
        return create_health_app(redis_client, minio_client, rabbitmq_client)
    
    async def test_health_endpoint_exists(self):
        resp = await self.client.request('GET', '/health')
        self.assertIn(resp.status, [200, 503])
    
    async def test_readiness_endpoint_exists(self):
        resp = await self.client.request('GET', '/health/ready')
        self.assertIn(resp.status, [200, 503])
    
    async def test_liveness_endpoint_exists(self):
        resp = await self.client.request('GET', '/health/live')
        self.assertEqual(resp.status, 200)

class TestHealthUtils(unittest.TestCase):
    def test_status_code_healthy(self):
        code = determine_status_code(HealthStatus.HEALTHY)
        self.assertEqual(code, 200)
    
    def test_status_code_unhealthy(self):
        code = determine_status_code(HealthStatus.UNHEALTHY)
        self.assertEqual(code, 503)

if __name__ == '__main__':
    unittest.main()
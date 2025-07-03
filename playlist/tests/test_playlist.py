import unittest
from unittest.mock import AsyncMock, Mock
from services.playlist import PlaylistService
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient
from models import Segment, VideoMetadata

class TestPlaylistService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.redis_client = Mock(spec=RedisClient)
        self.minio_client = Mock(spec=MinioClient)
        self.rabbitmq_client = Mock(spec=RabbitMQClient)
        self.playlist_service = PlaylistService(
            self.redis_client,
            self.minio_client,
            self.rabbitmq_client
        )
    
    def test_generate_media_playlist_content(self):
        segments = [
            Segment(path='segment_0000.ts', duration=10.0),
            Segment(path='segment_0001.ts', duration=9.5)
        ]
        
        result = self.playlist_service._generate_media_playlist_content(segments)
        
        self.assertIn('#EXTM3U', result.content)
        self.assertIn('#EXT-X-TARGETDURATION:10', result.content)
        self.assertIn('segment_0000.ts', result.content)
        self.assertIn('segment_0001.ts', result.content)
        self.assertIn('#EXT-X-ENDLIST', result.content)
        self.assertEqual(result.target_duration, 10)
    
    def test_generate_master_playlist_content(self):
        resolution_bandwidths = {'720': '1500000', '1080': '3000000'}
        
        content = self.playlist_service._generate_master_playlist_content(resolution_bandwidths)
        
        self.assertIn('#EXTM3U', content)
        self.assertIn('BANDWIDTH=1500000', content)
        self.assertIn('BANDWIDTH=3000000', content)
        self.assertIn('720/playlist.m3u8', content)
        self.assertIn('1080/playlist.m3u8', content)
    
    def test_master_playlist_resolution_sorting(self):
        resolution_bandwidths = {'1080': '3000000', '480': '800000', '720': '1500000'}
        
        content = self.playlist_service._generate_master_playlist_content(resolution_bandwidths)
        lines = content.split('\n')
        
        bandwidth_480_index = next(i for i, line in enumerate(lines) if 'BANDWIDTH=800000' in line)
        bandwidth_720_index = next(i for i, line in enumerate(lines) if 'BANDWIDTH=1500000' in line)
        bandwidth_1080_index = next(i for i, line in enumerate(lines) if 'BANDWIDTH=3000000' in line)
        
        self.assertLess(bandwidth_480_index, bandwidth_720_index)
        self.assertLess(bandwidth_720_index, bandwidth_1080_index)
    
    async def test_process_playlist_request_no_segments(self):
        self.redis_client.get_video_segments.return_value = None
        
        result = await self.playlist_service.process_playlist_request('video123', '720')
        
        self.assertFalse(result)
        self.redis_client.get_video_segments.assert_called_once_with('video123', '720')

if __name__ == '__main__':
    unittest.main()
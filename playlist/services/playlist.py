import math
import logging
from typing import List, Dict, Tuple, Optional
from models import Segment, PlaylistContent, VideoMetadata
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)

class PlaylistService:
    def __init__(self, redis_client: RedisClient, minio_client: MinioClient, rabbitmq_client: RabbitMQClient) -> None:
        self.redis_client = redis_client
        self.minio_client = minio_client
        self.rabbitmq_client = rabbitmq_client
        
    async def process_playlist_request(self, video_id: str, resolution: str) -> bool:
        """
        Processes playlist generation request for specific video and resolution.
        Retrieves segments from Redis, generates media playlist, uploads to MinIO,
        and triggers master playlist creation if all resolutions are complete.
        Returns True if processing succeeds, False otherwise.
        """
        try:
            segments = await self.redis_client.get_video_segments(video_id, resolution)
            if not segments:
                logger.error(f'No segments found for {video_id}/{resolution}')
                return False
            
            playlist_content = self._generate_media_playlist_content(segments)
            
            success = await self.minio_client.upload_media_playlist(
                video_id, resolution, playlist_content.content
            )
            
            if not success:
                logger.error(f'Failed to upload media playlist for {video_id}/{resolution}')
                return False
            
            await self.redis_client.mark_playlist_completed(video_id, resolution)
            
            if await self._should_create_master_playlist(video_id):
                await self._create_master_playlist(video_id)
            
            logger.info(f'Successfully processed playlist request for {video_id}/{resolution}')
            return True
            
        except Exception as e:
            logger.error(f'Error processing playlist request for {video_id}/{resolution}: {e}')
            return False
    
    def _generate_media_playlist_content(self, segments: List[Segment]) -> PlaylistContent:
        """
        Generates HLS media playlist content from video segments.
        Creates M3U8 format with proper headers, segment entries, and footer.
        Calculates target duration from maximum segment duration.
        """
        max_duration = max(segment.duration for segment in segments)
        target_duration = math.ceil(max_duration)
        
        playlist_lines = [
            '#EXTM3U',
            '#EXT-X-VERSION:3',
            f'#EXT-X-TARGETDURATION:{target_duration}',
            '#EXT-X-MEDIA-SEQUENCE:0',
            '#EXT-X-PLAYLIST-TYPE:VOD',
            '#EXT-X-INDEPENDENT-SEGMENTS'
        ]
        
        for i, segment in enumerate(segments):
            if i > 0:
                playlist_lines.append('#EXT-X-DISCONTINUITY')
            duration_str = f'{segment.duration:.5f}'.rstrip('0').rstrip('.')
            playlist_lines.extend([
                f'#EXTINF:{duration_str},',
                segment.path
            ])
        
        playlist_lines.append('#EXT-X-ENDLIST')
        content = '\n'.join(playlist_lines) + '\n'
        
        return PlaylistContent(content=content, target_duration=target_duration)
    
    async def _should_create_master_playlist(self, video_id: str) -> bool:
        """
        Determines if master playlist should be created by checking completion status.
        Compares number of completed playlists against expected count from metadata.
        """
        try:
            metadata = await self.redis_client.get_video_metadata(video_id)
            if not metadata:
                return False
            
            completed_count = len(metadata.completed_resolutions)
            return completed_count >= metadata.expected_count and metadata.expected_count > 0
            
        except Exception as e:
            logger.error(f'Error checking master playlist creation condition for {video_id}: {e}')
            return False
    
    async def _create_master_playlist(self, video_id: str) -> bool:
        """
        Creates and uploads master playlist containing all resolution variants.
        Retrieves video metadata, generates master playlist content with bandwidth info,
        uploads to MinIO, and publishes completion notification via RabbitMQ.
        """
        try:
            metadata = await self.redis_client.get_video_metadata(video_id)
            if not metadata:
                logger.error(f'No metadata found for master playlist creation: {video_id}')
                return False
            
            master_content = self._generate_master_playlist_content(metadata.resolution_bandwidths)
            
            success = await self.minio_client.upload_master_playlist(video_id, master_content)
            if not success:
                logger.error(f'Failed to upload master playlist for {video_id}')
                return False
            
            await self.rabbitmq_client.publish_video_completion(video_id)
            logger.info(f'Master playlist created and completion published for {video_id}')
            return True
            
        except Exception as e:
            logger.error(f'Error creating master playlist for {video_id}: {e}')
            return False
    
    def _generate_master_playlist_content(self, resolution_bandwidths: Dict[str, str]) -> str:
        """
        Generates HLS master playlist content from resolution bandwidth mapping.
        Creates M3U8 format with stream information for each resolution variant.
        Sorts resolutions numerically and calculates proper dimensions.
        """
        sorted_resolutions = sorted(resolution_bandwidths.keys(), key=int)
        
        playlist_lines = ['#EXTM3U', '#EXT-X-VERSION:3']
        
        for resolution in sorted_resolutions:
            bandwidth = resolution_bandwidths[resolution]
            height = int(resolution)
            width = int(height * 16 / 9)
            playlist_path = f'{resolution}/playlist.m3u8'
            
            playlist_lines.extend([
                f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={width}x{height}',
                playlist_path
            ])
        
        return '\n'.join(playlist_lines) + '\n'

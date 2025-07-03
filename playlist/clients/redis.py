import json
import logging
from typing import Dict, List, Optional, Any
from redis.asyncio import Redis, from_url
from models import Segment, VideoMetadata

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client: Optional[Redis] = None
        
    async def connect(self) -> Redis:
        """
        Establishes connection to Redis server with proper configuration.
        Builds connection URL with authentication if provided and tests connectivity.
        """
        url = self._build_redis_url()
        self.client = await from_url(url, encoding='utf-8', decode_responses=True)
        
        await self.client.ping()
        logger.info(f"Connected to Redis at {self.config['host']}:{self.config['port']}")
        
        return self.client
    
    def _build_redis_url(self) -> str:
        """
        Constructs Redis connection URL with optional authentication.
        Handles both password-protected and open Redis instances.
        """
        host = self.config['host']
        port = self.config['port']
        db = self.config['db']
        password = self.config.get('password')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    async def get_video_segments(self, video_id: str, resolution: str) -> Optional[List[Segment]]:
        """
        Retrieves and parses video segments from Redis for given video and resolution.
        Handles segment data stored as JSON in hash maps and converts to Segment objects.
        Returns None if no segments found.
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
            
        segments_key = f'transcode:playlists:{video_id}:data:{resolution}'
        playlist_data = await self.client.hgetall(segments_key)
        
        if not playlist_data:
            logger.warning(f"No segments found for {video_id}/{resolution}")
            return None
        
        segments = []
        sorted_data = dict(sorted(playlist_data.items()))
        
        for value in sorted_data.values():
            try:
                chunk_data = json.loads(value)
                segment_infos = chunk_data['segments']
                
                # for segment_value in sorted(segment_infos.values()):
                for segment_value in sorted(segment_infos.values(), key=lambda seg: seg['path']):
                    segment = Segment(
                        path=segment_value['path'], 
                        duration=segment_value['extinf']
                    )
                    segments.append(segment)
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse segment data: {e}")
                continue
        
        return segments if segments else None
    
    async def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Retrieves comprehensive video metadata including resolution bandwidths,
        completed playlists, and expected completion count.
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
            
        metadata_key = f'transcode:playlists:{video_id}:meta'
        completed_key = f'transcode:playlists:{video_id}:completed'
        
        try:
            resolution_bandwidths = await self.client.hgetall(metadata_key)
            completed_resolutions = await self.client.smembers(completed_key)
            expected_count = await self.client.hlen(metadata_key)
            
            if not resolution_bandwidths:
                logger.warning(f"No metadata found for video {video_id}")
                return None
            
            return VideoMetadata(
                resolution_bandwidths=resolution_bandwidths,
                completed_resolutions=list(completed_resolutions),
                expected_count=expected_count
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve video metadata for {video_id}: {e}")
            return None
    
    async def mark_playlist_completed(self, video_id: str, resolution: str) -> bool:
        """
        Marks a specific resolution playlist as completed for a video.
        Updates the completed resolutions set in Redis.
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
            
        completed_key = f'transcode:playlists:{video_id}:completed'
        
        try:
            await self.client.sadd(completed_key, resolution)
            logger.info(f"Marked playlist completed: {video_id}/{resolution}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark playlist completed for {video_id}/{resolution}: {e}")
            return False
    
    async def check_health(self) -> bool:
        """
        Performs health check by pinging Redis server.
        Returns True if Redis is responsive, False otherwise.
        """
        if not self.client:
            return False
            
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """
        Gracefully closes Redis connection and cleans up resources.
        """
        if self.client:
            await self.client.aclose()
            logger.info('Redis connection closed')
            self.client = None

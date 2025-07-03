import logging
from typing import Optional, List

from redis.asyncio import Redis, RedisError

from config import config


class RedisClient:
    def __init__(self) -> None:
        self.client: Optional[Redis] = None
        
        try:
            self.client = Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password,
                db=config.redis_db
            )
            logging.info("Connected to Redis successfully")
            
        except (RedisError, Exception) as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        if self.client is not None:
            await self.client.close()
            logging.info("Redis connection closed")


    async def delete_keys(self, video_id: str) -> bool:
        if self.client is None:
            logging.error("Redis client not initialized")
            return False
            
        try:
            keys = await self.client.keys(f"transcode:*:{video_id}:*")
            
            if not keys:
                logging.warning(f"No Redis keys found for video: {video_id}")
                return True
            
            await self.client.delete(*keys)
            logging.info(f"Deleted {len(keys)} keys for video {video_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete keys: {e}")
            return False

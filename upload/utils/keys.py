from typing import List
from core.redis import RedisClient
from core.config import logger
import string
import random

def generate_unique_key(length=24):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def get_session_meta_key(key: str) -> str:
    return f"upload:session:{key}:meta"

def get_session_parts_key(key: str) -> str:
    return f"upload:session:{key}:parts"

async def delete_redis_keys(redis: RedisClient, keys: List[str]) -> None:
    try:
        deleted_count = await redis.delete(*keys)
        logger.info(f"Cleaned up {deleted_count} Redis keys: {keys}")
    except Exception as e:
        logger.error(f"Failed to delete Redis keys {keys}: {e}")

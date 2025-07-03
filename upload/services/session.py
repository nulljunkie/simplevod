import json
from typing import Dict, List
from fastapi import HTTPException, status
from core.redis import RedisClient
from models.models import SessionData
from utils.keys import get_session_meta_key, get_session_parts_key
from core.config import logger, redis_config

class SessionService:
    """Service for managing upload sessions in Redis with Pydantic validation."""

    def __init__(self, redis: RedisClient):
        self.redis = redis

    async def store_session(self, unique_key: str, session_data: SessionData) -> None:
        """Store session metadata in Redis with Pydantic validation."""
        session_meta_key = get_session_meta_key(unique_key)
        async with await self.redis.pipeline(transaction=True) as pipe:
            await pipe.set(session_meta_key, session_data.model_dump_json())
            await pipe.expire(session_meta_key, redis_config.session_expiry_seconds)
            await pipe.execute()
        logger.debug(f"Stored session metadata for key '{unique_key}'")

    async def validate_session(
        self, key: str, user_id: str | None, expected_status: str | None = None
    ) -> SessionData:
        """Validate and retrieve session data as a Pydantic model."""
        session_meta_key = get_session_meta_key(key)
        session_data_json = await self.redis.get(session_meta_key)
        if not session_data_json:
            logger.error(f"Session not found for key '{key}'")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found or expired")
        try:
            session_data = SessionData.model_validate_json(session_data_json)
            if user_id and session_data.user_id != user_id:
                logger.warning(f"Unauthorized access to session '{key}' by user '{user_id}'")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            if expected_status and session_data.status != expected_status:
                logger.warning(f"Invalid session status for key '{key}': {session_data.status}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Upload session is not {expected_status} (status: {session_data.status})",
                )
            return session_data
        except ValueError as e:
            logger.error(f"Failed to decode session data for key '{key}': {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid session state")

    async def record_part(self, key: str, part_number: int, etag: str) -> None:
        """Record an uploaded part and increment uploaded_parts in Redis."""
        session_parts_key = get_session_parts_key(key)
        session_meta_key = get_session_meta_key(key)
        session_data = await self.validate_session(key, user_id=None)  # No user_id check here
        session_data.uploaded_parts += 1
        async with await self.redis.pipeline(transaction=True) as pipe:
            await pipe.hset(session_parts_key, str(part_number), etag)
            await pipe.set(session_meta_key, session_data.model_dump_json())
            await pipe.expire(session_meta_key, redis_config.session_expiry_seconds)
            await pipe.expire(session_parts_key, redis_config.session_expiry_seconds)
            await pipe.execute()
        logger.debug(f"Recorded part {part_number} for key '{key}', total parts: {session_data.uploaded_parts}")

    async def list_parts(self, key: str) -> List[Dict]:
        """List all recorded parts for an upload."""
        session_parts_key = get_session_parts_key(key)
        parts_dict = await self.redis.hgetall(session_parts_key)
        return [{"part_number": int(pn), "etag": etag} for pn, etag in parts_dict.items()]

    async def extend_session_expiry(self, key: str) -> None:
        """Extend the expiry of session keys."""
        session_meta_key = get_session_meta_key(key)
        session_parts_key = get_session_parts_key(key)
        async with await self.redis.pipeline(transaction=True) as pipe:
            await pipe.expire(session_meta_key, redis_config.session_expiry_seconds)
            await pipe.expire(session_parts_key, redis_config.session_expiry_seconds)
            await pipe.execute()
        logger.debug(f"Extended session expiry for key '{key}'")

    async def cleanup_session(self, key: str) -> None:
        """Delete session keys from Redis."""
        session_meta_key = get_session_meta_key(key)
        session_parts_key = get_session_parts_key(key)
        await self.redis.delete(session_meta_key, session_parts_key)
        logger.debug(f"Cleaned up session keys for key '{key}'")

from typing import Any, Dict, Optional
from redis.asyncio import Redis
from .config import redis_config, logger

class RedisClient:
    """A client for interacting with Redis using the async driver."""

    def __init__(self) -> None:
        """
        Initialize Redis client with configured settings.

        Raises:
            RuntimeError: If connection to Redis fails.
        """
        self._client: Optional[Redis] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Set up Redis client with connection parameters."""
        try:
            self._client = Redis(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password,
                db=redis_config.db,
                decode_responses=True,
            )
            logger.info(f"Connected to Redis at {redis_config.host}:{redis_config.port}/db={redis_config.db}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise RuntimeError(f"Redis connection failed: {str(e)}")

    async def ping(self) -> bool:
        """Check if Redis is responsive.

        Returns:
            bool: True if ping succeeds, False otherwise.
        """
        try:
            await self._client.ping()
            logger.debug("Redis ping successful")
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a value by key.

        Args:
            key: Key to retrieve.

        Returns:
            Optional[str]: Value associated with the key, or None if not found.

        Raises:
            RuntimeError: If retrieval fails.
        """
        try:
            value = await self._client.get(key)
            logger.debug(f"Retrieved key '{key}': {value}")
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve key '{key}': {str(e)}")
            raise RuntimeError(f"Key retrieval failed: {str(e)}")

    async def set(self, key: str, value: str, expire: int = 0) -> bool:
        """Set a key-value pair with optional expiry.

        Args:
            key: Key to set.
            value: Value to associate with the key.
            expire: Expiry time in seconds (0 for no expiry).

        Returns:
            bool: True if set operation succeeds.

        Raises:
            RuntimeError: If set operation fails.
        """
        try:
            result = await self._client.set(key, value, ex=expire)
            logger.debug(f"Set key '{key}' to '{value}'{' with expiry ' + str(expire) + 's' if expire else ''}")
            return result
        except Exception as e:
            logger.error(f"Failed to set key '{key}': {str(e)}")
            raise RuntimeError(f"Key set operation failed: {str(e)}")

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set a field in a hash.

        Args:
            name: Name of the hash.
            key: Field key to set.
            value: Value to associate with the field.

        Returns:
            int: Number of fields set.

        Raises:
            RuntimeError: If hash set operation fails.
        """
        try:
            result = await self._client.hset(name, key, value)
            logger.debug(f"HSET '{name}' key '{key}' to '{value}'")
            return result
        except Exception as e:
            logger.error(f"Failed to HSET '{name}' key '{key}': {str(e)}")
            raise RuntimeError(f"Hash set operation failed: {str(e)}")

    async def hgetall(self, name: str) -> Dict[str, str]:
        """Retrieve all fields and values in a hash.

        Args:
            name: Name of the hash.

        Returns:
            Dict[str, str]: Dictionary of field-value pairs.

        Raises:
            RuntimeError: If hash retrieval fails.
        """
        try:
            result = await self._client.hgetall(name)
            logger.debug(f"HGETALL '{name}' returned {len(result)} items")
            return result
        except Exception as e:
            logger.error(f"Failed to HGETALL '{name}': {str(e)}")
            raise RuntimeError(f"Hash retrieval failed: {str(e)}")

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys.

        Args:
            *keys: Keys to delete.

        Returns:
            int: Number of keys deleted.

        Raises:
            RuntimeError: If deletion fails.
        """
        try:
            result = await self._client.delete(*keys)
            logger.debug(f"Deleted {result} keys: {keys}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete keys {keys}: {str(e)}")
            raise RuntimeError(f"Key deletion failed: {str(e)}")

    async def expire(self, key: str, seconds: int) -> bool:
        """Set an expiry time for a key.

        Args:
            key: Key to set expiry for.
            seconds: Expiry time in seconds.

        Returns:
            bool: True if expiry was set, False if key doesn’t exist.

        Raises:
            RuntimeError: If expiry operation fails.
        """
        try:
            result = await self._client.expire(key, seconds)
            logger.debug(f"Set expiry on '{key}' to {seconds}s")
            return result
        except Exception as e:
            logger.error(f"Failed to set expiry on '{key}': {str(e)}")
            raise RuntimeError(f"Key expiry operation failed: {str(e)}")

    async def pipeline(self, transaction: bool = True) -> Any:
        """Create a Redis pipeline for batch operations.

        Args:
            transaction: Whether to execute commands as a transaction (default: True).

        Returns:
            Any: Redis pipeline object.

        Raises:
            RuntimeError: If pipeline creation fails.
        """
        try:
            return self._client.pipeline(transaction=transaction)
        except Exception as e:
            logger.error(f"Failed to create pipeline: {str(e)}")
            raise RuntimeError(f"Pipeline creation failed: {str(e)}")

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            try:
                await self._client.close()
                logger.info("Closed Redis connection")
            except Exception as e:
                logger.error(f"Failed to close Redis connection: {str(e)}")
                raise RuntimeError(f"Redis connection closure failed: {str(e)}")

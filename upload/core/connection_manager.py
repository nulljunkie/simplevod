"""
Connection Manager for Upload Service

Provides singleton connection managers for MinIO, Redis, and MongoDB
with connection pooling, health monitoring, and retry logic.
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import motor.motor_asyncio
import redis.asyncio as redis
from minio import Minio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.config import get_settings


logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Custom exception for connection errors"""
    pass


class BaseConnectionManager:
    """Base class for connection managers"""
    
    def __init__(self):
        self._client = None
        self._lock = threading.Lock()
        self._last_health_check = 0
        self._settings = get_settings()
        self._health_cache_duration = self._settings.health_check.cache_duration_seconds
        self._is_healthy = False
    
    async def get_client(self):
        """Get the client instance, creating it if necessary"""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = await self._create_client()
        return self._client
    
    async def _create_client(self):
        """Create a new client instance - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def health_check(self, use_cache: bool = True) -> bool:
        """Check if the service is healthy"""
        now = time.time()
        
        if use_cache and (now - self._last_health_check) < self._health_cache_duration:
            return self._is_healthy
        
        try:
            self._is_healthy = await self._perform_health_check()
            self._last_health_check = now
            logger.debug(f"{self.__class__.__name__} health check: {'healthy' if self._is_healthy else 'unhealthy'}")
        except Exception as e:
            logger.warning(f"{self.__class__.__name__} health check failed: {e}")
            self._is_healthy = False
        
        return self._is_healthy
    
    async def _perform_health_check(self) -> bool:
        """Perform actual health check - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def refresh_connection(self):
        """Force refresh the connection"""
        logger.info(f"Refreshing {self.__class__.__name__} connection")
        with self._lock:
            if self._client:
                await self._cleanup_client()
            self._client = None
        # Reset health cache
        self._last_health_check = 0
        self._is_healthy = False
    
    async def _cleanup_client(self):
        """Clean up the current client - to be implemented by subclasses"""
        pass
    
    async def close(self):
        """Close the connection manager"""
        with self._lock:
            if self._client:
                await self._cleanup_client()
            self._client = None


class MinIOConnectionManager(BaseConnectionManager):
    """Connection manager for MinIO"""
    
    async def _create_client(self) -> Minio:
        """Create a new MinIO client"""
        settings = get_settings()
        logger.info(f"Creating MinIO client for {settings.minio.endpoint}")
        
        return Minio(
            endpoint=settings.minio.endpoint,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            secure=settings.minio.use_ssl
        )
    
    async def _perform_health_check(self) -> bool:
        """Check MinIO health by listing buckets"""
        settings = get_settings()
        
        @retry(
            stop=stop_after_attempt(settings.retry.max_attempts),
            wait=wait_exponential(
                multiplier=settings.retry.exponential_multiplier,
                min=settings.retry.min_wait_seconds,
                max=settings.retry.max_wait_seconds
            ),
            retry=retry_if_exception_type((ConnectionError, Exception))
        )
        async def _retry_health_check():
            try:
                client = await self.get_client()
                # Use a thread pool to run the synchronous MinIO operation
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: list(client.list_buckets()))
                return True
            except Exception as e:
                logger.error(f"MinIO health check failed: {e}")
                raise ConnectionError(f"MinIO health check failed: {e}")
        
        return await _retry_health_check()
    
    async def _cleanup_client(self):
        """MinIO client doesn't need explicit cleanup"""
        pass


class RedisConnectionManager(BaseConnectionManager):
    """Connection manager for Redis"""
    
    async def _create_client(self) -> redis.Redis:
        """Create a new Redis client with connection pool"""
        settings = get_settings()
        logger.info(f"Creating Redis client for {settings.redis.host}:{settings.redis.port}")
        
        connection_pool = redis.ConnectionPool(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password,
            db=settings.redis.db,
            max_connections=settings.redis.max_connections,
            retry_on_timeout=True,
            health_check_interval=settings.redis.health_check_interval
        )
        
        return redis.Redis(connection_pool=connection_pool)
    
    async def _perform_health_check(self) -> bool:
        """Check Redis health with ping"""
        settings = get_settings()
        
        @retry(
            stop=stop_after_attempt(settings.retry.max_attempts),
            wait=wait_exponential(
                multiplier=settings.retry.exponential_multiplier,
                min=settings.retry.min_wait_seconds,
                max=settings.retry.max_wait_seconds
            ),
            retry=retry_if_exception_type((ConnectionError, redis.RedisError))
        )
        async def _retry_health_check():
            try:
                client = await self.get_client()
                await client.ping()
                return True
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                raise ConnectionError(f"Redis health check failed: {e}")
        
        return await _retry_health_check()
    
    async def _cleanup_client(self):
        """Close Redis connection pool"""
        if self._client:
            await self._client.close()


class MongoDBConnectionManager(BaseConnectionManager):
    """Connection manager for MongoDB"""
    
    async def _create_client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """Create a new MongoDB client"""
        settings = get_settings()
        logger.info(f"Creating MongoDB client for {settings.mongodb.url}")
        
        return motor.motor_asyncio.AsyncIOMotorClient(
            settings.mongodb.url,
            maxPoolSize=settings.mongodb.max_pool_size,
            minPoolSize=settings.mongodb.min_pool_size,
            maxIdleTimeMS=settings.mongodb.max_idle_time_ms,
            serverSelectionTimeoutMS=settings.mongodb.server_selection_timeout_ms
        )
    
    async def _perform_health_check(self) -> bool:
        """Check MongoDB health with ping"""
        settings = get_settings()
        
        @retry(
            stop=stop_after_attempt(settings.retry.max_attempts),
            wait=wait_exponential(
                multiplier=settings.retry.exponential_multiplier,
                min=settings.retry.min_wait_seconds,
                max=settings.retry.max_wait_seconds
            ),
            retry=retry_if_exception_type((ConnectionError, Exception))
        )
        async def _retry_health_check():
            try:
                client = await self.get_client()
                await client.admin.command('ping')
                return True
            except Exception as e:
                logger.error(f"MongoDB health check failed: {e}")
                raise ConnectionError(f"MongoDB health check failed: {e}")
        
        return await _retry_health_check()
    
    async def _cleanup_client(self):
        """Close MongoDB client"""
        if self._client:
            self._client.close()


class ConnectionManagerRegistry:
    """Registry for all connection managers"""
    
    def __init__(self):
        self.minio = MinIOConnectionManager()
        self.redis = RedisConnectionManager()
        self.mongodb = MongoDBConnectionManager()
    
    async def health_check_all(self, use_cache: bool = True) -> Dict[str, bool]:
        """Check health of all services"""
        health_results = {}
        
        # Run health checks concurrently
        tasks = [
            ("minio", self.minio.health_check(use_cache)),
            ("redis", self.redis.health_check(use_cache)),
            ("mongodb", self.mongodb.health_check(use_cache))
        ]
        
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        for (service_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Health check for {service_name} failed with exception: {result}")
                health_results[service_name] = False
            else:
                health_results[service_name] = result
        
        return health_results
    
    async def close_all(self):
        """Close all connection managers"""
        await asyncio.gather(
            self.minio.close(),
            self.redis.close(),
            self.mongodb.close(),
            return_exceptions=True
        )


# Global connection manager registry
_connection_registry: Optional[ConnectionManagerRegistry] = None


def get_connection_registry() -> ConnectionManagerRegistry:
    """Get the global connection manager registry"""
    global _connection_registry
    if _connection_registry is None:
        _connection_registry = ConnectionManagerRegistry()
    return _connection_registry


@asynccontextmanager
async def get_minio_client():
    """Context manager for MinIO client with retry logic"""
    registry = get_connection_registry()
    settings = get_settings()
    
    @retry(
        stop=stop_after_attempt(settings.retry.max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry.exponential_multiplier,
            min=settings.retry.min_wait_seconds,
            max=settings.retry.max_wait_seconds
        ),
        retry=retry_if_exception_type(ConnectionError)
    )
    async def _get_client():
        if not await registry.minio.health_check():
            await registry.minio.refresh_connection()
        return await registry.minio.get_client()
    
    client = await _get_client()
    try:
        yield client
    except Exception as e:
        if "connection" in str(e).lower():
            await registry.minio.refresh_connection()
        raise


@asynccontextmanager
async def get_redis_client():
    """Context manager for Redis client with retry logic"""
    registry = get_connection_registry()
    settings = get_settings()
    
    @retry(
        stop=stop_after_attempt(settings.retry.max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry.exponential_multiplier,
            min=settings.retry.min_wait_seconds,
            max=settings.retry.max_wait_seconds
        ),
        retry=retry_if_exception_type((ConnectionError, redis.RedisError))
    )
    async def _get_client():
        if not await registry.redis.health_check():
            await registry.redis.refresh_connection()
        return await registry.redis.get_client()
    
    client = await _get_client()
    try:
        yield client
    except redis.RedisError as e:
        if "connection" in str(e).lower():
            await registry.redis.refresh_connection()
        raise


@asynccontextmanager
async def get_mongodb_client():
    """Context manager for MongoDB client with retry logic"""
    registry = get_connection_registry()
    settings = get_settings()
    
    @retry(
        stop=stop_after_attempt(settings.retry.max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry.exponential_multiplier,
            min=settings.retry.min_wait_seconds,
            max=settings.retry.max_wait_seconds
        ),
        retry=retry_if_exception_type(ConnectionError)
    )
    async def _get_client():
        if not await registry.mongodb.health_check():
            await registry.mongodb.refresh_connection()
        return await registry.mongodb.get_client()
    
    client = await _get_client()
    try:
        yield client
    except Exception as e:
        if "connection" in str(e).lower() or "network" in str(e).lower():
            await registry.mongodb.refresh_connection()
        raise
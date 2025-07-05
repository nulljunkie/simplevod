"""
Client Wrappers for Connection Manager Integration

These wrappers provide compatibility with existing service interfaces
while using the new connection managers for improved efficiency.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

from minio import Minio
from minio.datatypes import Object
from minio.error import S3Error
import redis.asyncio as redis
import motor.motor_asyncio

from core.connection_manager import (
    get_connection_registry,
    get_minio_client as get_minio_context,
    get_redis_client as get_redis_context,
    get_mongodb_client as get_mongodb_context
)
from core.config import minio_config, redis_config, mongo_config, logger


class ManagedMinioClient:
    """MinIO client wrapper using connection manager"""
    
    def __init__(self):
        self._connection_registry = get_connection_registry()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="minio-wrapper")
    
    @property
    def _client(self) -> Optional[Minio]:
        """Compatibility property for existing code"""
        try:
            # Use asyncio to run the async method
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                # Return None for now - the actual client will be retrieved via context manager
                return None
            else:
                return loop.run_until_complete(self._connection_registry.minio.get_client())
        except Exception:
            return None
    
    async def get_client(self) -> Minio:
        """Get the MinIO client asynchronously"""
        return await self._connection_registry.minio.get_client()
    
    def _run_async_in_thread(self, coro):
        """Run an async coroutine in a thread pool to avoid event loop conflicts."""
        def _run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        
        # Check if we're in an async context
        try:
            current_loop = asyncio.get_running_loop()
            # We're in an async context, run in thread pool
            future = self._executor.submit(_run_in_thread)
            return future.result()
        except RuntimeError:
            # No running event loop, we can run directly
            return asyncio.run(coro)
    
    def create_multipart_upload(self, object_name: str, headers: Dict[str, str]) -> str:
        """Initiate a multipart upload for an object."""
        async def _async_create():
            async with get_minio_context() as client:
                return client._create_multipart_upload(minio_config.bucket, object_name, headers=headers)
        
        return self._run_async_in_thread(_async_create())
    
    def complete_multipart_upload(
        self,
        object_name: str,
        upload_id: str,
        parts: List[Dict[str, Any]]
    ) -> None:
        """Complete a multipart upload."""
        async def _async_complete():
            async with get_minio_context() as client:
                return client._complete_multipart_upload(
                    minio_config.bucket, object_name, upload_id, parts
                )
        
        return self._run_async_in_thread(_async_complete())
    
    def abort_multipart_upload(self, object_name: str, upload_id: str) -> None:
        """Abort a multipart upload."""
        async def _async_abort():
            async with get_minio_context() as client:
                return client._abort_multipart_upload(minio_config.bucket, object_name, upload_id)
        
        return self._run_async_in_thread(_async_abort())
    
    def list_objects(self, prefix: str = "", recursive: bool = False) -> List[Object]:
        """List objects in the bucket."""
        async def _async_list():
            async with get_minio_context() as client:
                return list(client.list_objects(minio_config.bucket, prefix, recursive))
        
        return self._run_async_in_thread(_async_list())
    
    def remove_object(self, object_name: str) -> None:
        """Remove an object from the bucket."""
        async def _async_remove():
            async with get_minio_context() as client:
                return client.remove_object(minio_config.bucket, object_name)
        
        return self._run_async_in_thread(_async_remove())
    
    def get_presigned_url(
        self,
        method: str,
        object_name: str,
        expires: timedelta,
        part_number: Optional[int] = None,
        upload_id: Optional[str] = None,
        bucket: Optional[str] = None,
    ) -> str:
        """Generate a presigned URL for an object operation."""
        async def _async_presigned():
            async with get_minio_context() as client:
                target_bucket = bucket or minio_config.bucket
                extra_query_params = {}
                if part_number:
                    extra_query_params["partNumber"] = str(part_number)
                if upload_id:
                    extra_query_params["uploadId"] = upload_id
                
                return client.get_presigned_url(
                    method=method,
                    bucket_name=target_bucket,
                    object_name=object_name,
                    expires=expires,
                    extra_query_params=extra_query_params if extra_query_params else None,
                )
        
        return self._run_async_in_thread(_async_presigned())
    
    def stat_object(self, object_name: str, bucket: Optional[str] = None) -> Any:
        """Get object metadata."""
        async def _async_stat():
            async with get_minio_context() as client:
                target_bucket = bucket or minio_config.bucket
                return client.stat_object(target_bucket, object_name)
        
        return self._run_async_in_thread(_async_stat())
    
    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


class ManagedRedisClient:
    """Redis client wrapper using connection manager"""
    
    def __init__(self):
        self._connection_registry = get_connection_registry()
    
    @property
    def _client(self) -> Optional[redis.Redis]:
        """Compatibility property for existing code"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            else:
                return loop.run_until_complete(self._connection_registry.redis.get_client())
        except Exception:
            return None
    
    async def get_client(self) -> redis.Redis:
        """Get the Redis client asynchronously"""
        return await self._connection_registry.redis.get_client()
    
    async def ping(self) -> bool:
        """Ping Redis server"""
        try:
            async with get_redis_context() as client:
                await client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set field in hash"""
        async with get_redis_context() as client:
            return await client.hset(name, key, value)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get field from hash"""
        async with get_redis_context() as client:
            result = await client.hget(name, key)
            return result.decode() if result else None
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all fields from hash"""
        async with get_redis_context() as client:
            result = await client.hgetall(name)
            return {k.decode(): v.decode() for k, v in result.items()}
    
    async def hmset(self, name: str, mapping: Dict[str, str]) -> bool:
        """Set multiple fields in hash"""
        async with get_redis_context() as client:
            return await client.hmset(name, mapping)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete fields from hash"""
        async with get_redis_context() as client:
            return await client.hdel(name, *keys)
    
    async def expire(self, name: str, time: int) -> bool:
        """Set expiration time"""
        async with get_redis_context() as client:
            return await client.expire(name, time)
    
    async def delete(self, *names: str) -> int:
        """Delete keys"""
        async with get_redis_context() as client:
            return await client.delete(*names)
    
    async def exists(self, *names: str) -> int:
        """Check if keys exist"""
        async with get_redis_context() as client:
            return await client.exists(*names)
    
    async def pipeline(self, transaction: bool = True):
        """Create a Redis pipeline for batch operations"""
        async with get_redis_context() as client:
            return client.pipeline(transaction=transaction)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        async with get_redis_context() as client:
            result = await client.get(key)
            return result.decode() if result else None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        async with get_redis_context() as client:
            return await client.set(key, value, ex=ex)


class ManagedMongoDBClient:
    """MongoDB client wrapper using connection manager"""
    
    def __init__(self):
        self._connection_registry = get_connection_registry()
    
    @property
    def _db(self):
        """Compatibility property for existing code"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            else:
                client = loop.run_until_complete(self._connection_registry.mongodb.get_client())
                return client[mongo_config.db_name]
        except Exception:
            return None
    
    async def get_database(self):
        """Get the MongoDB database asynchronously"""
        client = await self._connection_registry.mongodb.get_client()
        return client[mongo_config.db_name]
    
    async def ping(self) -> bool:
        """Ping MongoDB server"""
        try:
            async with get_mongodb_context() as client:
                await client.admin.command('ping')
                return True
        except Exception as e:
            logger.error(f"MongoDB ping failed: {e}")
            return False
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Any:
        """Insert a single document"""
        async with get_mongodb_context() as client:
            db = client[mongo_config.db_name]
            collection = db[collection_name]
            return await collection.insert_one(document)
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        async with get_mongodb_context() as client:
            db = client[mongo_config.db_name]
            collection = db[collection_name]
            return await collection.find_one(filter_dict)
    
    async def update_one(
        self, 
        collection_name: str, 
        filter_dict: Dict[str, Any], 
        update_dict: Dict[str, Any]
    ) -> Any:
        """Update a single document"""
        async with get_mongodb_context() as client:
            db = client[mongo_config.db_name]
            collection = db[collection_name]
            return await collection.update_one(filter_dict, update_dict)
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Any:
        """Delete a single document"""
        async with get_mongodb_context() as client:
            db = client[mongo_config.db_name]
            collection = db[collection_name]
            return await collection.delete_one(filter_dict)
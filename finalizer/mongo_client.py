import logging
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from config import config


class MongoClient:
    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None
        
        try:
            self._client = AsyncIOMotorClient(config.mongo_url)
            self._db = self._client[config.mongo_db_name]
            logging.info("Connected to MongoDB successfully")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def update_db(self, video_id: str) -> bool:
        if self._db is None:
            logging.error("Database not initialized")
            return False
            
        stream_url = self._build_stream_url(video_id)
        
        try:
            collection = self._db["videos"]
            
            # Update using the upload service schema structure
            update_data = {
                "$set": {
                    "streaming_info": {
                        "url": stream_url
                    },
                    "status": "published",
                    "published_at": self._get_current_datetime(),
                    "last_modified_at": self._get_current_datetime()
                }
            }
            
            result = await collection.update_one(
                {"unique_key": video_id}, 
                update_data
            )
            
            if result.modified_count > 0:
                logging.info(f"Video {video_id} updated successfully with streaming URL: {stream_url}")
                return True
            
            logging.warning(f"No document updated for video {video_id}")
            return False
            
        except Exception as e:
            logging.error(f"Failed to update database: {e}")
            return False
    
    def _build_stream_url(self, video_id: str) -> str:
        if config.minio_public_hostname_override:
            return f"{config.minio_scheme_for_public_url}://{config.minio_public_hostname_override}/{config.minio_stream_bucket}/{video_id}/master.m3u8"
        else:
            return f"http://{config.minio_endpoint}/{config.minio_stream_bucket}/{video_id}/master.m3u8"
    
    def _get_current_datetime(self) -> datetime:
        """Get current UTC datetime for database updates."""
        return datetime.now(timezone.utc)
    
    def disconnect(self):
        if self._client is not None:
            self._client.close()
            logging.info("MongoDB connection closed")

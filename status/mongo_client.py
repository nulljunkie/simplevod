import logging
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from config import config
from models import StatusEvent, VIDEO_STATUSES

class MongoClient:
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None
        self._videos_collection = None
        self._status_logs_collection = None
        self._connect()

    def _connect(self):
        try:
            self._client = AsyncIOMotorClient(config.mongo_url)
            self._db = self._client[config.mongo_db_name]
            self._videos_collection = self._db.videos
            self._status_logs_collection = self._db.status_logs
            logging.info("Connected to MongoDB")
        except ConnectionFailure as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def update_video_status(self, event: StatusEvent) -> tuple[bool, bool]:
        try:
            if event.status not in VIDEO_STATUSES.values():
                logging.warning(f"Unknown status '{event.status}' for video {event.video_id}")
                return False, True

            update_data = {
                'status': event.status,
                'updated_at': event.timestamp
            }

            if event.status == 'published':
                update_data['published_at'] = event.timestamp

            if event.error:
                update_data['error_message'] = event.error

            result = await self._videos_collection.update_one(
                {'unique_key': event.video_id},
                {'$set': update_data}
            )

            if result.matched_count == 0:
                logging.warning(f"Video {event.video_id} not found in database")
                return False, False

            logging.info(f"Updated video {event.video_id} status to {event.status}")
            return True, True

        except Exception as e:
            logging.error(f"Failed to update video status: {e}")
            return False, True

    async def log_status_event(self, event: StatusEvent) -> bool:
        try:
            log_entry = {
                'video_id': event.video_id,
                'status': event.status,
                'service': event.service,
                'timestamp': event.timestamp,
                'metadata': event.metadata,
                'error': event.error
            }

            await self._status_logs_collection.insert_one(log_entry)
            logging.debug(f"Logged status event for video {event.video_id}")
            return True

        except Exception as e:
            logging.error(f"Failed to log status event: {e}")
            return False

    def disconnect(self):
        if self._client:
            self._client.close()
            logging.info("Disconnected from MongoDB")
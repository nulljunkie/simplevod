from datetime import datetime, timezone, timedelta
from core.database import MongoDBClient
from core.minio import MinioClient
from models.models import StoredVideo, RawFileInfo, ThumbnailUrls, SessionData, Parts
from services.storage import StorageService
from core.config import logger, minio_config

class VideoService:
    """Service for managing video metadata and processing."""

    def __init__(self, mongo: MongoDBClient):
        self.mongo = mongo

    async def save_video(
        self, unique_key: str, session_data: SessionData, parts: Parts, user_id: str, username: str, storage_service: StorageService
    ) -> StoredVideo:
        """Save video metadata to MongoDB."""
        thumbnail_urls = ThumbnailUrls(small=None, large=None)
        if session_data.thumbnail_key:
            try:
                storage_service.minio.stat_object(session_data.thumbnail_key, bucket=minio_config.thumbnail_bucket)
                thumbnail_url = storage_service.minio.get_presigned_url(
                    "GET", session_data.thumbnail_key, timedelta(days=7), bucket=minio_config.thumbnail_bucket
                )
                thumbnail_urls.small = thumbnail_url
                thumbnail_urls.large = thumbnail_url
                logger.debug(f"Generated thumbnail URL for key '{session_data.thumbnail_key}'")
            except Exception as e:
                logger.warning(f"Thumbnail not found for key '{session_data.thumbnail_key}': {str(e)}")

        video = StoredVideo(
            unique_key=unique_key,
            title=session_data.title,
            description=session_data.description,
            original_filename=session_data.filename,
            original_content_type=session_data.content_type,
            size_bytes=0,  # Placeholder, to be updated by processing
            duration_seconds=int(session_data.duration) if session_data.duration else None,
            user_id=user_id,
            uploader_username=username,
            status="published",
            visibility=session_data.visibility,
            raw_file_info=RawFileInfo(
                bucket=minio_config.bucket,
                key=session_data.object_key,
                url=storage_service.minio.get_presigned_url(
                    "GET", session_data.object_key, timedelta(days=7)
                ),
            ),
            streaming_info=None,
            thumbnail_urls=thumbnail_urls,
            uploaded_at=datetime.now(timezone.utc),
            published_at=None,
            last_modified_at=datetime.now(timezone.utc),
        )
        
        await self.mongo.insert_one("videos", video.model_dump())
        logger.info(f"Saved video metadata for key '{unique_key}'")
        return video

    async def publish_processing_message(self, video: StoredVideo) -> None:
        """Placeholder for publishing a processing message."""
        logger.info(f"Published processing message for video '{video.unique_key}'")
        # Implement actual message publishing (e.g., to a queue) here

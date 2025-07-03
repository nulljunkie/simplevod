import logging
from io import BytesIO
from typing import Dict, Any, Optional
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client: Optional[Minio] = None
        self.bucket_name = config['bucket']
        
    def connect(self) -> Minio:
        """
        Creates MinIO client connection and validates bucket existence.
        Initializes secure or insecure connection based on configuration.
        Validates that the target bucket exists and is accessible.
        """
        self.client = Minio(
            self.config['endpoint'],
            access_key=self.config['access_key'],
            secret_key=self.config['secret_key'],
            secure=self.config['use_ssl']
        )
        
        if not self._validate_bucket():
            raise RuntimeError(f"MinIO bucket '{self.bucket_name}' validation failed")
            
        logger.info(f"Connected to MinIO at {self.config['endpoint']}, bucket: {self.bucket_name}")
        return self.client
    
    def _validate_bucket(self) -> bool:
        """
        Validates that the configured bucket exists and is accessible.
        Logs appropriate warnings if bucket is not found.
        """
        if not self.client:
            return False
            
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.warning(f'MinIO bucket not found: {self.bucket_name}')
                return False
            return True
        except Exception as e:
            logger.error(f'Failed to validate MinIO bucket: {e}')
            return False
    
    async def upload_playlist_file(self, object_name: str, playlist_content: str) -> bool:
        """
        Uploads playlist content to MinIO as M3U8 file.
        Handles content encoding, stream creation, and proper MIME type setting.
        Provides comprehensive error handling and logging for upload operations.
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
            
        try:
            content_bytes = playlist_content.encode('utf-8')
            content_stream = BytesIO(content_bytes)
            content_length = len(content_bytes)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=content_stream,
                length=content_length,
                content_type='application/vnd.apple.mpegurl'
            )
            
            logger.info(f'Successfully uploaded playlist: {object_name} ({content_length} bytes)')
            return True
            
        except S3Error as e:
            logger.error(f'S3 error uploading {object_name}: {e.code} - {e.message}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error uploading {object_name}: {e}')
            return False
    
    async def upload_media_playlist(self, video_id: str, resolution: str, content: str) -> bool:
        """
        Uploads media playlist for specific video resolution.
        Constructs proper object path and delegates to upload_playlist_file.
        """
        object_name = f'{video_id}/{resolution}/playlist.m3u8'
        success = await self.upload_playlist_file(object_name, content)
        
        if success:
            logger.info(f'Media playlist uploaded for {video_id}/{resolution}')
        else:
            logger.error(f'Failed to upload media playlist for {video_id}/{resolution}')
            
        return success
    
    async def upload_master_playlist(self, video_id: str, content: str) -> bool:
        """
        Uploads master playlist for video containing all resolution variants.
        Creates master playlist at video root level.
        """
        object_name = f'{video_id}/master.m3u8'
        success = await self.upload_playlist_file(object_name, content)
        
        if success:
            logger.info(f'Master playlist uploaded for {video_id}')
        else:
            logger.error(f'Failed to upload master playlist for {video_id}')
            
        return success
    
    async def check_health(self) -> bool:
        """
        Performs health check by listing buckets to verify MinIO connectivity.
        Returns True if MinIO is accessible and responsive.
        """
        if not self.client:
            return False
            
        try:
            list(self.client.list_buckets())
            return True
        except Exception as e:
            logger.error(f'MinIO health check failed: {e}')
            return False
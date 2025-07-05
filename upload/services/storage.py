from typing import Dict, List
from datetime import timedelta
from core.client_wrappers import ManagedMinioClient
from models.models import InitiateUploadRequest, SessionData, Parts
from utils.keys import generate_unique_key
from utils.filename import get_safe_filename
from core.config import minio_config, logger

class StorageService:
    """Service for managing storage operations with MinIO."""

    def __init__(self, minio: ManagedMinioClient):
        self.minio = minio

    async def initiate_upload(self, request: InitiateUploadRequest, user_id: str) -> Dict:
        """Initiate a multipart upload and prepare session data."""
        unique_key = generate_unique_key()
        safe_filename = get_safe_filename(request.filename)
        object_key = f"{unique_key}/{safe_filename}"
        thumbnail_key = f"{unique_key}/{get_safe_filename(request.thumbnail_filename)}" if request.thumbnail_filename else None
        headers = {
            "Content-Type": request.content_type or "application/octet-stream",
            "original-filename": request.filename,
            "user-id": user_id,
            "title": request.title,
            "visibility": request.visibility,
        }
        upload_id = self.minio.create_multipart_upload(object_key, headers)
        thumbnail_url = None
        if thumbnail_key:
            thumbnail_url = self.minio.get_presigned_url(
                "PUT", thumbnail_key, timedelta(minutes=30), bucket=minio_config.thumbnail_bucket
            )
        session_data = SessionData(
            minio_upload_id=upload_id,
            object_key=object_key,
            user_id=user_id,
            filename=safe_filename,
            content_type=request.content_type or "application/octet-stream",
            total_parts=request.total_parts,
            title=request.title,
            description=request.description,
            visibility=request.visibility,
            thumbnail_key=thumbnail_key,
            duration=request.duration,
            status="pending",
            uploaded_parts=0,
        )
        return {
            "key": unique_key,
            "upload_id": upload_id,
            "object_key": object_key,
            "thumbnail_url": thumbnail_url,
            "session_data": session_data,
        }

    async def get_presigned_url(self, object_key: str, upload_id: str, part_number: int) -> str:
        """Generate a presigned URL for a single part."""
        return self.minio.get_presigned_url(
            "PUT", object_key, timedelta(minutes=30), part_number, upload_id
        )

    async def get_presigned_urls(self, object_key: str, upload_id: str, part_numbers: List[int]) -> List[Dict]:
        """Generate presigned URLs for multiple parts."""
        return [
            {
                "partNumber": pn,
                "url": self.minio.get_presigned_url(
                    "PUT", object_key, timedelta(minutes=10), pn, upload_id
                ),
            }
            for pn in part_numbers
        ]

    async def complete_upload(self, object_key: str, upload_id: str, parts: Parts) -> None:
        """Complete a multipart upload."""
        sorted_parts = sorted(parts.parts, key=lambda p: p.part_number)
        self.minio.complete_multipart_upload(object_key, upload_id, sorted_parts)

    async def abort_upload(self, object_key: str, upload_id: str) -> None:
        """Abort a multipart upload."""
        try:
            self.minio.abort_multipart_upload(object_key, upload_id)
        except Exception as e:
            if "NoSuchUpload" not in str(e):
                logger.error(f"Failed to abort upload for key '{object_key}': {str(e)}")
                raise

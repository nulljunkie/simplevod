from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Dict
from bson import ObjectId
from beanie import Document, Indexed

class RawFileInfo(BaseModel):
    """Information about a raw file stored in a bucket."""
    bucket: str = Field(..., description="Storage bucket name")
    key: str = Field(..., description="Object key in the bucket")
    url: Optional[str] = Field(None, description="Presigned URL for the file")

class StreamingInfo(BaseModel):
    """Streaming URL for a video."""
    url: str = Field(..., description="URL for streaming the video")

class ThumbnailUrls(BaseModel):
    """URLs for video thumbnails of different sizes."""
    small: Optional[str] = Field(None, description="URL for small thumbnail")
    large: Optional[str] = Field(None, description="URL for large thumbnail")

class StoredVideo(Document):
    """MongoDB document model for stored videos."""
    unique_key: Indexed(str, unique=True) = Field(..., description="Unique identifier for the video")
    title: str = Field(..., min_length=1, description="Video title")
    description: Optional[str]= Field(None, description="Video description")
    original_filename: str = Field(..., description="Original uploaded filename")
    original_content_type: str = Field(..., description="MIME type of the original file")
    size_bytes: int = Field(..., description="File size in bytes")
    duration_seconds: Optional[int] = Field(None, description="Video duration in seconds")
    user_id: Indexed(str) = Field(..., description="ID of the uploading user")
    uploader_username: Optional[str] = Field(None, description="Username of the uploader")
    status: str = Field("pending_metadata", description="Processing status of the video")
    visibility: str = Field("public", description="Visibility setting (public/private)")
    raw_file_info: RawFileInfo = Field(..., description="Raw file storage details")
    streaming_info: Optional[StreamingInfo] = Field(None, description="Streaming URL details")
    thumbnail_urls: Optional[ThumbnailUrls] = Field(None, description="Thumbnail URLs")
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of video upload",
    )
    published_at: Optional[datetime] = Field(None, description="Timestamp of video publication")
    last_modified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last modification",
    )

    class Settings:
        name = "videos"  # MongoDB collection name
        bson_encoders = {ObjectId: str}  # Convert ObjectId to string for serialization

class InitiateUploadRequest(BaseModel):
    """Request model for initiating a video upload."""
    filename: str = Field(..., description="Name of the file to upload")
    content_type: Optional[str] = Field(None, description="MIME type of the file")
    total_parts: int = Field(..., ge=1, description="Total number of upload parts")
    title: str = Field(..., min_length=1, description="Video title")
    description: str = Field("", description="Video description")
    visibility: str = Field(
        "public",
        pattern=r"^(public|private)$",
        description="Visibility setting (public/private)",
    )
    thumbnail_filename: Optional[str] = Field(None, description="Filename for thumbnail")
    duration: Optional[float] = Field(None, description="Video duration in seconds")

class PresignedUrlRequest(BaseModel):
    """Request model for a single presigned URL."""
    key: str = Field(..., description="Object key for the upload")
    part_number: int = Field(..., ge=1, description="Part number for multipart upload")

class PresignedUrlsRequest(BaseModel):
    """Request model for multiple presigned URLs."""
    key: str = Field(..., description="Object key for the upload")
    part_numbers: List[int] = Field(..., description="List of part numbers for multipart upload")

    @classmethod
    def validate_part_numbers(cls, values: List[int]) -> List[int]:
        """Validate that part numbers are positive and non-empty."""
        if not values:
            raise ValueError("At least one part number must be provided")
        if any(pn < 1 for pn in values):
            raise ValueError("Part numbers must be positive integers")
        return values

class RecordPartRequest(BaseModel):
    """Request model for recording a completed upload part."""
    key: str = Field(..., description="Object key for the upload")
    part_number: int = Field(..., ge=1, description="Part number of the uploaded part")
    etag: str = Field(..., description="ETag of the uploaded part")

class CompleteUploadRequest(BaseModel):
    """Request model for completing a multipart upload."""
    key: str = Field(..., description="Object key for the upload")

class AbortUploadRequest(BaseModel):
    """Request model for aborting a multipart upload."""
    key: str = Field(..., description="Object key for the upload")

class ListPartsRequest(BaseModel):
    """Request model for listing parts of a multipart upload."""
    key: str = Field(..., description="Object key for the upload")


class Part(BaseModel):
    """Represents a part of a multipart upload."""
    part_number: int
    etag: str


class Parts(BaseModel):
    """A list of parts for a multipart upload."""
    parts: List[Part]


class SessionData(BaseModel):
    minio_upload_id: str
    object_key: str
    user_id: str
    filename: str
    content_type: str
    total_parts: int
    title: str
    description: Optional[str] = None
    visibility: str = "public"
    thumbnail_key: Optional[str] = None
    duration: Optional[float] = None
    status: str = "pending"
    uploaded_parts: int = 0

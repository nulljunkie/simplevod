from typing import Dict, List, Optional
from datetime import timedelta
from minio import Minio
from minio.datatypes import Object
from minio.error import S3Error
from .config import minio_config, logger

class MinioClient:
    """A client for interacting with MinIO storage service."""

    def __init__(self) -> None:
        """
        Initialize MinIO client and verify bucket existence

        Raises:
            RuntimeError: If client initialization or bucket check fails.
        """
        self._client: Optional[Minio] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Set up MinIO client and ensure bucket exists."""
        try:
            self._client = Minio(
                endpoint=minio_config.endpoint,
                access_key=minio_config.access_key,
                secret_key=minio_config.secret_key,
                secure=minio_config.use_ssl,
                cert_check=False,
            )
            if not self._client.bucket_exists(minio_config.bucket):
                logger.warning(f"Bucket '{minio_config.bucket}' not found. Creation required.")
                # self._client.make_bucket(minio_config.bucket)
                # logger.info(f"Created bucket '{minio_config.bucket}'")
            else:
                logger.info(f"Connected to bucket '{minio_config.bucket}'")
        except S3Error as e:
            logger.error(f"Failed to initialize bucket '{minio_config.bucket}': {str(e)}")
            raise RuntimeError(f"MinIO bucket initialization failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise RuntimeError(f"MinIO client initialization failed: {str(e)}")

    def create_multipart_upload(self, object_name: str, headers: Dict[str, str]) -> str:
        """Initiate a multipart upload for an object.

        Args:
            object_name: Name of the object to upload.
            headers: HTTP headers for the upload request.

        Returns:
            str: Upload ID for the multipart upload.

        Raises:
            RuntimeError: If multipart upload initiation fails.
        """
        try:
            upload_id = self._client._create_multipart_upload(minio_config.bucket, object_name, headers=headers)
            logger.debug(f"Initiated multipart upload for '{object_name}', ID: {upload_id}")
            return upload_id
        except S3Error as e:
            logger.error(f"Failed to initiate multipart upload for '{object_name}': {str(e)}")
            raise RuntimeError(f"Multipart upload initiation failed: {str(e)}")

    def get_presigned_url(
        self,
        method: str,
        object_name: str,
        expires: timedelta,
        part_number: Optional[int] = None,
        upload_id: Optional[str] = None,
        bucket: Optional[str] = None,
    ) -> str:
        """Generate a presigned URL for an object operation.

        Args:
            method: HTTP method (e.g., 'GET', 'PUT').
            object_name: Name of the object.
            expires: Time duration for URL validity.
            part_number: Part number for multipart upload (optional).
            upload_id: Upload ID for multipart upload (optional).
            bucket: Bucket name (defaults to configured bucket).

        Returns:
            str: Presigned URL for the operation.

        Raises:
            RuntimeError: If URL generation fails.
        """
        target_bucket = bucket or minio_config.bucket
        try:
            url = self._client.get_presigned_url(
                method=method,
                bucket_name=target_bucket,
                object_name=object_name,
                expires=expires,
                extra_query_params={
                    k: v
                    for k, v in {
                        "partNumber": str(part_number) if part_number else None,
                        "uploadId": upload_id,
                    }.items()
                    if v is not None
                },
            )
            logger.debug(f"Generated presigned URL for '{object_name}' in bucket '{target_bucket}'")
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for '{object_name}' in '{target_bucket}': {str(e)}")
            raise RuntimeError(f"Presigned URL generation failed: {str(e)}")

    def complete_multipart_upload(self, object_name: str, upload_id: str, parts: List[Dict]) -> None:
        """Complete a multipart upload for an object.

        Args:
            object_name: Name of the object.
            upload_id: Upload ID for the multipart upload.
            parts: List of completed parts with ETag and part number.

        Raises:
            RuntimeError: If multipart upload completion fails.
        """
        try:
            self._client._complete_multipart_upload(minio_config.bucket, object_name, upload_id, parts)
            logger.info(f"Completed multipart upload for '{object_name}'")
        except S3Error as e:
            logger.error(f"Failed to complete multipart upload for '{object_name}': {str(e)}")
            raise RuntimeError(f"Multipart upload completion failed: {str(e)}")

    def abort_multipart_upload(self, object_name: str, upload_id: str) -> None:
        """Abort a multipart upload for an object.

        Args:
            object_name: Name of the object.
            upload_id: Upload ID for the multipart upload.

        Raises:
            RuntimeError: If multipart upload abortion fails.
        """
        try:
            self._client._abort_multipart_upload(minio_config.bucket, object_name, upload_id)
            logger.info(f"Aborted multipart upload for '{object_name}'")
        except S3Error as e:
            logger.error(f"Failed to abort multipart upload for '{object_name}': {str(e)}")
            raise RuntimeError(f"Multipart upload abortion failed: {str(e)}")

    def object_exists(self, object_name: str, bucket: Optional[str] = None) -> bool:
        """Check if an object exists in a bucket.

        Args:
            object_name: Name of the object.
            bucket: Bucket name (defaults to thumbnail bucket for images, else main bucket).

        Returns:
            bool: True if object exists, False otherwise.
        """
        image_extensions = (".jpg", ".jpeg", ".png")
        target_bucket = (
            bucket
            or (minio_config.thumbnail_bucket if object_name.endswith(image_extensions) else minio_config.bucket)
        )
        try:
            self._client.stat_object(target_bucket, object_name)
            return True
        except S3Error:
            return False

    def stat_object(self, object_name: str, bucket: Optional[str] = None) -> Object:
        """Retrieve metadata for an object.

        Args:
            object_name: Name of the object.
            bucket: Bucket name (defaults to configured bucket).

        Returns:
            Object: Metadata of the object.

        Raises:
            RuntimeError: If object stat retrieval fails.
        """
        target_bucket = bucket or minio_config.bucket
        try:
            result = self._client.stat_object(target_bucket, object_name)
            logger.debug(f"Retrieved metadata for '{object_name}' in '{target_bucket}'")
            return result
        except S3Error as e:
            logger.error(f"Failed to retrieve metadata for '{object_name}' in '{target_bucket}': {str(e)}")
            raise RuntimeError(f"Object stat retrieval failed: {str(e)}")

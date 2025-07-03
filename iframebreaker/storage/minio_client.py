import logging
import datetime
from minio import Minio
from minio.error import S3Error

class MinioClient:
    def __init__(self, config):
        try:
            self.client = Minio(
                config.MINIO_ENDPOINT,
                access_key=config.MINIO_ACCESS_KEY,
                secret_key=config.MINIO_SECRET_KEY,
                secure=config.MINIO_SECURE
            )
            self.expiry = datetime.timedelta(hours=config.PRESIGNED_URL_EXPIRY_HOURS)
            logging.info("Successfully connected to Minio")
        except Exception as e:
            logging.error(f"Failed to initialize MinIO client: {e}")
            raise

    def get_presigned_url(self, bucket_name, object_name):
        """Generate a presigned URL for the specified object."""
        try:
            if not self.client.bucket_exists(bucket_name):
                logging.error(f"Bucket '{bucket_name}' does not exist")
                return None

            # Check if the object actually exists before generating presigned URL
            try:
                self.client.stat_object(bucket_name, object_name)
            except S3Error as stat_err:
                if stat_err.code == 'NoSuchKey':
                    logging.error(f"Object '{bucket_name}/{object_name}' does not exist")
                    return None
                else:
                    logging.error(f"Error checking object existence '{bucket_name}/{object_name}': {stat_err}")
                    return None

            url = self.client.presigned_get_object(
                bucket_name, object_name, expires=self.expiry
            )
            return url

        except S3Error as err:
            logging.error(f"S3Error while generating URL for '{bucket_name}/{object_name}': {err}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error generating presigned URL for '{bucket_name}/{object_name}': {e}")
            return None

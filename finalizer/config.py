from dotenv import load_dotenv
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    def __init__(self) -> None:
        load_dotenv()

        self.mongo_url = os.getenv("MONGO_URL", "mongodb://user:password@localhost:27017")
        self.mongo_db_name = os.getenv("MONGO_DB_NAME", "upload")

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_password = os.getenv("REDIS_PASSWORD", "password")
        self.redis_db = int(os.getenv("REDIS_DB", 0))

        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_stream_bucket = os.getenv("MINIO_STREAM_BUCKET", "stream")

        # User-defined public hostname for Minio (optional). If set, this will be used for stream URLs.
        self.minio_public_hostname_override = os.getenv("MINIO_PUBLIC_HOSTNAME")

        # Scheme for the public Minio URL (https or http). Only used if minio_public_hostname_override is set.
        # Defaults to 'https' if minio_public_hostname_override is set and MINIO_PUBLIC_SCHEME is not 'http'.
        if self.minio_public_hostname_override:
            self.minio_scheme_for_public_url = os.getenv("MINIO_PUBLIC_SCHEME", "https")
            if self.minio_scheme_for_public_url not in ["http", "https"]:
                logging.warning(f"Invalid MINIO_PUBLIC_SCHEME '{self.minio_scheme_for_public_url}', defaulting to 'https' for public URL.")
                self.minio_scheme_for_public_url = "https"
            logging.info(f"Public Minio URL will use: scheme='{self.minio_scheme_for_public_url}', hostname='{self.minio_public_hostname_override}'.")
        else:
            # If no public hostname override, the scheme for internal URLs will be 'http' (handled in mongo_client)
            # and minio_endpoint (with port) will be used.
            # This attribute helps clarify intent or can be used if logic centralizes more in config.
            self.minio_scheme_for_public_url = "http" # Effectively, the scheme for the 'default' case.
            logging.info("MINIO_PUBLIC_HOSTNAME not set. Stream URLs will use internal Minio endpoint (MINIO_ENDPOINT) with 'http' scheme and include the port.")


        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = int(os.getenv("RABBITMQ_PORT", 5672))
        self.rabbitmq_vhost = os.getenv("RABBITMQ_VHOST", "/")
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.consume_queue = os.getenv("RABBITMQ_CONSUME_QUEUE", "finish")

        self.health_port = int(os.getenv("HEALTH_PORT", 8080))


config = Config()

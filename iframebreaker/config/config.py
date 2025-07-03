import os
from dotenv import load_dotenv
import logging

def setup_logging():
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_format = os.environ.get('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=getattr(logging, log_level), format=log_format)
    
    # Suppress verbose third-party library logs
    logging.getLogger('pika').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)

setup_logging()

class Config:
    def __init__(self):
        load_dotenv()
        
        # MinIO Configuration
        self.MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'minio:9000')
        self.MINIO_RAW_BUCKET = os.environ.get('MINIO_RAW_BUCKET', 'raw')
        self.MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
        self.MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin123')
        self.MINIO_SECURE = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'

        # RabbitMQ Configuration
        self.RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.RABBITMQ_VHOST = os.environ.get('RABBITMQ_VHOST', '/')
        self.RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
        self.RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'guest')
        self.RABBITMQ_PUBLISH_EXCHANGE = os.environ.get('RABBITMQ_PUBLISH_EXCHANGE', 'video_segments')
        self.RABBITMQ_PUBLISH_ROUTING_KEY = os.environ.get('RABBITMQ_PUBLISH_ROUTING_KEY', 'segment.process')
        self.RABBITMQ_CONSUME_QUEUE = os.environ.get('RABBITMQ_CONSUME_QUEUE', 'video_upload_queue')
        
        # RabbitMQ Retry Configuration
        self.RABBITMQ_MAX_RETRIES = int(os.environ.get('RABBITMQ_MAX_RETRIES', '5'))
        self.RABBITMQ_RETRY_DELAY = int(os.environ.get('RABBITMQ_RETRY_DELAY', '5'))
        self.RABBITMQ_HEARTBEAT = int(os.environ.get('RABBITMQ_HEARTBEAT', '30'))
        self.RABBITMQ_CONNECTION_ATTEMPTS = int(os.environ.get('RABBITMQ_CONNECTION_ATTEMPTS', '3'))
        
        # Circuit Breaker Configuration
        self.CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.environ.get('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '3'))
        self.CIRCUIT_BREAKER_TIMEOUT = int(os.environ.get('CIRCUIT_BREAKER_TIMEOUT', '60'))

        # Presigned URL Configuration
        self.PRESIGNED_URL_EXPIRY_HOURS = int(os.environ.get('PRESIGNED_URL_EXPIRY_HOURS', '24'))

        # Video Processing Configuration
        self.MIN_PERIOD_SECONDS = float(os.environ.get('MIN_PERIOD_SECONDS', '5.0'))
        self.MAX_PERIOD_SECONDS = float(os.environ.get('MAX_PERIOD_SECONDS', '8.0'))
        self.MESSAGE_SPAN_SECONDS = float(os.environ.get('MESSAGE_SPAN_SECONDS', '60.0'))
        self.FFPROBE_TIMEOUT_SECONDS = int(os.environ.get('FFPROBE_TIMEOUT_SECONDS', '900'))
        
        # Health Check Configuration
        self.HEALTH_CHECK_PORT = int(os.environ.get('HEALTH_CHECK_PORT', '8080'))
        
        # Application Configuration
        self.WORKER_THREADS = int(os.environ.get('WORKER_THREADS', '1'))
        self.GRACEFUL_SHUTDOWN_TIMEOUT = int(os.environ.get('GRACEFUL_SHUTDOWN_TIMEOUT', '30'))

def load_config():
    return Config()

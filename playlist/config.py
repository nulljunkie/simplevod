import os
from dotenv import load_dotenv

load_dotenv()

def get_rabbitmq_config():
    return {
        'host': os.getenv('RABBITMQ_HOST', 'localhost'),
        'port': int(os.getenv('RABBITMQ_PORT', 5672)),
        'user': os.getenv('RABBITMQ_USER', 'guest'),
        'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
        'vhost': os.getenv('RABBITMQ_VHOST', '/'),
        'queue': os.getenv('RABBITMQ_PLAYLIST_QUEUE', 'playlist'),
        'exchange': os.getenv('RABBITMQ_EXCHANGE_NAME', 'video'),
        'routing_key': os.getenv('RABBITMQ_ROUTING_KEY', 'video.finish')
    }

def get_redis_config():
    return {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': os.getenv('REDIS_PASSWORD', 'password'),
        'db': int(os.getenv('REDIS_DB', 0))
    }

def get_minio_config():
    return {
        'endpoint': os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
        'access_key': os.getenv('MINIO_ACCESS_KEY', 'minio'),
        'secret_key': os.getenv('MINIO_SECRET_KEY', 'minio123'),
        'bucket': os.getenv('MINIO_TRANSCODE_BUCKET', 'stream'),
        'use_ssl': os.getenv('MINIO_USE_SSL', 'False').lower() == 'true'
    }

def get_health_port():
    return int(os.getenv('HEALTH_PORT', 8080))
from dataclasses import dataclass
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass(frozen=True)
class MinioConfig:
    """Configuration for MinIO storage service."""
    endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    external_endpoint: str = os.getenv("MINIO_EXTERNAL_ENDPOINT", "api.minio.simplevod.app")
    access_key: str = os.getenv("MINIO_ACCESS_KEY", "minio")
    secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio123")
    bucket: str = os.getenv("MINIO_BUCKET", "raw")
    thumbnail_bucket: str = os.getenv("MINIO_THUMBNAIL_BUCKET", "thumbnail")
    use_ssl: bool = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

@dataclass(frozen=True)
class MongoConfig:
    """Configuration for MongoDB database."""
    url: str = os.getenv("MONGO_URL", "mongodb://user:password@localhost:27017")
    db_name: str = os.getenv("MONGO_DB_NAME", "upload")
    # Connection pool settings
    max_pool_size: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "20"))
    min_pool_size: int = int(os.getenv("MONGO_MIN_POOL_SIZE", "5"))
    max_idle_time_ms: int = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", "30000"))
    server_selection_timeout_ms: int = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))

@dataclass(frozen=True)
class RedisConfig:
    """Configuration for Redis cache."""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD", "password")
    db: int = int(os.getenv("REDIS_DB", "0"))
    session_expiry_seconds: int = int(os.getenv("REDIS_SESSION_EXPIRY_SECONDS", str(24 * 60 * 60)))
    # Connection pool settings
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    health_check_interval: int = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))

@dataclass(frozen=True)
class UvicornConfig:
    """Configuration for Uvicorn server."""
    reload: bool = os.getenv("UVICORN_RELOAD", "True").lower() == "true"

@dataclass(frozen=True)
class JwtConfig:
    """Configuration for JWT authentication."""
    secret_key: str
    algorithm: str = "HS256"

    def __post_init__(self):
        """Validate JWT configuration post-initialization."""
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable must be set")

@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry policies."""
    max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    min_wait_seconds: int = int(os.getenv("RETRY_MIN_WAIT_SECONDS", "4"))
    max_wait_seconds: int = int(os.getenv("RETRY_MAX_WAIT_SECONDS", "10"))
    exponential_multiplier: int = int(os.getenv("RETRY_EXPONENTIAL_MULTIPLIER", "1"))

@dataclass(frozen=True)
class HealthCheckConfig:
    """Configuration for health checks."""
    cache_duration_seconds: int = int(os.getenv("HEALTH_CHECK_CACHE_DURATION", "30"))
    timeout_seconds: int = int(os.getenv("HEALTH_CHECK_TIMEOUT_SECONDS", "5"))

def setup_logger(name: str = "upload", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name (default: 'upload').
        level: Logging level (default: logging.INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
    if debug_enabled:
        level = logging.DEBUG
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:  # Prevent duplicate handlers
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

# Initialize configurations
minio_config = MinioConfig()
mongo_config = MongoConfig()
redis_config = RedisConfig()
uvicorn_config = UvicornConfig()
jwt_config = JwtConfig(secret_key=os.getenv("JWT_SECRET_KEY", "defaultkey"))
retry_config = RetryConfig()
health_check_config = HealthCheckConfig()
logger = setup_logger()

def get_settings():
    """Get all configuration settings as a simple object for easy access."""
    class Settings:
        minio = minio_config
        mongodb = mongo_config
        redis = redis_config
        uvicorn = uvicorn_config
        jwt = jwt_config
        retry = retry_config
        health_check = health_check_config
    
    return Settings()

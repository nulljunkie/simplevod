import asyncio
import logging
import signal
from typing import Optional
from config import get_rabbitmq_config, get_redis_config, get_minio_config, get_health_port
from clients.redis import RedisClient
from clients.minio import MinioClient
from clients.rabbitmq import RabbitMQClient
from services.playlist import PlaylistService
from handlers.playlist_handler import PlaylistHandler
from handlers.health_handler import create_health_app, start_health_server, stop_health_server

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlaylistApp:
    def __init__(self) -> None:
        self.redis_client: Optional[RedisClient] = None
        self.minio_client: Optional[MinioClient] = None
        self.rabbitmq_client: Optional[RabbitMQClient] = None
        self.playlist_service: Optional[PlaylistService] = None
        self.playlist_handler: Optional[PlaylistHandler] = None
        self.health_runner = None
        self.shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """
        Main application startup sequence.
        Initializes all dependencies, starts health server, and begins message processing.
        Handles graceful shutdown and cleanup on termination or errors.
        """
        try:
            await self._setup_dependencies()
            await self._start_health_server()
            await self._start_message_processing()
        except Exception as e:
            logger.error(f'Failed to start application: {e}')
            raise
        finally:
            await self._cleanup()

    async def _setup_dependencies(self) -> None:
        """
        Initializes all service dependencies and creates service layer objects.
        Sets up Redis, MinIO, and RabbitMQ clients, then creates playlist service and handler.
        """
        await self._setup_redis()
        await self._setup_minio()
        await self._setup_rabbitmq()
        
        self.playlist_service = PlaylistService(
            self.redis_client,
            self.minio_client,
            self.rabbitmq_client
        )
        
        self.playlist_handler = PlaylistHandler(self.playlist_service)

    async def _setup_redis(self) -> None:
        """
        Initializes Redis client and establishes connection.
        """
        redis_config = get_redis_config()
        self.redis_client = RedisClient(redis_config)
        await self.redis_client.connect()

    async def _setup_minio(self) -> None:
        """
        Initializes MinIO client and validates bucket access.
        """
        minio_config = get_minio_config()
        self.minio_client = MinioClient(minio_config)
        self.minio_client.connect()

    async def _setup_rabbitmq(self) -> None:
        """
        Initializes RabbitMQ client and establishes connection with channel setup.
        """
        rabbitmq_config = get_rabbitmq_config()
        self.rabbitmq_client = RabbitMQClient(rabbitmq_config)
        await self.rabbitmq_client.connect()

    async def _start_health_server(self) -> None:
        """
        Starts HTTP health check server for Kubernetes probes.
        Creates health application with all dependency health checks.
        """
        health_app = create_health_app(
            self.redis_client,
            self.minio_client,
            self.rabbitmq_client
        )
        health_port = get_health_port()
        self.health_runner = await start_health_server(health_app, health_port)

    async def _start_message_processing(self) -> None:
        """
        Sets up RabbitMQ queue consumption and begins processing playlist messages.
        Configures signal handlers for graceful shutdown and waits for termination.
        """
        queue = await self.rabbitmq_client.setup_playlist_queue()
        
        await queue.consume(self.playlist_handler.create_message_handler())
        
        rabbitmq_config = get_rabbitmq_config()
        logger.info(f"Waiting for messages in queue: {rabbitmq_config['queue']}")
        
        self._setup_signal_handlers()
        await self.shutdown_event.wait()

    def _setup_signal_handlers(self) -> None:
        """
        Configures signal handlers for graceful application shutdown.
        Handles SIGTERM and SIGINT signals from Kubernetes or user interruption.
        """
        def signal_handler(signum, frame):
            logger.info(f'Received signal {signum}, initiating shutdown')
            asyncio.create_task(self._shutdown())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def _shutdown(self) -> None:
        """
        Initiates graceful application shutdown.
        """
        logger.info('Shutdown initiated')
        self.shutdown_event.set()

    async def _cleanup(self) -> None:
        """
        Performs cleanup of all resources and connections.
        Stops health server and closes all client connections gracefully.
        """
        logger.info('Cleaning up application resources')
        
        await stop_health_server(self.health_runner)
        
        if self.rabbitmq_client:
            await self.rabbitmq_client.close()
            
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info('Application cleanup complete')

async def main() -> None:
    """
    Application entry point. Creates and starts the playlist application.
    """
    app = PlaylistApp()
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info('Application interrupted by user')

if __name__ == '__main__':
    asyncio.run(main())

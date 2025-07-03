import json
import logging
from typing import Dict, Any, Optional, Tuple
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractExchange, AbstractQueue

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange: Optional[AbstractExchange] = None
        
    async def connect(self) -> Tuple[AbstractConnection, AbstractChannel, AbstractExchange]:
        """
        Establishes robust connection to RabbitMQ server with proper channel setup.
        Creates connection with authentication, sets up channel with QoS settings,
        and obtains reference to the configured exchange for message publishing.
        """
        self.connection = await aio_pika.connect_robust(
            host=self.config['host'],
            port=self.config['port'],
            virtualhost=self.config['vhost'],
            login=self.config['user'],
            password=self.config['password']
        )
        
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        
        self.exchange = await self.channel.get_exchange(name=self.config['exchange'])
        
        logger.info(f"Connected to RabbitMQ at {self.config['host']}:{self.config['port']}")
        return self.connection, self.channel, self.exchange
    
    async def setup_playlist_queue(self) -> AbstractQueue:
        """
        Declares and configures the playlist processing queue.
        Creates durable queue to ensure message persistence across restarts.
        Returns queue object for message consumption setup.
        """
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not available")
            
        queue = await self.channel.declare_queue(
            self.config['queue'], 
            durable=True
        )
        
        logger.info(f"Playlist queue '{self.config['queue']}' ready for consumption")
        return queue
    
    async def publish_video_completion(self, video_id: str) -> bool:
        """
        Publishes video processing completion notification to configured exchange.
        Creates JSON message with video ID and publishes using configured routing key.
        Handles potential publishing errors and provides appropriate logging.
        """
        if not self.exchange:
            raise RuntimeError("RabbitMQ exchange not available")
            
        try:
            payload = {'video_id': video_id}
            message_body = json.dumps(payload).encode('utf-8')
            
            message = aio_pika.Message(
                body=message_body,
                content_type='application/json'
            )
            
            await self.exchange.publish(
                message=message, 
                routing_key=self.config['routing_key']
            )
            
            logger.info(f'Published completion notification for video: {video_id}')
            return True
            
        except aio_pika.exceptions.AMQPError as e:
            logger.error(f'AMQP error publishing completion for {video_id}: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error publishing completion for {video_id}: {e}')
            return False
    
    def check_health(self) -> bool:
        """
        Performs health check by verifying connection status.
        Returns True if connection is established and not closed.
        """
        if not self.connection:
            return False
        return not self.connection.is_closed
    
    async def close(self) -> None:
        """
        Gracefully closes RabbitMQ connection and cleans up resources.
        Ensures proper cleanup of connection to prevent resource leaks.
        """
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info('RabbitMQ connection closed')
            
        self.connection = None
        self.channel = None
        self.exchange = None
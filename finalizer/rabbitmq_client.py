import logging
from typing import Optional

import aio_pika

from config import config


class RabbitmqClient:
    def __init__(self) -> None:
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                host=config.rabbitmq_host,
                port=config.rabbitmq_port,
                virtualhost=config.rabbitmq_vhost,
                login=config.rabbitmq_user,
                password=config.rabbitmq_password
            )
            
            self.channel = await self.connection.channel()
            logging.info("Connected to RabbitMQ successfully")
            
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        if self.connection is not None:
            await self.connection.close()
            logging.info("RabbitMQ connection closed")

    async def consume_queue(self):
        if self.channel is None:
            logging.error("RabbitMQ not connected")
            return None
            
        try:
            queue = await self.channel.get_queue(config.consume_queue)
            return queue
        except Exception as e:
            logging.error(f"Failed to get queue: {e}")
            return None

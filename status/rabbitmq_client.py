import asyncio
import logging
from typing import Optional

import aio_pika
from aio_pika import Queue
from aio_pika.abc import AbstractRobustConnection

from config import config

class RabbitmqClient:
    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel = None
        self.queue: Optional[Queue] = None

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
            await self.channel.set_qos(prefetch_count=1)
            logging.info("Connected to RabbitMQ")
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def consume_queue(self) -> Optional[Queue]:
        try:
            if not self.channel:
                raise RuntimeError("RabbitMQ channel not initialized")
            
            self.queue = await self.channel.declare_queue(
                config.consume_queue,
                durable=True
            )
            logging.info(f"Declared queue: {config.consume_queue}")
            return self.queue
        except Exception as e:
            logging.error(f"Failed to declare queue: {e}")
            return None

    async def disconnect(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logging.info("Disconnected from RabbitMQ")
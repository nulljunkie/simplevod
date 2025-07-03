import asyncio
import json
import logging
import signal
from typing import Optional

from aio_pika import IncomingMessage
from aiohttp import web

from config import config
from mongo_client import MongoClient
from rabbitmq_client import RabbitmqClient
from redis_client import RedisClient


class FinalizerService:
    def __init__(self):
        self.mongo: Optional[MongoClient] = None
        self.redis: Optional[RedisClient] = None
        self.rabbit: Optional[RabbitmqClient] = None
        self.health_server: Optional[web.Application] = None
        self.shutdown_event = asyncio.Event()

    async def process_message(self, message: IncomingMessage):
        body = message.body.decode()
        
        try:
            data = json.loads(body)
            video_id = data["video_id"]
            
            await self.mongo.update_db(video_id)
            await self.redis.delete_keys(video_id)
            await message.ack()
            
            logging.info(f"Successfully processed video {video_id}")
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in message '{body}': {e}")
            await message.reject(requeue=False)
        except KeyError as e:
            logging.error(f"Missing video_id in message '{body}': {e}")
            await message.reject(requeue=False)
        except Exception as e:
            logging.error(f"Failed to process message '{body}': {e}")
            await message.nack(requeue=True)

    async def setup_health_endpoints(self):
        app = web.Application()
        
        async def liveness_probe(request):
            return web.Response(text="OK", status=200)
        
        async def readiness_probe(request):
            if any(client is None for client in [self.mongo, self.redis, self.rabbit]):
                return web.Response(text="Service not ready", status=503)
            
            try:
                await self.redis.client.ping()
                await self.mongo._client.admin.command('ping')
                return web.Response(text="Ready", status=200)
            except Exception as e:
                logging.error(f"Readiness check failed: {e}")
                return web.Response(text="Service not ready", status=503)
        
        app.router.add_get('/health/live', liveness_probe)
        app.router.add_get('/health/ready', readiness_probe)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', config.health_port)
        await site.start()
        logging.info(f"Health check server started on port {config.health_port}")
        return runner

    async def initialize_clients(self):
        self.mongo = MongoClient()
        self.redis = RedisClient()
        self.rabbit = RabbitmqClient()
        await self.rabbit.connect()
        
        if not all([self.mongo, self.redis, self.rabbit]):
            raise RuntimeError("Failed to initialize clients")

    async def cleanup(self):
        if self.rabbit is not None:
            await self.rabbit.disconnect()
        if self.mongo is not None:
            self.mongo.disconnect()
        if self.redis is not None:
            await self.redis.disconnect()
        logging.info("Cleanup completed")

    def setup_signal_handlers(self):
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, initiating shutdown")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def run(self):
        try:
            self.setup_signal_handlers()
            
            await self.initialize_clients()
            health_runner = await self.setup_health_endpoints()
            
            queue = await self.rabbit.consume_queue()
            if not queue:
                raise RuntimeError("Failed to setup message queue")
            
            await queue.consume(self.process_message)
            logging.info("Finalizer service started successfully")
            
            await self.shutdown_event.wait()
            
        except Exception as e:
            logging.error(f"Service error: {e}")
            raise
        finally:
            await self.cleanup()
            if 'health_runner' in locals():
                await health_runner.cleanup()


async def main():
    service = FinalizerService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())

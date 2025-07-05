import asyncio
import json
import logging
import os
import signal
from typing import Optional

from aio_pika import IncomingMessage
from aiohttp import web

from config import config
from models import StatusEvent
from mongo_client import MongoClient
from rabbitmq_client import RabbitmqClient

debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if debug_enabled else logging.INFO
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

class StatusService:
    def __init__(self):
        self.mongo: Optional[MongoClient] = None
        self.rabbit: Optional[RabbitmqClient] = None
        self.health_server: Optional[web.Application] = None
        self.shutdown_event = asyncio.Event()

    async def process_message(self, message: IncomingMessage):
        body = message.body.decode()
        
        try:
            data = json.loads(body)
            logging.info(f"Received status event: {data}")
            
            event = StatusEvent.from_message(data)
            
            success, video_found = await self.mongo.update_video_status(event)
            
            if success:
                await self.mongo.log_status_event(event)
                await message.ack()
                logging.info(f"Successfully processed status update for video {event.video_id}: {event.status}")
            elif not video_found:
                await message.reject(requeue=False)
                logging.warning(f"Video {event.video_id} not found - rejecting message to without requeue")
            else:
                await message.nack(requeue=True)
                logging.error(f"Failed to update status for video {event.video_id}")
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in message '{body}': {e}")
            await message.reject(requeue=False)
        except KeyError as e:
            logging.error(f"Missing required field in message '{body}': {e}")
            await message.reject(requeue=False)
        except Exception as e:
            logging.error(f"Failed to process message '{body}': {e}")
            await message.nack(requeue=True)

    async def setup_health_endpoints(self):
        @web.middleware
        async def health_logging_middleware(request, handler):
            debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
            if not debug_enabled and request.path.startswith('/health'):
                return await handler(request)
            return await handler(request)
        
        app = web.Application(middlewares=[health_logging_middleware])
        
        async def liveness_probe(request):
            return web.Response(text="OK", status=200)
        
        async def readiness_probe(request):
            if any(client is None for client in [self.mongo, self.rabbit]):
                return web.Response(text="Service not ready", status=503)
            
            try:
                await self.mongo._client.admin.command('ping')
                return web.Response(text="Ready", status=200)
            except Exception as e:
                logging.error(f"Readiness check failed: {e}")
                return web.Response(text="Service not ready", status=503)
        
        app.router.add_get('/health/live', liveness_probe)
        app.router.add_get('/health/ready', readiness_probe)
        
        debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
        access_log = None if not debug_enabled else logging.getLogger('aiohttp.access')
        
        runner = web.AppRunner(app, access_log=access_log)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', config.health_port)
        await site.start()
        logging.info(f"Health check server started on port {config.health_port}")
        return runner

    async def initialize_clients(self):
        self.mongo = MongoClient()
        self.rabbit = RabbitmqClient()
        await self.rabbit.connect()
        
        if not all([self.mongo, self.rabbit]):
            raise RuntimeError("Failed to initialize clients")

    async def cleanup(self):
        if self.rabbit is not None:
            await self.rabbit.disconnect()
        if self.mongo is not None:
            self.mongo.disconnect()
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
            logging.info("Status service started successfully")
            
            await self.shutdown_event.wait()
            
        except Exception as e:
            logging.error(f"Service error: {e}")
            raise
        finally:
            await self.cleanup()
            if 'health_runner' in locals():
                await health_runner.cleanup()

async def main():
    service = StatusService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())

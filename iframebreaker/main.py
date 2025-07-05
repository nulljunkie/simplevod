import logging
import json
import os
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from http.server import BaseHTTPRequestHandler, HTTPServer
from config.config import load_config
from storage.minio_client import MinioClient
from messaging.rabbitmq_client import RabbitMQClient
from services.video_service import VideoService
from services.message_handler import MessageHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, health_checker=None, **kwargs):
        self.health_checker = health_checker
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
        if debug_enabled:
            super().log_message(format, *args)
    
    def do_GET(self):
        if self.path == '/health':
            self._handle_health_check()
        elif self.path == '/ready':
            self._handle_readiness_check()
        elif self.path == '/live':
            self._handle_liveness_check()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_health_check(self):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.health_checker.get_health_status if self.health_checker else lambda: {'status': 'unknown'})
                status = future.result(timeout=5.0)  # 5 second total timeout for health check
            self._respond_json(200 if status['status'] == 'healthy' else 503, status)
        except TimeoutError:
            logging.warning("Health check timed out after 5 seconds")
            self._respond_json(503, {'status': 'timeout', 'error': 'Health check timed out'})
        except Exception as e:
            logging.error(f"Health check error: {e}")
            self._respond_json(503, {'status': 'error', 'error': str(e)})
    
    def _handle_readiness_check(self):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.health_checker.is_ready if self.health_checker else lambda: False)
                ready = future.result(timeout=3.0)  # 3 second timeout for readiness
            self._respond_json(200 if ready else 503, {'ready': ready})
        except TimeoutError:
            logging.warning("Readiness check timed out after 3 seconds")
            self._respond_json(503, {'ready': False, 'error': 'Readiness check timed out'})
        except Exception as e:
            logging.error(f"Readiness check error: {e}")
            self._respond_json(503, {'ready': False, 'error': str(e)})
    
    def _handle_liveness_check(self):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.health_checker.is_alive if self.health_checker else lambda: True)
                alive = future.result(timeout=2.0)  # 2 second timeout for liveness
            self._respond_json(200 if alive else 503, {'alive': alive})
        except TimeoutError:
            logging.warning("Liveness check timed out after 2 seconds")
            self._respond_json(503, {'alive': False, 'error': 'Liveness check timed out'})
        except Exception as e:
            logging.error(f"Liveness check error: {e}")
            self._respond_json(503, {'alive': False, 'error': str(e)})
    
    def _respond_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

class HealthChecker:
    def __init__(self, rabbitmq_client, minio_client, config):
        self.rabbitmq_client = rabbitmq_client
        self.minio_client = minio_client
        self.config = config
    
    def get_health_status(self):
        checks = {
            'rabbitmq': self._check_rabbitmq(),
            'minio': self._check_minio(),
        }
        
        overall_status = 'healthy' if all(checks.values()) else 'unhealthy'
        return {
            'status': overall_status,
            'checks': checks,
            'circuit_breaker': {
                'state': self.rabbitmq_client.circuit_state.value,
                'failures': self.rabbitmq_client.failure_count
            }
        }
    
    def is_ready(self):
        return self._check_rabbitmq() and self._check_minio()
    
    def is_alive(self):
        return True
    
    def _check_rabbitmq(self):
        try:
            return (self.rabbitmq_client.connection and 
                   self.rabbitmq_client.connection.is_open and
                   self.rabbitmq_client.circuit_state.value != 'open')
        except Exception:
            return False
    
    def _check_minio(self):
        def _bucket_check():
            return self.minio_client.client.bucket_exists(self.config.MINIO_RAW_BUCKET)
        
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_bucket_check)
                return future.result(timeout=3.0)  # 3 second timeout for health checks
        except TimeoutError:
            logging.warning("MinIO health check timed out after 3 seconds")
            return False
        except Exception as e:
            logging.debug(f"MinIO health check failed: {e}")
            return False

def start_health_check_server(health_checker, port=8080):
    def handler(*args, **kwargs):
        return HealthCheckHandler(*args, health_checker=health_checker, **kwargs)
    
    server = HTTPServer(('', port), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = False
    thread.start()
    logging.info(f"Health check server started on port {port}")
    return server, thread

def main():
    config = load_config()
    minio_client = MinioClient(config)
    rabbitmq_client = RabbitMQClient(config)
    video_service = VideoService(config)
    message_handler = MessageHandler(config, minio_client, rabbitmq_client, video_service)
    
    health_checker = HealthChecker(rabbitmq_client, minio_client, config)
    health_server, health_thread = start_health_check_server(health_checker, config.HEALTH_CHECK_PORT)

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down...")
        try:
            rabbitmq_client.close()
        except Exception as e:
            logging.error(f"Shutting down error: {e}")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    def rabbitmq_consumer_worker():
        try:
            rabbitmq_client.connect()
            rabbitmq_client.consume(message_handler.process_video_message)
        except Exception as e:
            logging.error(f"RabbitMQ consumer error: {e}")
            rabbitmq_client.close()

    consumer_thread = threading.Thread(target=rabbitmq_consumer_worker)
    consumer_thread.daemon = False
    consumer_thread.start()

    try:
        consumer_thread.join()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()

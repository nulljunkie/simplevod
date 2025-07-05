import pika
import json
import logging
import time
import threading
from enum import Enum
from typing import Optional, Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RabbitMQClient:
    def __init__(self, config):
        self.config = config
        credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
        self.parameters = pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            virtual_host=config.RABBITMQ_VHOST,
            credentials=credentials,
            heartbeat=config.RABBITMQ_HEARTBEAT,
            connection_attempts=config.RABBITMQ_CONNECTION_ATTEMPTS,
            retry_delay=config.RABBITMQ_RETRY_DELAY
        )
        self.connection = None
        self.channel = None
        self.max_retries = config.RABBITMQ_MAX_RETRIES
        self.retry_delay = config.RABBITMQ_RETRY_DELAY
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_timeout = config.CIRCUIT_BREAKER_TIMEOUT
        self.failure_threshold = config.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self._lock = threading.Lock()

    def _is_circuit_open(self) -> bool:
        with self._lock:
            if self.circuit_state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.circuit_timeout:
                    self.circuit_state = CircuitState.HALF_OPEN
                    logging.info("Circuit breaker moving to half-open state")
                    return False
                return True
            return False

    def _record_success(self):
        with self._lock:
            self.failure_count = 0
            self.circuit_state = CircuitState.CLOSED

    def _record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.circuit_state = CircuitState.OPEN
                logging.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def _ensure_connection(self) -> bool:
        if self.connection and self.connection.is_open:
            return True
        
        if self._is_circuit_open():
            logging.error("Circuit breaker is open, not attempting connection")
            return False
            
        return self._reconnect()

    def _reconnect(self) -> bool:
        retries = 0
        while retries < self.max_retries:
            try:
                if self.connection and self.connection.is_open:
                    self.connection.close()
                
                self.connection = pika.BlockingConnection(self.parameters)
                self.channel = self.connection.channel()
                self.channel.basic_qos(prefetch_count=1)
                self._record_success()
                logging.info("Successfully connected to RabbitMQ")
                return True
                
            except Exception as err:
                logging.error(f"Failed to connect to RabbitMQ: {err}")
                self._record_failure()
                retries += 1
                
                if retries >= self.max_retries:
                    logging.error("Max retries reached. Could not connect to RabbitMQ.")
                    return False
                
                delay = min(self.retry_delay * (2 ** (retries - 1)), 60)
                logging.info(f"Retrying connection in {delay} seconds...")
                time.sleep(delay)
        
        return False

    def connect(self):
        """Establish RabbitMQ connection and channel with circuit breaker."""
        if not self._ensure_connection():
            raise Exception("Failed to establish RabbitMQ connection")

    def setup_queues(self):
        """Declare exchange and queues."""
        self.channel.exchange_declare(
            exchange=self.config.RABBITMQ_PUBLISH_EXCHANGE,
            exchange_type='topic',
            durable=True
        )
        self.channel.queue_declare(queue=self.config.RABBITMQ_CONSUME_QUEUE, durable=True)
        self.channel.queue_declare(queue=self.config.RABBITMQ_CONSUME_QUEUE + '_segments', durable=True)
        self.channel.queue_bind(
            queue=self.config.RABBITMQ_CONSUME_QUEUE + '_segments',
            exchange=self.config.RABBITMQ_PUBLISH_EXCHANGE,
            routing_key=self.config.RABBITMQ_PUBLISH_ROUTING_KEY
        )

    def publish_segment(self, segment_payload) -> bool:
        """Publish a segment message to RabbitMQ with retry logic."""
        for attempt in range(self.max_retries):
            if not self._ensure_connection():
                return False
                
            try:
                self.channel.basic_publish(
                    exchange=self.config.RABBITMQ_PUBLISH_EXCHANGE,
                    routing_key=self.config.RABBITMQ_PUBLISH_ROUTING_KEY,
                    body=json.dumps(segment_payload),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                self._record_success()
                return True
                
            except Exception as err:
                logging.error(f"Failed to publish segment (attempt {attempt + 1}): {err}")
                self._record_failure()
                self.connection = None
                self.channel = None
                
                if attempt < self.max_retries - 1:
                    time.sleep(min(2 ** attempt, 10))
                    
        return False

    def publish_status(self, video_id: str, status: str, service: str = "iframebreaker", metadata: dict = None, error: str = None) -> bool:
        """Publish a status update message to RabbitMQ with retry logic."""
        from datetime import datetime
        
        status_payload = {
            "video_id": video_id,
            "status": status,
            "service": service,
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "metadata": metadata or {},
            "error": error
        }
        
        for attempt in range(self.max_retries):
            if not self._ensure_connection():
                return False
                
            try:
                self.channel.basic_publish(
                    exchange="video",
                    routing_key="video.status",
                    body=json.dumps(status_payload),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                self._record_success()
                logging.info(f"Published status update: video_id={video_id}, status={status}")
                return True
                
            except Exception as err:
                logging.error(f"Failed to publish status (attempt {attempt + 1}): {err}")
                self._record_failure()
                self.connection = None
                self.channel = None
                
                if attempt < self.max_retries - 1:
                    time.sleep(min(2 ** attempt, 10))
                    
        return False

    def consume(self, callback):
        """Start consuming messages from the queue with automatic reconnection."""
        while True:
            try:
                if not self._ensure_connection():
                    logging.error("Cannot establish connection for consuming")
                    time.sleep(self.retry_delay)
                    continue
                    
                self.channel.basic_consume(
                    queue=self.config.RABBITMQ_CONSUME_QUEUE,
                    on_message_callback=callback
                )
                logging.info(f"Waiting for messages on queue '{self.config.RABBITMQ_CONSUME_QUEUE}'")
                self.channel.start_consuming()
                
            except KeyboardInterrupt:
                logging.info("Interrupted by user. Closing connection...")
                self.close()
                break
                
            except (pika.exceptions.AMQPConnectionError, 
                    pika.exceptions.ChannelClosedByBroker,
                    pika.exceptions.ConnectionClosedByBroker) as e:
                logging.error(f"Connection lost during consuming: {e}")
                self._record_failure()
                self.connection = None
                self.channel = None
                
                if self._is_circuit_open():
                    logging.error("Circuit breaker open, waiting before retry...")
                    time.sleep(self.circuit_timeout)
                else:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                logging.error(f"Unexpected error in consuming: {e}")
                time.sleep(self.retry_delay)

    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
        logging.info("RabbitMQ connection closed")

from dotenv import load_dotenv
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    def __init__(self) -> None:
        load_dotenv()

        self.mongo_url = os.getenv("MONGO_URL", "mongodb://user:password@localhost:27017")
        self.mongo_db_name = os.getenv("MONGO_DB_NAME", "upload")

        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = int(os.getenv("RABBITMQ_PORT", 5672))
        self.rabbitmq_vhost = os.getenv("RABBITMQ_VHOST", "/")
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.consume_queue = os.getenv("RABBITMQ_CONSUME_QUEUE", "status")

        self.health_port = int(os.getenv("HEALTH_PORT", 8080))

config = Config()
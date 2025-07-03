import json
import logging
from urllib.parse import unquote
from pathvalidate import sanitize_filename
from config.config import Config
from storage.minio_client import MinioClient
from messaging.rabbitmq_client import RabbitMQClient
from services.video_service import VideoService

class MessageHandler:
    def __init__(self, config: Config, minio_client: MinioClient, rabbitmq_client: RabbitMQClient, video_service: VideoService):
        self.config = config
        self.minio_client = minio_client
        self.rabbitmq_client = rabbitmq_client
        self.video_service = video_service

    def process_video_message(self, ch, method, properties, body):
        """Process incoming RabbitMQ message."""
        try:
            message_data = json.loads(body.decode('utf-8'))

            record = message_data.get("Records", [{}])[0]
            s3_info = record.get("s3", {})
            bucket = s3_info.get("bucket", {}).get("name")
            encoded_key = s3_info.get("object", {}).get("key")

            if not bucket or not encoded_key:
                logging.error("No bucket or key in message")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            # URL decode the key since MinIO sends it encoded but the client will encode it again
            key = unquote(encoded_key)

            presigned_url = self.minio_client.get_presigned_url(bucket, key)
            
            # If the presigned URL fails with the original key, try alternatives
            if not presigned_url:
                # Extract session ID and filename from the key
                key_parts = key.split('/', 1)
                if len(key_parts) == 2:
                    session_id, filename = key_parts
                    
                    # Try different filename variations
                    alternatives = [
                        # 1. Convert + signs to spaces (since + is URL encoding for space)
                        filename.replace('+', ' '),
                        # 2. Sanitized version to match upload service behavior  
                        sanitize_filename(filename, platform="universal").lower(),
                        # 3. Sanitized version of the + to space converted filename
                        sanitize_filename(filename.replace('+', ' '), platform="universal").lower()
                    ]
                    
                    for alt_filename in alternatives:
                        if alt_filename != filename:  # Skip if same as original
                            alt_key = f"{session_id}/{alt_filename}"
                            presigned_url = self.minio_client.get_presigned_url(bucket, alt_key)
                            if presigned_url:
                                key = alt_key  # Use the working key for further processing
                                break
                
            if not presigned_url:
                logging.error(f"Failed to generate presigned URL for {bucket}/{key} (tried both original and sanitized)")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            video_id = self.video_service.extract_video_id(key)
            logging.info(f"Processing New Upload: {key}")

            keyframes, total_duration = self.video_service.get_video_info(presigned_url)
            if keyframes is None or total_duration is None:
                logging.error(f"Failed to get video info for {key}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            cut_points = self.video_service.get_video_cut_points(presigned_url)

            if cut_points is None or len(cut_points) < 2:
                logging.warning(f"No valid cut points created for {key}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            batches = self.video_service.batch_timestamps(cut_points, self.config.MESSAGE_SPAN_SECONDS)

            total_messages = len(batches)
            for i, batch in enumerate(batches):
                message_id = i + 1
                segment_payload = {
                    "message_id": message_id,
                    "video_url": presigned_url,
                    "video_id": video_id,
                    "timestamps": batch,
                    "total_video_duration": total_duration,
                    "total_messages": total_messages
                }
                if not self.rabbitmq_client.publish_segment(segment_payload):
                    logging.error(f"Failed to publish segment {message_id} for {video_id}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return

            logging.info(f"Processed: {key}, {total_messages} messages published to \"{self.config.RABBITMQ_PUBLISH_EXCHANGE}\" exchange")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            logging.error(f"Failed to decode message: {body}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

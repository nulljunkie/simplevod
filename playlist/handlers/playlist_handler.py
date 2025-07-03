import json
import logging
from typing import Callable, Awaitable
from pydantic import ValidationError
import aio_pika
from models import PlaylistMessage
from services.playlist import PlaylistService

logger = logging.getLogger(__name__)

class PlaylistHandler:
    def __init__(self, playlist_service: PlaylistService) -> None:
        self.playlist_service = playlist_service
        
    async def handle_playlist_message(self, message: aio_pika.IncomingMessage) -> None:
        """
        Handles incoming playlist generation messages from RabbitMQ.
        Parses message content, processes playlist request through service layer,
        and manages message acknowledgment or rejection based on processing results.
        Provides comprehensive error handling for malformed messages and processing failures.
        """
        async with message.process(ignore_processed=True):
            try:
                playlist_msg = self._parse_message(message)
                
                success = await self.playlist_service.process_playlist_request(
                    playlist_msg.video_id,
                    playlist_msg.resolution
                )
                
                if success:
                    await message.ack()
                    logger.info(f'Successfully processed playlist: {playlist_msg.video_id}/{playlist_msg.resolution}')
                else:
                    await message.nack(requeue=False)
                    logger.error(f'Failed to process playlist: {playlist_msg.video_id}/{playlist_msg.resolution}')
                    
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f'Invalid message format: {e}. Message: {message.body.decode()}')
                await message.reject(requeue=False)
            except Exception as e:
                logger.error(f'Unexpected error processing playlist message: {e}')
                await message.nack(requeue=False)
    
    def _parse_message(self, message: aio_pika.IncomingMessage) -> PlaylistMessage:
        """
        Parses RabbitMQ message into PlaylistMessage object.
        Decodes message body, parses JSON content, and validates against schema.
        Raises appropriate exceptions for malformed or invalid messages.
        """
        try:
            body = message.body.decode('utf-8')
            data = json.loads(body)
            return PlaylistMessage(**data)
        except UnicodeDecodeError as e:
            raise ValueError(f'Failed to decode message body: {e}')
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f'Invalid JSON in message: {e}', body, e.pos)
        except ValidationError as e:
            raise ValidationError(f'Message validation failed: {e}')
    
    def create_message_handler(self) -> Callable[[aio_pika.IncomingMessage], Awaitable[None]]:
        """
        Creates message handler function for RabbitMQ queue consumption.
        Returns callable that can be passed to queue.consume() method.
        """
        return self.handle_playlist_message

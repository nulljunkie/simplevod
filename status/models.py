from datetime import datetime
from typing import Optional, Dict, Any

class StatusEvent:
    def __init__(
        self,
        video_id: str,
        status: str,
        service: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.video_id = video_id
        self.status = status
        self.service = service
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
        self.error = error

    @classmethod
    def from_message(cls, data: Dict[str, Any]) -> 'StatusEvent':
        return cls(
            video_id=data['video_id'],
            status=data['status'],
            service=data['service'],
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) if 'timestamp' in data else None,
            metadata=data.get('metadata'),
            error=data.get('error')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'video_id': self.video_id,
            'status': self.status,
            'service': self.service,
            'timestamp': self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'metadata': self.metadata,
            'error': self.error
        }

VIDEO_STATUSES = {
    'uploaded': 'uploaded',
    'processing': 'processing', 
    'transcoding': 'transcoding',
    'published': 'published',
    'failed': 'failed'
}
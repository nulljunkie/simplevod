from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel

class PlaylistMessage(BaseModel):
    video_id: str
    resolution: str

class Segment(BaseModel):
    path: str
    duration: float

class PlaylistContent(BaseModel):
    content: str
    target_duration: int

class VideoMetadata(BaseModel):
    resolution_bandwidths: Dict[str, str]
    completed_resolutions: List[str]
    expected_count: int

class HealthStatus(Enum):
    HEALTHY = 'healthy'
    UNHEALTHY = 'unhealthy'

class ComponentHealth(BaseModel):
    status: HealthStatus
    message: Optional[str] = None
    last_checked: Optional[float] = None

class HealthResponse(BaseModel):
    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: float
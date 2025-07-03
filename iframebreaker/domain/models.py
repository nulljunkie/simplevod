from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class VideoInfo:
    keyframes: List[float]
    duration: float
    video_id: str

@dataclass(frozen=True)
class SegmentMessage:
    message_id: int
    video_url: str
    video_id: str
    timestamps: List[float]
    total_duration: float
    total_messages: int

@dataclass(frozen=True)
class ProcessingResult:
    success: bool
    segments: Optional[List[SegmentMessage]] = None
    error: Optional[str] = None

@dataclass(frozen=True)
class HealthStatus:
    status: str
    checks: dict
    circuit_breaker: Optional[dict] = None
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any

class VideoAnalyzer(ABC):
    @abstractmethod
    def extract_keyframes(self, video_url: str) -> Tuple[Optional[List[float]], Optional[float]]:
        pass

class TimestampSelector(ABC):
    @abstractmethod
    def select_optimal_timestamps(
        self, 
        keyframes: List[float], 
        min_period: float, 
        max_period: float
    ) -> List[float]:
        pass

class MessagePublisher(ABC):
    @abstractmethod
    def publish(self, message: Any) -> bool:
        pass

class HealthMonitor(ABC):
    @abstractmethod
    def is_healthy(self) -> bool:
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        pass

class ConnectionManager(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        pass
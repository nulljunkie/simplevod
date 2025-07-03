import subprocess
import json
import logging
from urllib.parse import urlparse
from pathlib import Path
from typing import List, Optional, Tuple
from config.config import Config
from infrastructure.video_analyzer import FFProbeVideoAnalyzer
from infrastructure.timestamp_selector import OptimalTimestampSelector

class VideoService:
    def __init__(self, config: Config):
        self.config = config
        self._video_analyzer = FFProbeVideoAnalyzer()
        self._timestamp_selector = OptimalTimestampSelector()

    def get_video_info(self, video_url: str) -> Tuple[Optional[List[float]], Optional[float]]:
        """Extract keyframe timestamps and duration using ffprobe with a presigned URL."""
        return self._video_analyzer.extract_keyframes(video_url)

    def get_video_cut_points(self, video_url: str) -> Optional[List[float]]:
        """Return clean cut points for a video using optimal I-frame selection."""

        iframe_ts, _ = self.get_video_info(video_url)
        if iframe_ts is None:
            logging.error("Could not retrieve I-frame timestamps; aborting cut generation.")
            return None

        return self._timestamp_selector.select_optimal_timestamps(
            iframe_ts,
            self.config.MIN_PERIOD_SECONDS,
            self.config.MAX_PERIOD_SECONDS,
        )

    @staticmethod
    def extract_video_id(object_key: str) -> str:
        """Extract video ID (session ID) from object key.
        
        Object key format: raw/session_id/filename.ext
        Returns: session_id
        """
        try:
            # Remove bucket prefix if present
            if object_key.startswith('raw/'):
                object_key = object_key[4:]  # Remove 'raw/' prefix
            
            # Split by '/' and get the first part (session ID)
            parts = object_key.split('/')
            if len(parts) >= 2:
                return parts[0]  # Return session ID
            else:
                # Fallback: if no session structure, use the whole path as ID
                return Path(object_key).stem
        except Exception as e:
            logging.warning(f"Could not extract video ID from {object_key}: {e}")
            return Path(object_key).stem


    @staticmethod
    def batch_timestamps(timestamps: List[float], span: float) -> List[List[float]]:
        """Group sorted timestamps into overlapping windows."""
        if not timestamps:
            return []

        batches: List[List[float]] = []
        batch: List[float] = [timestamps[0]]

        for ts in timestamps[1:]:
            if ts - batch[0] <= span:
                batch.append(ts)
            else:
                batches.append(batch)
                batch = [batch[-1], ts]

        batches.append(batch)
        return batches

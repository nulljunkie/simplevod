import subprocess
import json
import logging
from typing import List, Optional, Tuple
from domain.interfaces import VideoAnalyzer
from config.config import load_config

class FFProbeVideoAnalyzer(VideoAnalyzer):
    
    def __init__(self):
        self.config = load_config()
    
    def extract_keyframes(self, video_url: str) -> Tuple[Optional[List[float]], Optional[float]]:
        
        try:
            ffprobe_data = self._run_ffprobe(video_url)
            keyframes = self._extract_keyframe_timestamps(ffprobe_data)
            duration = self._extract_duration(ffprobe_data)
            
            if not keyframes:
                keyframes = self._handle_no_keyframes(duration)
                if not keyframes:
                    return None, None
            
            keyframes = self._ensure_starts_at_zero(keyframes)
            keyframes = self._deduplicate_and_sort(keyframes)
            
            return keyframes, duration
            
        except Exception as e:
            logging.error(f"Error analyzing video {video_url}: {e}")
            return None, None

    def _run_ffprobe(self, video_url: str) -> dict:
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-skip_frame", "nokey",
            "-show_entries", "frame=pts_time:format=duration",
            "-of", "json",
            video_url
        ]
        
        timeout_seconds = self.config.FFPROBE_TIMEOUT_SECONDS
        
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=timeout_seconds)
            return json.loads(process.stdout)
        except subprocess.TimeoutExpired:
            logging.error(f"FFProbe timeout ({timeout_seconds}s) for video: {video_url}")
            raise
        except subprocess.CalledProcessError as e:
            logging.error(f"FFProbe failed for video {video_url}: {e.stderr}")
            raise

    def _extract_keyframe_timestamps(self, data: dict) -> List[float]:
        frames = data.get("frames", [])
        return [float(frame["pts_time"]) for frame in frames if "pts_time" in frame]

    def _extract_duration(self, data: dict) -> Optional[float]:
        duration_str = data.get("format", {}).get("duration")
        if duration_str:
            return float(duration_str)
        return None

    def _handle_no_keyframes(self, duration: Optional[float]) -> Optional[List[float]]:
        if duration:
            logging.warning("No keyframes found, using start timestamp")
            return [0.0]
        return None

    def _ensure_starts_at_zero(self, keyframes: List[float]) -> List[float]:
        if not keyframes or keyframes[0] > 0.0:
            keyframes.insert(0, 0.0)
        return keyframes

    def _deduplicate_and_sort(self, keyframes: List[float]) -> List[float]:
        return sorted(list(set(keyframes)))
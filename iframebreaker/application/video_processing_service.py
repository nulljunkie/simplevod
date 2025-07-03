import logging
from typing import List, Optional
from urllib.parse import urlparse
from pathlib import Path

from domain.interfaces import VideoAnalyzer, TimestampSelector, MessagePublisher
from domain.models import VideoInfo, SegmentMessage, ProcessingResult

class VideoProcessingService:
    
    def __init__(
        self, 
        video_analyzer: VideoAnalyzer,
        timestamp_selector: TimestampSelector,
        message_publisher: MessagePublisher,
        min_period: float,
        max_period: float,
        message_span: float
    ):
        self._video_analyzer = video_analyzer
        self._timestamp_selector = timestamp_selector
        self._message_publisher = message_publisher
        self._min_period = min_period
        self._max_period = max_period
        self._message_span = message_span

    def process_video(self, video_url: str) -> ProcessingResult:
        try:
            video_info = self._analyze_video(video_url)
            if not video_info:
                return ProcessingResult(success=False, error="Failed to analyze video")
            
            cut_points = self._generate_cut_points(video_info.keyframes)
            if not self._has_valid_cut_points(cut_points):
                return ProcessingResult(success=False, error="No valid cut points generated")
            
            segments = self._create_segments(video_info, cut_points, video_url)
            success = self._publish_segments(segments)
            
            if success:
                return ProcessingResult(success=True, segments=segments)
            else:
                return ProcessingResult(success=False, error="Failed to publish segments")
                
        except Exception as e:
            logging.error(f"Error processing video {video_url}: {e}")
            return ProcessingResult(success=False, error=str(e))

    def _analyze_video(self, video_url: str) -> Optional[VideoInfo]:
        keyframes, duration = self._video_analyzer.extract_keyframes(video_url)
        if keyframes is None or duration is None:
            return None
        
        video_id = self._extract_video_id(video_url)
        return VideoInfo(keyframes=keyframes, duration=duration, video_id=video_id)

    def _generate_cut_points(self, keyframes: List[float]) -> List[float]:
        return self._timestamp_selector.select_optimal_timestamps(
            keyframes, self._min_period, self._max_period
        )

    def _has_valid_cut_points(self, cut_points: List[float]) -> bool:
        return cut_points and len(cut_points) >= 2

    def _create_segments(
        self, 
        video_info: VideoInfo, 
        cut_points: List[float], 
        video_url: str
    ) -> List[SegmentMessage]:
        batches = self._batch_timestamps(cut_points)
        segments = []
        
        for i, batch in enumerate(batches):
            segment = SegmentMessage(
                message_id=i + 1,
                video_url=video_url,
                video_id=video_info.video_id,
                timestamps=batch,
                total_duration=video_info.duration,
                total_messages=len(batches)
            )
            segments.append(segment)
        
        return segments

    def _batch_timestamps(self, timestamps: List[float]) -> List[List[float]]:
        if not timestamps:
            return []

        batches = []
        batch = [timestamps[0]]

        for ts in timestamps[1:]:
            if ts - batch[0] <= self._message_span:
                batch.append(ts)
            else:
                batches.append(batch)
                batch = [batch[-1], ts]

        batches.append(batch)
        return batches

    def _publish_segments(self, segments: List[SegmentMessage]) -> bool:
        for segment in segments:
            if not self._message_publisher.publish(segment):
                return False
        return True

    def _extract_video_id(self, video_url: str) -> str:
        try:
            path = Path(urlparse(video_url).path)
            return path.stem
        except Exception:
            logging.warning(f"Could not extract video ID from {video_url}")
            return Path(video_url).name
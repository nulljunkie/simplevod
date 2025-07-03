#!/usr/bin/env python3

import sys
import argparse
import logging
import os
import json
from typing import List

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.video_service import VideoService
from config.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def log_rabbitmq_payloads(cut_points, video_id, video_url, total_duration, span_seconds=60.0):
    """
    Constructs and logs the JSON payloads that would be sent to RabbitMQ.
    
    Args:
        cut_points: List of timestamps representing cut points.
        video_id: Identifier for the video.
        video_url: The URL of the video.
        total_duration: The total duration of the video.
        span_seconds: Span of seconds for batching.
    """
    if not cut_points or len(cut_points) < 2:
        logging.warning(f"No valid segments to generate payloads for video: {video_id}")
        return

    segments = VideoService.batch_timestamps(cut_points, span_seconds)
    
    total_messages = len(segments)
    
    print(f"\n--- Simulating RabbitMQ Payloads for video: {video_id} ---")
    print(f"Total Messages to be published: {total_messages}")
    print("-" * 60)

    for i, segment in enumerate(segments):
        message_id = i + 1
        segment_payload = {
            "message_id": message_id,
            "video_url": video_url,
            "video_id": video_id,
            "timestamps": segment,
            "total_video_duration": total_duration,
            "total_messages": total_messages
        }
        # Log the exact JSON string that would be published
        print(json.dumps(segment_payload, indent=4))
        if i < len(segments) - 1:
            print("-" * 20) # Separator between messages

    print("-" * 60)


def test_video_cuts(video_input, min_duration=5.0, max_duration=8.0, message_span=60.0):
    """
    Tests the video cutting logic by generating and printing simulated RabbitMQ payloads.
    
    Args:
        video_input: URL or local path to the video.
        min_duration: Minimum segment duration in seconds.
        max_duration: Maximum segment duration in seconds.
        message_span: Span of seconds for batching.
    """
    logging.info(f"Processing video: {video_input}")
    
    config = Config()
    config.MIN_PERIOD_SECONDS = min_duration
    config.MAX_PERIOD_SECONDS = max_duration
    video_service = VideoService(config)

    # 1. Get video info (iframes and duration)
    iframe_timestamps, video_total_duration = video_service.get_video_info(video_input)
    
    if iframe_timestamps is None or video_total_duration is None:
        logging.error(f"Failed to retrieve video info for {video_input}. Cannot generate cuts.")
        return

    logging.info(f"Retrieved {len(iframe_timestamps)} I-frames and duration {video_total_duration:.2f}s.")

    # 2. Generate simple cuts
    cut_points = video_service.get_video_cut_points(video_input)
    
    # 3. Log the simulated RabbitMQ payloads
    if cut_points:
        video_id = video_service.extract_video_id(video_input)
        log_rabbitmq_payloads(
            cut_points,
            video_id,
            video_input,
            video_total_duration,
            span_seconds=message_span,
        )
    else:
        logging.error(f"Failed to generate cut points for {video_input}")

def main():
    parser = argparse.ArgumentParser(description="Test video cutting logic and simulate RabbitMQ message payloads.")
    parser.add_argument("video_input", help="URL or local path to the video file.")
    parser.add_argument("--min-duration", type=float, default=5.0, help="Minimum segment duration in seconds (default: 5.0).")
    parser.add_argument("--max-duration", type=float, default=8.0, help="Maximum segment duration in seconds (default: 8.0).")
    parser.add_argument("--message-span", type=float, default=60.0, help="Seconds span per message window (default: 60.0)")
    
    args = parser.parse_args()
    
    test_video_cuts(
        args.video_input,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        message_span=args.message_span,
    )

if __name__ == "__main__":
    main()

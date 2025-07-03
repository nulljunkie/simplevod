#!/usr/bin/env python3

import sys
import argparse
import logging
import os
from typing import List

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.video_service import VideoService
from config.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="List the first 500 raw I-frame timestamps from a video using ffprobe.")
    parser.add_argument("video_input", help="URL or local path to the video file.")
    
    args = parser.parse_args()
    
    logging.info(f"Retrieving raw I-frame timestamps for video: {args.video_input}")
    
    config = Config()
    video_service = VideoService(config)

    iframe_timestamps, _ = video_service.get_video_info(args.video_input)
    
    if iframe_timestamps is None:
        logging.error(f"Failed to retrieve I-frame timestamps for {args.video_input}.")
        return

    print(f"\n--- First 500 Raw I-frame Timestamps for {args.video_input} ---")
    for i, ts in enumerate(iframe_timestamps):
        if i >= 500:
            break
        print(f"{ts:.3f}", end=" ")

if __name__ == "__main__":
    main()

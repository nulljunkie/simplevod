export interface VideoPlayerQuality {
  level: number;
  height: number;
  name: string;
  bitrate?: number;
}

export interface VideoPlayerState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  isBuffering: boolean;
  currentQuality: number;
  availableQualities: VideoPlayerQuality[];
  playbackRate: number;
  isFullScreen: boolean;
  errorMessage: string | null;
}

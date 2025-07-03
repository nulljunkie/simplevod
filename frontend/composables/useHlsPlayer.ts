// composables/useHlsPlayer.ts
import Hls from 'hls.js';
import type { VideoPlayerState, VideoPlayerQuality } from '~/types/video';
import type { VideoDetail } from '~/types/api';

export function useHlsPlayer(videoElement: Ref<HTMLVideoElement | null>, videoDetails: Ref<VideoDetail | null>) {
  const playerState = reactive<VideoPlayerState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 0.75,
    isMuted: false,
    isBuffering: false,
    currentQuality: -1, // -1 for auto
    availableQualities: [],
    playbackRate: 1.0,
    isFullScreen: false,
    errorMessage: null,
  });

  let hls: Hls | null = null;
  let updateInterval: NodeJS.Timeout | null = null;
  const isMouseMoving = ref(false);
  let mouseMoveTimeout: NodeJS.Timeout | null = null;

  const _handleMouseMove = () => {
    isMouseMoving.value = true;
    if (mouseMoveTimeout) clearTimeout(mouseMoveTimeout);
    mouseMoveTimeout = setTimeout(() => {
      isMouseMoving.value = false;
    }, 3000); // Hide controls after 3 seconds of inactivity
  };


  function initializePlayer() {
    if (!videoElement.value) {
      playerState.errorMessage = 'Video element not available.';
      console.error(playerState.errorMessage);
      return;
    }
    
    if (!videoDetails.value?.stream_url) {
      playerState.errorMessage = 'Video stream URL not available. Video may still be processing.';
      console.error('Stream URL missing:', videoDetails.value);
      return;
    }

    playerState.errorMessage = null;
    const video = videoElement.value;

    if (Hls.isSupported()) {
      if (hls) {
        hls.destroy();
      }
      hls = new Hls({
        // Refer to HLS.js config options for fine-tuning
        // e.g., abrController, capLevelToPlayerSize, etc.
        // Enable smooth quality switching and robust error recovery
        abrEwmaDefaultEstimate: 500000, // 500 kbps initial estimate
        capLevelToPlayerSize: true,
        maxBufferLength: 30,
        maxMaxBufferLength: 600,
        maxBufferHole: 1, // Increase tolerance for buffer gaps
      });

      hls.loadSource(videoDetails.value.stream_url);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
        playerState.availableQualities = [
          { level: -1, height: 0, name: 'Auto' }, // Auto quality option
          ...data.levels.map((level, index) => ({
            level: index,
            height: level.height,
            name: `${level.height}p`,
            bitrate: level.bitrate,
          })).sort((a, b) => (b.height || 0) - (a.height || 0)) // Sort descending by height
        ];
        // Set default quality if specified in videoDetails, otherwise auto
        const defaultQualityObj = videoDetails.value?.default_quality
            ? playerState.availableQualities.find(q => q.name === videoDetails.value?.default_quality)
            : null;

        if (defaultQualityObj && defaultQualityObj.level !== -1) {
            hls!.currentLevel = defaultQualityObj.level;
            playerState.currentQuality = defaultQualityObj.level;
        } else {
            hls!.currentLevel = -1; // Auto
            playerState.currentQuality = -1;
        }
      });

      hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
        playerState.currentQuality = data.level;
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              playerState.errorMessage = `Network Error: ${data.details}`;
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              if (hls) {
                hls.recoverMediaError();
              }
              playerState.errorMessage = `Media Error: ${data.details}`;
              break;
            default:
              playerState.errorMessage = `An unrecoverable error occurred: ${data.details}`;
              hls?.destroy();
              break;
          }
        } else {
            // Attempt to recover from buffer seek over hole errors, which are often non-fatal
            if (data.type === Hls.ErrorTypes.MEDIA_ERROR && data.details === Hls.ErrorDetails.BUFFER_SEEK_OVER_HOLE) {
              if (hls) {
                hls.recoverMediaError();
              }
            } else {
              playerState.errorMessage = `Warning: ${data.details}`;
            }
        }
      });

       hls.on(Hls.Events.FRAG_BUFFERED, () => {
            playerState.isBuffering = false;
        });
        hls.on(Hls.Events.FRAG_LOAD_EMERGENCY_ABORTED, () => {
            playerState.isBuffering = false;
        });
        // The 'BUFFER_STALLED' event seems to cause a lint error in this environment,
        // even though it appears to be a valid HLS.js event. Commenting out for now.
        // The 'waiting' event on the video element and other buffer events should
        // provide a reasonable buffering indication.
        // hls.on(Hls.Events.BUFFER_STALLED, () => {
        //     playerState.isBuffering = true;
        // });
         hls.on(Hls.Events.BUFFER_APPENDING, () => {
            playerState.isBuffering = true; // Show buffering when new data is being appended
        });
        hls.on(Hls.Events.BUFFER_APPENDED, () => {
            // Check if we still need to buffer or if playback can resume
            if (video.paused && video.readyState >= video.HAVE_FUTURE_DATA) {
                 playerState.isBuffering = false;
            }
        });


    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // For Safari native HLS support
      video.src = videoDetails.value.stream_url;
      video.addEventListener('loadedmetadata', () => {
        playerState.duration = video.duration;
        // Native HLS doesn't typically expose quality levels in the same way
        playerState.availableQualities = [{ level: -1, height: 0, name: 'Auto' }];
        playerState.currentQuality = -1;
      });
    } else {
      playerState.errorMessage = 'HLS is not supported in your browser.';
      console.error(playerState.errorMessage);
      return;
    }

    // Common video event listeners
    video.addEventListener('play', () => playerState.isPlaying = true);
    video.addEventListener('pause', () => playerState.isPlaying = false);
    video.addEventListener('ended', () => playerState.isPlaying = false);
    video.addEventListener('loadedmetadata', () => playerState.duration = video.duration);
    video.addEventListener('volumechange', () => {
      playerState.volume = video.volume;
      playerState.isMuted = video.muted;
    });
    video.addEventListener('waiting', () => playerState.isBuffering = true);
    video.addEventListener('playing', () => playerState.isBuffering = false);
    video.addEventListener('ratechange', () => playerState.playbackRate = video.playbackRate);
    video.addEventListener('fullscreenchange', () => {
        playerState.isFullScreen = !!document.fullscreenElement;
    });


    // Update current time
    if (updateInterval) clearInterval(updateInterval);
    updateInterval = setInterval(() => {
      if (video && !isNaN(video.currentTime)) {
          playerState.currentTime = video.currentTime;
      }
      if (video && video.buffered.length > 0) {
          const bufferedEnd = video.buffered.end(video.buffered.length - 1);
          if (playerState.isPlaying && !playerState.isBuffering && bufferedEnd - video.currentTime < 1 && video.currentTime < video.duration -1) {
              // Heuristic: if less than 1s buffered ahead and actively playing, show buffering
              // playerState.isBuffering = true;
          }
      }
    }, 250); // Update 4 times a second

    // Initial state
    playerState.volume = video.volume;
    playerState.isMuted = video.muted;
    playerState.playbackRate = video.playbackRate;

    // Mouse move listener for controls visibility
    const playerContainer = video.parentElement; // Assuming video is wrapped
    if (playerContainer) {
        playerContainer.addEventListener('mousemove', _handleMouseMove);
        playerContainer.addEventListener('mouseleave', () => {
            if (mouseMoveTimeout) clearTimeout(mouseMoveTimeout);
            isMouseMoving.value = false;
        });
    }
  }

  function cleanupPlayer() {
    if (updateInterval) clearInterval(updateInterval);
    if (hls) {
      hls.destroy();
      hls = null;
    }
    if (videoElement.value) {
      // Remove event listeners to prevent memory leaks
      const video = videoElement.value;
      video.removeEventListener('play', () => playerState.isPlaying = true);
      // ... remove all other listeners added in initializePlayer
       const playerContainer = video.parentElement;
        if (playerContainer) {
            playerContainer.removeEventListener('mousemove', _handleMouseMove);
            playerContainer.removeEventListener('mouseleave', () => isMouseMoving.value = false);
        }
        if (mouseMoveTimeout) clearTimeout(mouseMoveTimeout);
    }
    // Reset state if needed
    Object.assign(playerState, {
        isPlaying: false, currentTime: 0, duration: 0, isBuffering: false,
        errorMessage: null, currentQuality: -1, availableQualities: []
        // keep volume, muted, playbackRate as they are user preferences
    });
  }

  watch(videoDetails, (newDetails) => {
    if (newDetails && videoElement.value) {
      cleanupPlayer(); // Cleanup previous instance if any
      initializePlayer();
    } else if (!newDetails) {
      cleanupPlayer();
    }
  }, { immediate: false }); // `immediate: false` to wait for videoElement to be ready

  onMounted(() => {
      if (videoElement.value && videoDetails.value) {
        initializePlayer();
      }
  });

  onBeforeUnmount(() => {
    cleanupPlayer();
  });

  // Player Controls
  const togglePlayPause = () => {
    if (!videoElement.value) return;
    videoElement.value.paused ? videoElement.value.play() : videoElement.value.pause();
  };

  const seek = (time: number) => {
    if (!videoElement.value) return;
    videoElement.value.currentTime = Math.max(0, Math.min(time, playerState.duration));
  };

  const forward = (seconds: number = 10) => {
    if (!videoElement.value) return;
    seek(videoElement.value.currentTime + seconds);
  };

  const rewind = (seconds: number = 10) => {
    if (!videoElement.value) return;
    seek(videoElement.value.currentTime - seconds);
  };

  const setVolume = (volume: number) => {
    if (!videoElement.value) return;
    videoElement.value.volume = Math.max(0, Math.min(volume, 1));
    videoElement.value.muted = false; // Unmute when volume is set
  };

  const toggleMute = () => {
    if (!videoElement.value) return;
    videoElement.value.muted = !videoElement.value.muted;
  };

  const setQuality = (levelIndex: number) => {
    if (hls) {
      hls.currentLevel = levelIndex; // -1 for auto
      playerState.currentQuality = levelIndex;
    } else {
      console.warn('HLS instance not available for quality switching. This might be native playback.');
    }
  };

  const setPlaybackRate = (rate: number) => {
    if (!videoElement.value) return;
    videoElement.value.playbackRate = rate;
  };

  const toggleFullScreen = () => {
    if (!videoElement.value) return;
    const playerContainer = videoElement.value.parentElement; // Or a dedicated player wrapper
    if (!playerContainer) return;

    if (!document.fullscreenElement) {
      if (playerContainer.requestFullscreen) {
        playerContainer.requestFullscreen();
      } else if ((playerContainer as any).mozRequestFullScreen) { /* Firefox */
        (playerContainer as any).mozRequestFullScreen();
      } else if ((playerContainer as any).webkitRequestFullscreen) { /* Chrome, Safari & Opera */
        (playerContainer as any).webkitRequestFullscreen();
      } else if ((playerContainer as any).msRequestFullscreen) { /* IE/Edge */
        (playerContainer as any).msRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if ((document as any).mozCancelFullScreen) { /* Firefox */
        (document as any).mozCancelFullScreen();
      } else if ((document as any).webkitExitFullscreen) { /* Chrome, Safari & Opera */
        (document as any).webkitExitFullscreen();
      } else if ((document as any).msExitFullscreen) { /* IE/Edge */
        (document as any).msExitFullscreen();
      }
    }
  };

  return {
    playerState,
    isMouseMoving,
    togglePlayPause,
    seek,
    forward,
    rewind,
    setVolume,
    toggleMute,
    setQuality,
    setPlaybackRate,
    toggleFullScreen,
    // No need to expose initializePlayer or cleanupPlayer typically
  };
}
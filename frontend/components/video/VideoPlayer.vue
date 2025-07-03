<template>
  <div
    ref="playerWrapperRef"
    class="relative w-full aspect-video border-2 border-primary-gray rounded-md bg-primary-dark text-primary-smoke select-none overflow-hidden group"
    @keydown.space.prevent="handleSpaceKey"
    @keydown.left.prevent="handleArrowLeft"
    @keydown.right.prevent="handleArrowRight"
    @click="handleClickOnPlayer"
    @dblclick="handleDoubleClickOnPlayer"
    tabindex="0"
  >

    <!-- Thumbnail -->
    <video ref="videoElementRef" class="w-full h-full" :poster="videoDetails?.thumbnail_urls?.large || videoDetails?.thumbnail_urls?.small"></video>

    <!-- Loading Spinner -->
    <div
      v-if="playerState.isBuffering && !playerState.errorMessage"
      class="absolute inset-0 flex items-center justify-center bg-primary-dark/30 z-10"
    >
      <UiSpinner size="large" color="white" />
    </div>

    <!-- Error Message -->
    <div
        v-if="playerState.errorMessage"
        class="absolute inset-0 flex flex-col items-center justify-center bg-primary-dark/80 z-20 p-4 text-center"
    >
        <ExclamationTriangleIcon class="h-12 w-12 text-primary-error mb-2"/>
        <p class="text-lg mb-1">A wild error appeared!</p>
        <p class="text-sm text-primary-silver">{{ playerState.errorMessage }}</p>
        <UiButton @click="retryLoad" variant="primary" size="sm" class="mt-4">Retry</UiButton>
    </div>

    <div
      :class="[
        'absolute inset-0 z-10 flex flex-col justify-between p-2 md:p-4 transition-opacity duration-300',
        (playerState.isPlaying && !isMouseMoving && !isDropdownOpen) ? 'opacity-0 group-hover:opacity-100' : 'opacity-100',
        playerState.errorMessage ? 'hidden' : ''
      ]"
    >
      <!-- Video title inside the player -->
      <div class="flex justify-between items-center">
        <h3 v-if="videoDetails?.title" class="text-sm md:text-lg font-semibold truncate drop-shadow-md">
          {{ videoDetails.title }}
        </h3>
        <div></div>
      </div>

      <!-- Video play button middle of the player -->
      <div class="absolute inset-0 flex items-center justify-center" v-if="!playerState.isPlaying && isMouseMoving">
           <button @click.stop="togglePlayPause" class="p-4 bg-primary-dark/30 rounded-full hover:bg-primary-red/50 transition-colors">
               <PlayIcon class="h-10 w-10 md:h-16 md:w-16 text-primary-smoke" />
           </button>
       </div>


      <!-- Video play progress and controls -->
      <div class="space-y-1 md:space-y-2">
        <!-- Video play progress -->
        <div class="relative group/timeline h-5 flex items-center cursor-pointer" @click.stop="handleTimelineClick">
            <div class="absolute w-full h-1 md:h-1.5 bg-primary-red/30 rounded-full top-1/2 -translate-y-1/2">
                <div
                    class="absolute h-full bg-primary-red/70 rounded-full"
                    :style="{ width: `${(playerState.currentTime / playerState.duration) * 100}%` }"
                ></div>
                 <div
                    class="absolute h-full bg-primary-red rounded-full"
                    :style="{ width: `${(playerState.currentTime / playerState.duration) * 100}%` }"
                ></div>
            </div>
             <div
                class="absolute h-3 w-3 md:h-3.5 md:w-3.5 bg-primary-red rounded-full top-1/2 -translate-y-1/2 -translate-x-1/2 scale-0 group-hover/timeline:scale-100 transition-transform"
                :style="{ left: `${(playerState.currentTime / playerState.duration) * 100}%` }"
             ></div>
        </div>


        <!-- Video play progress -->
        <div class="flex items-center justify-between text-xs md:text-sm">
          <!-- Left -->
          <div class="flex items-center gap-2 md:gap-4">

            <!-- Play/Pause button -->
            <UiButton variant="icon" @click.stop="togglePlayPause" class="p-1 z-10 md:p-2 hover:text-primary-red bg-opacity-0 ">
              <PlayIcon v-if="!playerState.isPlaying" class="h-5 w-5 md:h-6 md:w-6" />
              <PauseIcon v-else class="h-5 w-5 md:h-6 md:w-6" />
            </UiButton>

            <!-- Forward button -->
            <UiButton v-if="onNextVideo" variant="icon" @click.stop="onNextVideo" class="p-1 z-10 md:p-2 hover:text-primary-red bg-opacity-0">
              <ForwardIcon class="h-5 w-5 md:h-6 md:w-6" />
            </UiButton>

            <!-- Volume  -->
            <div class="flex items-center group/volume relative">
              <UiButton variant="icon" @click.stop="toggleMute" class="p-1 z-10 md:p-2 hover:text-primary-red bg-opacity-0">
                <SpeakerWaveIcon v-if="!playerState.isMuted && playerState.volume > 0.5" class="h-5 w-5 md:h-6 md:w-6" />
                <SpeakerXMarkIcon v-else-if="playerState.isMuted" class="h-5 w-5 md:h-6 md:w-6" />
                <SpeakerWaveIcon v-else-if="playerState.volume > 0" class="h-5 w-5 md:h-6 md:w-6 opacity-70" />
                 <SpeakerXMarkIcon v-else class="h-5 w-5 md:h-6 md:w-6" />
              </UiButton>
              <div class="relative overflow-visible">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  :value="playerState.volume"
                  @input.stop="e => setVolume(parseFloat((e.target as HTMLInputElement).value))"
                  class="w-0 group-hover/volume:w-16 md:group-hover/volume:w-20 h-1.5 transition-all duration-200 ml-1 cursor-pointer slider-red"
                />
              </div>
            </div>

            <!-- Time -->
            <div class="text-primary-smoke/80">
              {{ formatTime(playerState.currentTime) }} / {{ formatTime(playerState.duration) }}
            </div>
          </div>

          <!-- Right -->
          <div class="flex items-center gap-2 md:gap-3">
            <!-- Resolution Settings -->
            <UiDropdown v-if="playerState.availableQualities.length > 1" origin="top" align="right" variant="transparent" @update:modelValue="val => isDropdownOpen = val">
              <template #trigger="{ toggle, isOpen }">
                <UiButton variant="icon" @click.stop="toggle" class="p-1 z-10 md:p-2 hover:text-primary-red bg-opacity-0">
                  <Cog6ToothIcon class="h-5 w-5 md:h-6 md:w-6" />
                </UiButton>
              </template>
              <template #default="{ close, variant }">
                 <button
                    v-for="quality in playerState.availableQualities"
                    :key="quality.level"
                    @click.stop="() => { setQuality(quality.level); close(); }"
                    :class="[
                        'block w-full text-left px-4 py-2 text-xs md:text-sm transition-colors',
                        variant === 'transparent' ? 'hover:bg-primary-red/20' : 'hover:bg-background-light',
                        playerState.currentQuality === quality.level ? 'text-primary-red font-semibold' : 'text-primary-smoke'
                    ]"
                    role="menuitem"
                 >
                    {{ quality.name }} <span v-if="quality.bitrate" class="text-primary-silver text-xs">({{ (quality.bitrate / 1000000).toFixed(1) }} Mbps)</span>
                 </button>
              </template>
            </UiDropdown>

            <!-- Playback Rate -->
            <UiDropdown origin="top" align="right" variant="transparent" @update:modelValue="val => isDropdownOpen = val">
                <template #trigger="{ toggle }">
                    <UiButton variant="icon" @click.stop="toggle" class="p-1 z-10 md:p-2 min-w-[3rem] text-center hover:text-primary-red bg-opacity-0">
                        {{ playerState.playbackRate.toFixed(1) }}x
                    </UiButton>
                </template>
                <template #default="{ close, variant }">
                    <button
                        v-for="rate in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]"
                        :key="rate"
                        @click.stop="() => { setPlaybackRate(rate); close(); }"
                        :class="[
                            'block w-full text-left px-4 py-2 text-xs md:text-sm transition-colors',
                            variant === 'transparent' ? 'hover:bg-primary-red/20' : 'hover:bg-background-light',
                            playerState.playbackRate === rate ? 'text-primary-red font-semibold' : 'text-primary-smoke'
                        ]"
                        role="menuitem"
                    >
                        {{ rate.toFixed(2) }}x
                    </button>
                </template>
            </UiDropdown>

            <!-- Fullscreen Button -->
            <UiButton variant="icon" @click.stop="toggleFullScreen" class="p-1 z-10 md:p-2 hover:text-primary-red bg-opacity-0">
              <ArrowsPointingOutIcon v-if="!playerState.isFullScreen" class="h-5 w-5 md:h-6 md:w-6" />
              <ArrowsPointingInIcon v-else class="h-5 w-5 md:h-6 md:w-6" />
            </UiButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useHlsPlayer } from '~/composables/useHlsPlayer';
import type { VideoDetail } from '~/types/api';
import UiButton from '~/components/ui/Button.vue';
import UiDropdown from '~/components/ui/Dropdown.vue';
import UiSpinner from '~/components/ui/Spinner.vue';
import {
  PlayIcon, PauseIcon, ForwardIcon, SpeakerWaveIcon, SpeakerXMarkIcon, Cog6ToothIcon,
  ArrowsPointingOutIcon, ArrowsPointingInIcon, ExclamationTriangleIcon
} from '@heroicons/vue/24/outline';

const props = defineProps<{
  videoDetails: VideoDetail | null;
  onNextVideo?: () => void;
  onPreviousVideo?: () => void; // Not used in UI yet but good to have
}>();

const emit = defineEmits(['playerError']);

const videoElementRef = ref<HTMLVideoElement | null>(null);
const playerWrapperRef = ref<HTMLElement | null>(null);
const isDropdownOpen = ref(false); // To keep controls visible when a dropdown is open

const {
  playerState, isMouseMoving,
  togglePlayPause, seek, forward: seekForward, rewind: seekRewind,
  setVolume, toggleMute, setQuality, setPlaybackRate, toggleFullScreen
} = useHlsPlayer(videoElementRef, computed(() => props.videoDetails));

watch(() => playerState.errorMessage, (newError) => {
    if (newError) {
        emit('playerError', newError);
    }
});

const formatTime = (timeInSeconds: number): string => {
  if (isNaN(timeInSeconds) || timeInSeconds < 0) return '00:00';
  const flooredTime = Math.floor(timeInSeconds);
  const hours = Math.floor(flooredTime / 3600);
  const minutes = Math.floor((flooredTime % 3600) / 60);
  const seconds = flooredTime % 60;

  const paddedMinutes = String(minutes).padStart(2, '0');
  const paddedSeconds = String(seconds).padStart(2, '0');

  if (hours > 0) {
    return `${hours}:${paddedMinutes}:${paddedSeconds}`;
  }
  return `${paddedMinutes}:${paddedSeconds}`;
};

const handleTimelineClick = (event: MouseEvent) => {
  if (!videoElementRef.value || !playerState.duration) return;
  const timeline = event.currentTarget as HTMLElement;
  const rect = timeline.getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const percentage = clickX / rect.width;
  seek(playerState.duration * percentage);
};

// Keyboard controls
const handleSpaceKey = () => togglePlayPause();
const handleArrowLeft = () => seekRewind(5); // Rewind 5 seconds
const handleArrowRight = () => seekForward(5); // Forward 5 seconds

let lastClickTime = 0;
const handleClickOnPlayer = (event: MouseEvent) => {
    // Prevent click on controls from toggling play/pause
    const target = event.target as HTMLElement;
    if (target.closest('button, input[type="range"], .group\\/timeline, .group\\/volume')) {
        return;
    }
    const currentTime = new Date().getTime();
    if (currentTime - lastClickTime < 300) { // Double click threshold
        // This is handled by dblclick, so do nothing here to avoid conflict
    } else {
        // Single click
        togglePlayPause();
    }
    lastClickTime = currentTime;
};

const handleDoubleClickOnPlayer = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (target.closest('button, input[type="range"], .group\\/timeline, .group\\/volume')) {
        return; // Don't toggle fullscreen if clicking on controls
    }

    if (playerWrapperRef.value) {
        const rect = playerWrapperRef.value.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const third = rect.width / 3;

        if (clickX < third) { // Double click on left third
            seekRewind(10);
        } else if (clickX > rect.width - third) { // Double click on right third
            seekForward(10);
        } else { // Double click on center third
            toggleFullScreen();
        }
    }
};

const retryLoad = () => {
    playerState.errorMessage = null;
    playerState.isBuffering = true; // Show spinner while retrying
    // The useHlsPlayer composable's watch on videoDetails should re-initialize
    // If videoDetails hasn't changed, we might need a more direct re-initiation method in the composable.
    // For now, we assume the source is still the same and hls.js might recover or re-fetch.
    // A more robust retry might involve hls.loadSource(url) again.
    const currentVideoDetails = props.videoDetails; // copy current details
    // Temporarily set to null then back to trigger re-initialization if videoDetails is a ref watched by useHlsPlayer
    // This is a bit of a hack. A better way would be an explicit retry function in useHlsPlayer.
    if (videoElementRef.value && currentVideoDetails) {
        const hlsInstance = (videoElementRef.value as any).hls; // Access HLS instance if directly attached
        if (hlsInstance && typeof hlsInstance.loadSource === 'function') {
             hlsInstance.loadSource(currentVideoDetails.stream_url);
        } else {
            videoElementRef.value.load(); // General HTML5 video reload
        }
    }
};

onMounted(() => {
  playerWrapperRef.value?.focus(); // For keyboard controls
});
</script>

<style scoped>
/* Custom red volume slider styling */
.slider-red {
  background: transparent;
  -webkit-appearance: none;
  appearance: none;
}

.slider-red::-webkit-slider-track {
  background: rgba(179, 0, 61, 0.3); /* primary-red/30 */
  height: 6px;
  border-radius: 3px;
  border: none;
  outline: none;
}

/* Show track only when volume group is hovered */
.slider-red::-webkit-slider-track {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.group\/volume:hover .slider-red::-webkit-slider-track {
  opacity: 1;
}

.slider-red::-webkit-slider-thumb {
  background: #b3003d; /* primary-red */
  height: 14px;
  width: 14px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.group\/volume:hover .slider-red::-webkit-slider-thumb {
  opacity: 1;
}

.slider-red::-webkit-slider-thumb:hover {
  background: #d1004a; /* lighter red on hover */
  transform: scale(1.1);
}

.slider-red::-moz-range-track {
  background: rgba(179, 0, 61, 0.3); /* primary-red/30 */
  height: 6px;
  border-radius: 3px;
  border: none;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.group\/volume:hover .slider-red::-moz-range-track {
  opacity: 1;
}

.slider-red::-moz-range-thumb {
  background: #b3003d; /* primary-red */
  height: 14px;
  width: 14px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.group\/volume:hover .slider-red::-moz-range-thumb {
  opacity: 1;
}

.slider-red::-moz-range-thumb:hover {
  background: #d1004a; /* lighter red on hover */
  transform: scale(1.1);
}
</style>

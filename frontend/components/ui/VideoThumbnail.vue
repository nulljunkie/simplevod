<template>
  <div class="relative group border border-primary-gray rounded-lg overflow-hidden aspect-[16/9]">
    <!-- Thumbnail image -->
    <img
      v-if="thumbnailUrl && !imageError"
      :src="thumbnailUrl"
      :alt="title"
      class="w-full h-full object-cover"
      loading="lazy"
      @error="handleImageError"
    />
    <!-- Video icon if there is no thumbnail -->
    <div
      v-else
      class="w-full h-full flex items-center justify-center"
    >
      <VideoCameraIcon class="h-16 w-16 md:h-20 md:w-20 text-primary-silver" />
    </div>

    <!-- Video duration -->
    <div v-if="duration" class="absolute bottom-2 right-2 bg-primary-dark/80 text-primary-smoke text-xs px-2 py-1 rounded font-medium">
      {{ formatDuration(duration) }}
    </div>

    <!-- Play icon on hover -->
    <div class="absolute inset-0 bg-primary-dark/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
      <PlayIcon class="h-12 w-12 md:h-16 md:w-16 text-primary-smoke drop-shadow-lg" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlayIcon } from '@heroicons/vue/24/solid';
import { VideoCameraIcon } from '@heroicons/vue/24/outline';

interface Props {
  thumbnailUrl?: string;
  title: string;
  duration?: number;
}
const props = defineProps<Props>();

const imageError = ref(false);

const handleImageError = () => {
  imageError.value = true;
};

const formatDuration = (totalSeconds: number): string => {
  if (isNaN(totalSeconds) || totalSeconds < 0) return '0:00';
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);

  const paddedMinutes = String(minutes).padStart(2, '0');
  const paddedSeconds = String(seconds).padStart(2, '0');

  if (hours > 0) {
    return `${hours}:${paddedMinutes}:${paddedSeconds}`;
  }
  return `${minutes}:${paddedSeconds}`;
};
</script>

<template>
  <div class="relative bg-primary-dark border border-primary-gray rounded-lg p-3 sm:p-6">
    <div class="flex flex-col sm:flex-row items-start space-y-4 sm:space-y-0 sm:space-x-6">
      <!-- Thumbnail -->
      <div class="flex-shrink-0 w-full sm:w-auto">
        <UiVideoThumbnail
          :thumbnail-url="video.thumbnail_url"
          :title="video.title"
          :duration="video.duration_seconds"
          class="w-full h-32 sm:w-48 sm:h-32"
        />
      </div>

      <!-- Video Details -->
      <div class="flex-1 space-y-4">
        <!-- Title with Edit Icon -->
        <div class="flex items-center space-x-2">
          <h3 class="text-lg font-semibold text-primary-smoke" :title="video.title">
            {{ video.title }}
          </h3>
          <button
            v-if="canEdit"
            @click="$emit('edit', video)"
            class="p-1 hover:bg-primary-gray rounded"
            title="Edit title"
          >
            <EditIcon class="w-4 h-4 text-primary-silver" />
          </button>
        </div>

        <!-- File Info Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-8 text-sm">
          <div>
            <span class="text-primary-silver">filename: </span>
            <span class="text-primary-smoke">{{ video.original_filename || 'video.mp4' }}</span>
          </div>
          <div>
            <span class="text-primary-silver">status: </span>
            <StatusBadge :status="videoStatus" />
          </div>
        </div>

        <!-- Duration and Upload Time Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-8 text-sm">
          <div>
            <span class="text-primary-silver">duration: </span>
            <span class="text-primary-smoke">{{ formatDuration(video.duration_seconds) }}</span>
          </div>
          <div>
            <span class="text-primary-silver">uploaded: </span>
            <span class="text-primary-smoke">{{ timeAgo(video.uploaded_at) }}</span>
          </div>
        </div>

        <!-- Visibility -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
          <span class="text-primary-silver text-sm">visibility:</span>
          <div class="flex items-center space-x-4">
            <label class="flex items-center space-x-2 cursor-pointer">
              <input 
                type="radio" 
                :checked="video.visibility === 'public'"
                @change="updateVisibility('public')"
                class="w-4 h-4"
              />
              <span class="text-sm text-primary-smoke">Public</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer">
              <input 
                type="radio" 
                :checked="video.visibility === 'private'"
                @change="updateVisibility('private')"
                class="w-4 h-4"
              />
              <span class="text-sm text-primary-smoke">Private</span>
            </label>
          </div>
        </div>

        <!-- Description -->
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <span class="text-primary-silver text-sm">Description:</span>
            <button
              v-if="canEdit"
              @click="$emit('edit', video)"
              class="p-1 hover:bg-primary-gray rounded"
              title="Edit description"
            >
              <EditIcon class="w-3 h-3 text-primary-silver" />
            </button>
          </div>
          <p class="text-sm text-primary-smoke leading-relaxed">
            {{ video.description || 'No description provided' }}
            <button v-if="video.description && video.description.length > 100" class="text-primary-blue ml-1">
              more
            </button>
          </p>
        </div>
      </div>

      <!-- Delete Button -->
      <div class="flex-shrink-0 absolute top-3 right-3 sm:static">
        <button
          v-if="canDelete"
          @click="$emit('delete', video)"
          class="p-2 hover:bg-primary-gray rounded"
          title="Delete video"
        >
          <TrashIcon class="w-5 h-5 text-primary-silver hover:text-primary-red" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { VideoListItem } from '~/types/api';
import StatusBadge from '~/components/upload/StatusBadge.vue';
import EditIcon from '~/components/icons/EditIcon.vue';
import TrashIcon from '~/components/icons/TrashIcon.vue';

interface Props {
  video: VideoListItem & { status?: string; file_size?: number; };
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'edit', video: VideoListItem): void;
  (e: 'delete', video: VideoListItem): void;
  (e: 'update-visibility', video: VideoListItem, visibility: 'public' | 'private'): void;
}>();

const videoStatus = computed(() => {
  return props.video.status || 'published';
});

const canEdit = computed(() => {
  return ['published', 'failed'].includes(videoStatus.value);
});

const canDelete = computed(() => {
  return true;
});

const formatViews = (views: number): string => {
  if (views >= 1_000_000) return `${(views / 1_000_000).toFixed(1)}M`;
  if (views >= 1_000) return `${(views / 1_000).toFixed(1)}K`;
  return String(views);
};

const formatFileSize = (size: number | undefined): string => {
  if (!size) return 'Unknown size';
  
  const units = ['B', 'KB', 'MB', 'GB'];
  let unitIndex = 0;
  let fileSize = size;
  
  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024;
    unitIndex++;
  }
  
  return `${fileSize.toFixed(1)} ${units[unitIndex]}`;
};

const timeAgo = (dateString: string): string => {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);
  const weeks = Math.round(days / 7);
  const months = Math.round(days / 30.44);
  const years = Math.round(days / 365.25);

  if (seconds < 60) return `${seconds} sec ago`;
  if (minutes < 60) return `${minutes} min ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  if (weeks < 5) return `${weeks}w ago`;
  if (months < 12) return `${months}mo ago`;
  return `${years}y ago`;
};

const formatDuration = (seconds: number | undefined): string => {
  if (!seconds) return 'Unknown';
  
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const updateVisibility = (visibility: 'public' | 'private') => {
  emit('update-visibility', props.video, visibility);
};
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

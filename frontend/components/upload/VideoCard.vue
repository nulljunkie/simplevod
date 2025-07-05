<template>
  <div class="group block">
    <div class="space-y-3">
      <div class="relative">
        <UiVideoThumbnail
          :thumbnail-url="video.thumbnail_url"
          :title="video.title"
          :duration="video.duration_seconds"
        />
        
        <div class="absolute top-2 right-2">
          <StatusBadge :status="videoStatus" />
        </div>
      </div>

      <div class="space-y-2">
        <div class="flex items-start justify-between">
          <h3 class="text-sm font-semibold text-primary-smoke line-clamp-2 leading-snug flex-1" :title="video.title">
            {{ video.title }}
          </h3>
          
          <div class="flex items-center space-x-2 ml-2">
            <button
              v-if="canEdit"
              @click="$emit('edit', video)"
              class="p-1 hover:bg-primary-gray rounded"
              title="Edit video"
            >
              <EditIcon class="w-4 h-4 text-primary-silver" />
            </button>
            
            <button
              v-if="canDelete"
              @click="$emit('delete', video)"
              class="p-1 hover:bg-primary-gray rounded"
              title="Delete video"
            >
              <TrashIcon class="w-4 h-4 text-primary-silver hover:text-primary-red" />
            </button>
          </div>
        </div>
        
        <div class="space-y-1">
          <div class="flex items-center justify-between text-xs text-primary-silver">
            <span>{{ formatFileSize(video.file_size) }}</span>
            <span>{{ video.visibility }}</span>
          </div>
          
          <div class="flex items-center justify-between text-xs text-primary-silver">
            <span>{{ formatViews(video.views_count) }} views</span>
            <span>{{ timeAgo(video.published_at) }}</span>
          </div>
        </div>
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
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);
  const weeks = Math.round(days / 7);
  const months = Math.round(days / 30.44);
  const years = Math.round(days / 365.25);

  if (seconds < 60) return `${seconds}s ago`;
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  if (weeks < 5) return `${weeks}w ago`;
  if (months < 12) return `${months}mo ago`;
  return `${years}y ago`;
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
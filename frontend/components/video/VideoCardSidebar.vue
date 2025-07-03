<template>
  <NuxtLink :to="`/watch/${video.id}`" class="group flex gap-4 p-2 rounded-lg">
    <!-- Thumbnail Section -->
    <div class="flex-shrink-0 w-28 sm:w-32">
      <UiVideoThumbnail
        :thumbnail-url="video.thumbnail_url"
        :title="video.title"
        :duration="video.duration_seconds"
      />
    </div>
    
    <!-- Info Section -->
    <div class="flex-1 min-w-0 space-y-1">
      <h3 class="text-sm font-medium text-primary-smoke group-hover:text-primary-smoke transition-colors duration-200 line-clamp-2 leading-snug" :title="video.title">
        {{ video.title }}
      </h3>
      
      <UiVideoOwner
        :username="video.uploader?.username || video.uploader_username || `User ${video.uploader_id}`"
        :avatar-url="video.uploader?.avatar_url"
        size="xs"
        :show-username="true"
      />
      
      <div class="flex items-center space-x-2 text-xs text-primary-silver">
        <span>{{ formatViews(video.views_count) }} views</span>
        <span>&bull;</span>
        <span>{{ timeAgo(video.published_at) }}</span>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import type { VideoListItem } from '~/types/api';

defineProps<{
  video: VideoListItem;
}>();

const formatViews = (views: number): string => {
  if (views >= 1_000_000) return `${(views / 1_000_000).toFixed(1)}M`;
  if (views >= 1_000) return `${(views / 1_000).toFixed(1)}K`;
  return String(views);
};

const timeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);

  if (seconds < 60) return `${seconds}s`;
  if (minutes < 60) return `${minutes}m`;
  if (hours < 24) return `${hours}h`;
  if (days < 7) return `${days}d`;
  return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
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

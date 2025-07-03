<template>
    <NuxtLink :to="`/watch/${video.id}`" class="group block">
    <div class="space-y-3">
      <!-- Thumbnail Section -->

      <UiVideoThumbnail
        :thumbnail-url="video.thumbnail_url"
        :title="video.title"
        :duration="video.duration_seconds"
      />

      <!-- Info Section -->
      <div class="space-y-2 ">
        <!-- Video title -->
        <h3 class="text-sm font-semibold text-primary-smoke group-hover:text-primary-smoke transition-colors duration-200 line-clamp-2 leading-snug" :title="video.title">
          {{ video.title }}
        </h3>
        
        <!-- User -->
        <UiVideoOwner
          :username="video.uploader?.username || video.uploader_username || `User ${video.uploader_id}`"
          :avatar-url="video.uploader?.avatar_url"
          size="sm"
          :show-username="true"
        />
        
        <!-- Views and upload date -->
        <div class="flex items-center space-x-2 text-xs text-primary-silver">
          <span>{{ formatViews(video.views_count) }} views</span>
          <span>&bull;</span>
          <span>{{ timeAgo(video.published_at) }}</span>
        </div>
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

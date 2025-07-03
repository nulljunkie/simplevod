<template>
  <div class="container mx-auto px-4 py-6">
    <Head>
      <Title>{{ videosStore.currentVideo?.title || 'Watch Video' }}</Title>
      <Meta v-if="videosStore.currentVideo?.description" name="description" :content="videosStore.currentVideo.description.substring(0, 150)" />
    </Head>

    <!-- Loading -->
    <div v-if="videosStore.isLoadingDetail" class="flex flex-col items-center justify-center py-20">
      <UiSpinner size="large" />
      <p class="mt-4 text-text-muted">Loading video...</p>
    </div>
    
    <!-- Errors -->
    <div v-else-if="videosStore.error && !videosStore.currentVideo" class="text-center py-20">
      <ExclamationTriangleIcon class="h-16 w-16 text-primary-silver-red mx-auto mb-4" />
      <p class="text-xl text-primary-smoke mb-2">Could not load video</p>
      <p class="text-primary-silver mb-6">{{ videosStore.error }}</p>
      <NuxtLink to="/">
        <UiButton variant="primary">Go to Homepage</UiButton>
      </NuxtLink>
    </div>
    
    <div v-else-if="videosStore.currentVideo" class="flex flex-col lg:flex-row gap-6">
      <!-- Main Video Section -->
      <div class="flex-1 lg:max-w-4xl">
        <!-- Video player -->
        <div class="mb-4">
          <VideoPlayer
            :video-details="videosStore.currentVideo"
            :on-next-video="playNextVideo"
            @player-error="handlePlayerError"
          />
        </div>

        <!-- Video info -->
        <div>
          <!-- Video title -->
          <h1 class="text-xl md:text-2xl font-bold text-primary-smoke mb-2">{{ videosStore.currentVideo.title }}</h1>
          
          <!-- Video engagement -->
          <div class="flex items-center justify-between mb-4">
            <!-- Views and upload date -->
            <div class="flex items-center space-x-3 text-sm text-primary-silver">
              <span>{{ formatViews(videosStore.currentVideo.views_count) }} views</span>
              <span>&bull;</span>
              <span>{{ timeAgo(videosStore.currentVideo.published_at) }}</span>
            </div>
            
            <!-- Engagement buttons -->
            <div class="flex items-center space-x-2">
              <UiButton variant="secondary" size="sm">
                <HandThumbUpIcon class="h-4 w-4 mr-1" /> {{ videosStore.currentVideo.likes_count || 12 }}
              </UiButton>
              <UiButton variant="secondary" size="sm">
                <HandThumbDownIcon class="h-4 w-4 mr-1" /> 5
              </UiButton>
              <UiButton variant="secondary" size="sm">
                <ShareIcon class="h-4 w-4" />
              </UiButton>
              <UiButton variant="secondary" size="sm">Subscribe</UiButton>
            </div>
          </div>

          <!-- Video owner -->
          <div class="flex items-center mb-4">
            <UiVideoOwner
              :username="videosStore.currentVideo.uploader?.username || `User ${videosStore.currentVideo.uploader_id}`"
              :avatar-url="videosStore.currentVideo.uploader?.avatar_url"
              size="md"
              :show-username="true"
            />
          </div>

          <!-- Video description -->
          <div class="bg-primary-gray/40 p-4 rounded-lg">
            <p class="text-sm text-primary-smoke whitespace-pre-wrap leading-relaxed">
              {{ videosStore.currentVideo.description || 'The videos description should be here, telling things that don\'t matter at all, here\'s the discription, this a placeholder, not the actually description, just an example' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Sidebar Section -->
      <div class="lg:w-80 xl:w-96">
        <div class="space-y-3">
          <VideoCardSidebar 
            v-for="video in recommendedVideos" 
            :key="video.id" 
            :video="video" 
          />
        </div>
      </div>
    </div>
    
    <div v-else class="text-center py-20">
      <p class="text-primary-silver">Video not found.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useVideosStore } from '~/stores/videos';
import VideoPlayer from '~/components/video/VideoPlayer.vue';
import VideoCardSidebar from '~/components/video/VideoCardSidebar.vue';
import UiButton from '~/components/ui/Button.vue';
import UiSpinner from '~/components/ui/Spinner.vue';
import UiVideoOwner from '~/components/ui/VideoOwner.vue';
import {
    ExclamationTriangleIcon, HandThumbUpIcon, HandThumbDownIcon, ShareIcon
} from '@heroicons/vue/24/outline';

const route = useRoute();
const router = useRouter();
const videosStore = useVideosStore();

const videoId = computed(() => route.params.id as string);

const fetchVideo = async () => {
  if (videoId.value) {
    await videosStore.fetchVideoById(videoId.value);
  }
};

const recommendedVideos = computed(() => {
  return videosStore.videos.filter(video => video.id !== videoId.value).slice(0, 8);
});

// Fetch video when component mounts or videoId changes
onMounted(fetchVideo);
watch(videoId, fetchVideo);

// Clear current video when navigating away from this page
onBeforeUnmount(() => {
    videosStore.clearCurrentVideo();
});

const playNextVideo = () => {
  const nextId = videosStore.getNextVideoId(videoId.value);
  if (nextId) {
    router.push(`/watch/${nextId}`);
  } else {
    // Handle no next video, e.g., show a message or go to homepage
    console.log('No next video in current list.');
    // Optionally: fetch next page of videos and then play the first one.
  }
};

const handlePlayerError = (errorMessage: string) => {
    console.error("Player error received in page:", errorMessage);
    // You could show a toast notification or update a local error state here
    // The VideoPlayer component itself already shows an error message.
};

const formatViews = (views: number): string => {
  if (views >= 1_000_000) return `${(views / 1_000_000).toFixed(1)}M`;
  if (views >= 1_000) return `${(views / 1_000).toFixed(0)}K`; // No decimal for views under 1M for cleaner look
  return String(views);
};

const timeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
  if (seconds < 5) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 1) return `${seconds} seconds ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 1) return `${minutes} minutes ago`;
  const days = Math.round(hours / 24);
  if (days < 1) return `${hours} hours ago`;
  if (days < 7) return `${days} days ago`;

  // For older dates, show simple date format
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// Ensure the page scrolls to the top when navigating between video watch pages
watch(() => route.fullPath, () => {
    if (process.client) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});
</script>

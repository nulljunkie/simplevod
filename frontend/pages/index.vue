<template>
  <div class="container mx-auto px-4 py-6">
    <Head>
      <Title>Home</Title>
      <Meta name="description" content="Upload and watch unlimited videos" />
    </Head>

    <ErrorState 
      v-if="videosStore.error" 
      :message="videosStore.error"
      retry-text="Try Again"
      @retry="fetchVideosData"
    />
    
    <EmptyState 
      v-else-if="videosStore.videos.length === 0 && !videosStore.isLoadingList"
      message="No videos found. Why not upload one?"
    />
    
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <template v-if="videosStore.isLoadingList">
        <VideoCardSkeleton v-for="n in 12" :key="`skeleton-${n}`" />
      </template>
      <template v-else>
        <VideoCard v-for="video in videosStore.videos" :key="video.id" :video="video" />
      </template>
    </div>

    <Pagination
      v-if="!videosStore.isLoadingList"
      :current-page="videosStore.pagination.page"
      :total-pages="videosStore.pagination.totalPages"
      @page-change="changePage"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useVideosStore } from '~/stores/videos';
import VideoCard from '~/components/video/VideoCard.vue';
import VideoCardSkeleton from '~/components/video/VideoCardSkeleton.vue';
import ErrorState from '~/components/ui/ErrorState.vue';
import EmptyState from '~/components/ui/EmptyState.vue';
import Pagination from '~/components/ui/Pagination.vue';

const videosStore = useVideosStore();
const route = useRoute();
const router = useRouter();

const currentPage = computed(() => parseInt(route.query.page as string) || 1);
const currentLimit = computed(() => parseInt(route.query.limit as string) || 12);

const fetchVideosData = async (page = currentPage.value, limit = currentLimit.value) => {
  await videosStore.fetchVideos(page, limit);
};

const changePage = (newPage: number) => {
  if (newPage > 0 && newPage <= videosStore.pagination.totalPages) {
    router.push({ query: { ...route.query, page: newPage } });
    // fetchVideosData will be called by the watcher
  }
};

onMounted(() => {
  fetchVideosData();
});

// Watch for query changes to re-fetch videos for pagination
watch(
  () => route.query,
  async (newQuery, oldQuery) => {
    if (newQuery.page !== oldQuery?.page || newQuery.limit !== oldQuery?.limit) {
      await fetchVideosData(parseInt(newQuery.page as string) || 1, parseInt(newQuery.limit as string) || 12);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  },
  { deep: true }
);

// Clear current video when navigating away from watch page to home.
// This is more of a global concern, could be in a layout or app.vue watcher.
onBeforeUnmount(() => {
    // This is not the best place, currentVideo should be cleared when leaving /watch/[id]
    // videosStore.clearCurrentVideo();
});
</script>

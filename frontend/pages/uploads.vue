<template>
  <div class="container mx-auto px-4 py-6">
    <Head>
      <Title>Your Uploads</Title>
      <Meta name="description" content="Manage your uploaded videos" />
    </Head>

    <div class="mb-6">
      <h1 class="text-2xl font-bold text-primary-smoke mb-2">Your Uploads</h1>
      <p class="text-primary-silver">Manage and view your uploaded videos</p>
    </div>

    <ErrorState 
      v-if="videosStore.error" 
      :message="videosStore.error"
      retry-text="Try Again"
      @retry="fetchUploadsData"
    />
    
    <EmptyState 
      v-else-if="videosStore.videos.length === 0 && !videosStore.isLoadingList"
      message="No videos uploaded yet. Upload your first video!"
    />
    
    <div v-else class="space-y-4">
      <template v-if="videosStore.isLoadingList">
        <UploadVideoCardSkeleton v-for="n in 5" :key="`skeleton-${n}`" />
      </template>
      <template v-else>
        <UploadVideoCard v-for="video in videosStore.videos" :key="video.id" :video="video" />
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
import { onMounted, onUnmounted, watch, computed, nextTick } from 'vue';
import { useVideosStore } from '~/stores/videos';
import { useAuthStore } from '~/stores/auth';
import { useUploadsStore } from '~/stores/uploads';
import { useStatusPolling } from '~/composables/useStatusPolling';
import UploadVideoCard from '~/components/upload/VideoCard.vue';
import UploadVideoCardSkeleton from '~/components/upload/VideoCardSkeleton.vue';
import ErrorState from '~/components/ui/ErrorState.vue';
import EmptyState from '~/components/ui/EmptyState.vue';
import Pagination from '~/components/ui/Pagination.vue';

definePageMeta({
  middleware: 'auth-required'
});

const videosStore = useVideosStore();
const authStore = useAuthStore();
const uploadsStore = useUploadsStore();
const route = useRoute();
const router = useRouter();
const { startPolling, stopPolling, getProcessingVideoIds } = useStatusPolling();

const currentPage = computed(() => parseInt(route.query.page as string) || 1);
const currentLimit = computed(() => parseInt(route.query.limit as string) || 12);

const fetchUploadsData = async (page = currentPage.value, limit = currentLimit.value) => {
  await videosStore.fetchMyVideos(page, limit);
  
  nextTick(() => {
    const processingVideoIds = getProcessingVideoIds();
    if (processingVideoIds.length > 0) {
      startPolling(processingVideoIds, 3000);
    } else {
      stopPolling();
    }
  });
};

const changePage = (newPage: number) => {
  if (newPage > 0 && newPage <= videosStore.pagination.totalPages) {
    router.push({ query: { ...route.query, page: newPage } });
  }
};

onMounted(() => {
  fetchUploadsData();
});

onUnmounted(() => {
  stopPolling();
});

watch(
  () => route.query,
  async (newQuery, oldQuery) => {
    if (newQuery.page !== oldQuery?.page || newQuery.limit !== oldQuery?.limit) {
      stopPolling();
      await fetchUploadsData(parseInt(newQuery.page as string) || 1, parseInt(newQuery.limit as string) || 12);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  },
  { deep: true }
);

watch(
  () => videosStore.videos,
  () => {
    const processingVideoIds = getProcessingVideoIds();
    if (processingVideoIds.length > 0) {
      if (!processingVideoIds.some(id => getProcessingVideoIds().includes(id))) {
        stopPolling();
        startPolling(processingVideoIds, 3000);
      }
    } else {
      stopPolling();
    }
  },
  { deep: true }
);

// Watch for completed uploads and refresh the list
watch(
  () => uploadsStore.completedUploads.length,
  (newLength, oldLength) => {
    if (newLength > oldLength) {
      // New upload completed, wait a bit then refresh the uploads list
      setTimeout(() => {
        fetchUploadsData();
      }, 2000);
    }
  }
);
</script>
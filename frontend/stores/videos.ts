import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { VideoListItem, VideoDetail, VideoListResponseData, ApiResponse } from '~/types/api';

export const useVideosStore = defineStore('videos', () => {
  const videos = ref<VideoListItem[]>([]);
  const currentVideo = ref<VideoDetail | null>(null);
  const isLoadingList = ref<boolean>(true);
  const isLoadingDetail = ref<boolean>(false);
  const error = ref<string | null>(null);
  const pagination = ref({
    totalCount: 0,
    page: 1,
    totalPages: 1,
    pageSize: 10,
  });

  const { get } = useApi();

  async function fetchVideos(page: number = 1, limit: number = 10): Promise<void> {
    isLoadingList.value = true;
    error.value = null;
    try {
      const response: ApiResponse<VideoListResponseData> = await get(
        'stream',
        `/videos?page=${page}&limit=${limit}`
      );

      if (response.success && response.data) {
        videos.value = response.data.videos;
        pagination.value.totalCount = response.data.total_count || 0;
        pagination.value.page = response.data.page || 1;
        pagination.value.totalPages = response.data.total_pages || 1;
        pagination.value.pageSize = limit;
      } else {
        error.value = response.message || 'Failed to fetch videos.';
      }
    } catch (err: unknown) {
      error.value = 'An unexpected error occurred while fetching videos.';
    } finally {
      isLoadingList.value = false;
    }
  }

  async function fetchVideoById(id: string): Promise<void> {
    isLoadingDetail.value = true;
    currentVideo.value = null;
    error.value = null;
    try {
      const response: ApiResponse<VideoDetail> = await get(
        'stream',
        `/videos/${id}`
      );

      if (response.success && response.data) {
        currentVideo.value = response.data;
      } else {
        error.value = response.message || `Failed to fetch video with id ${id}`;
      }
    } catch (err: unknown) {
      error.value = 'An unexpected error occurred while fetching video details.';
    } finally {
      isLoadingDetail.value = false;
    }
  }

  function getNextVideoId(currentId: string): string | null {
    const currentIndex = videos.value.findIndex(v => v.id === currentId);
    if (currentIndex !== -1 && currentIndex < videos.value.length - 1) {
      return videos.value[currentIndex + 1].id;
    }
    return null;
  }

  function getPreviousVideoId(currentId: string): string | null {
    const currentIndex = videos.value.findIndex(v => v.id === currentId);
    if (currentIndex > 0) {
      return videos.value[currentIndex - 1].id;
    }
    return null;
  }

  function clearCurrentVideo() {
    currentVideo.value = null;
  }

  return {
    videos,
    currentVideo,
    isLoadingList,
    isLoadingDetail,
    error,
    pagination,
    fetchVideos,
    fetchVideoById,
    getNextVideoId,
    getPreviousVideoId,
    clearCurrentVideo
  };
});

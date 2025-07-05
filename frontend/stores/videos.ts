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

  async function fetchUserVideos(userId: string, page: number = 1, limit: number = 10): Promise<void> {
    isLoadingList.value = true;
    error.value = null;
    try {
      const response: ApiResponse<VideoListResponseData> = await get(
        'stream',
        `/videos?user_id=${userId}&page=${page}&limit=${limit}`
      );

      if (response.success && response.data) {
        videos.value = response.data.videos;
        pagination.value.totalCount = response.data.total_count || 0;
        pagination.value.page = response.data.page || 1;
        pagination.value.totalPages = response.data.total_pages || 1;
        pagination.value.pageSize = limit;
      } else {
        error.value = response.message || 'Failed to fetch user videos.';
      }
    } catch (err: unknown) {
      error.value = 'An unexpected error occurred while fetching user videos.';
    } finally {
      isLoadingList.value = false;
    }
  }

  async function fetchMyVideos(page: number = 1, limit: number = 10, status?: string): Promise<void> {
    isLoadingList.value = true;
    error.value = null;
    try {
      let url = `/videos/my/videos?page=${page}&limit=${limit}`;
      if (status) {
        url += `&status=${status}`;
      }
      
      const response: ApiResponse<VideoListResponseData> = await get('stream', url);

      if (response.success && response.data) {
        videos.value = response.data.videos;
        pagination.value.totalCount = response.data.total_count || 0;
        pagination.value.page = response.data.page || 1;
        pagination.value.totalPages = response.data.total_pages || 1;
        pagination.value.pageSize = limit;
      } else {
        error.value = response.message || 'Failed to fetch your videos.';
      }
    } catch (err: unknown) {
      error.value = 'An unexpected error occurred while fetching your videos.';
    } finally {
      isLoadingList.value = false;
    }
  }

  async function pollVideoStatuses(videoIds: string[]): Promise<Record<string, any> | null> {
    if (videoIds.length === 0) return null;
    
    try {
      const response: ApiResponse<{ statuses: Record<string, any>; timestamp: string }> = await get(
        'stream',
        `/videos/my/status/poll?video_ids=${videoIds.join(',')}`
      );

      if (response.success && response.data) {
        return response.data.statuses;
      }
    } catch (err: unknown) {
      console.error('Failed to poll video statuses:', err);
    }
    return null;
  }

  async function getVideoStatus(videoId: string): Promise<any | null> {
    try {
      const response: ApiResponse<any> = await get('stream', `/videos/${videoId}/status`);
      
      if (response.success && response.data) {
        return response.data;
      }
    } catch (err: unknown) {
      console.error('Failed to get video status:', err);
    }
    return null;
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
    fetchUserVideos,
    fetchMyVideos,
    pollVideoStatuses,
    getVideoStatus,
    fetchVideoById,
    getNextVideoId,
    getPreviousVideoId,
    clearCurrentVideo
  };
});

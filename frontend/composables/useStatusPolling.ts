import { ref, onUnmounted } from 'vue';
import { useVideosStore } from '~/stores/videos';

export const useStatusPolling = () => {
  const videosStore = useVideosStore();
  const pollingInterval = ref<NodeJS.Timeout | null>(null);
  const isPolling = ref(false);

  const startPolling = (videoIds: string[], intervalMs: number = 5000) => {
    if (videoIds.length === 0) return;
    
    isPolling.value = true;
    
    const poll = async () => {
      try {
        const statuses = await videosStore.pollVideoStatuses(videoIds);
        if (statuses) {
          updateVideoStatuses(statuses);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    poll();
    pollingInterval.value = setInterval(poll, intervalMs);
  };

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value);
      pollingInterval.value = null;
    }
    isPolling.value = false;
  };

  const updateVideoStatuses = (statuses: Record<string, any>) => {
    videosStore.videos.forEach((video, index) => {
      if (statuses[video.id]) {
        const statusData = statuses[video.id];
        if (video.status !== statusData.status) {
          videosStore.videos[index] = {
            ...video,
            status: statusData.status,
            published_at: statusData.published_at
          };
        }
      }
    });
  };

  const getProcessingVideoIds = () => {
    return videosStore.videos
      .filter(video => 
        video.status && 
        !['published', 'failed'].includes(video.status.toLowerCase())
      )
      .map(video => video.id);
  };

  onUnmounted(() => {
    stopPolling();
  });

  return {
    isPolling,
    startPolling,
    stopPolling,
    getProcessingVideoIds
  };
};
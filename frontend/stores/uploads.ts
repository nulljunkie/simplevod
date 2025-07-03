import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useRuntimeConfig } from '#imports';
import type {
  InitiateUploadResponse,
  PresignedUrlsResponse,
  RecordPartResponse,
  CompleteUploadResponse,
  ApiResponse,
} from '~/types/api';
import type { UploadFile, ChunkJob } from '~/types/internal/upload';
import { UploadServiceImpl } from '~/services/upload.service';
import type { UploadService } from '~/services/upload.service';


interface UploadState {
  activeUploads: UploadFile[];
  completedUploads: string[];
  isUploadPanelOpen: boolean;
}

export const useUploadsStore = defineStore('uploads', () => {
  const state = ref<UploadState>({
    activeUploads: [],
    completedUploads: [],
    isUploadPanelOpen: false,
  });

  const config = useRuntimeConfig();
  const chunkSize = (config.public.uploadChunkSizeMb ?? 5) * 1024 * 1024;
  const maxConcurrentChunks = Number(config.public.maxConcurrentChunks ?? 4);
  const uploadService: UploadService = new UploadServiceImpl();

  const overallProgress = computed(() => {
    const uploadsInProgress = state.value.activeUploads.filter(u => ['uploading', 'pending', 'paused'].includes(u.status));
    if (!uploadsInProgress.length) return 0;
    const totalProgress = uploadsInProgress.reduce((sum, u) => sum + u.progress, 0);
    return Math.round(totalProgress / uploadsInProgress.length);
  });

  const hasActiveUploads = computed(() =>
    state.value.activeUploads.some(u => ['uploading', 'pending', 'paused'].includes(u.status))
  );
 
  //
  // INTERNAL HELPERS
  //

  const findUpload = (uploadId: string): UploadFile | undefined => state.value.activeUploads.find(u => u.id === uploadId);

  const updateProgress = (uploadId: string) => {
    const upload = findUpload(uploadId);
    if (!upload) return;
    
    const uploadedSize = upload.uploadedChunkSizes.reduce((acc, size) => acc + size, 0);
    const progress = upload.file.size > 0 ? Math.round((uploadedSize / upload.file.size) * 100) : 0;
    
    console.log(`[Progress] ${uploadId}: ${uploadedSize}/${upload.file.size} = ${progress}%`);
    console.log(`Uploaded chunks: ${JSON.stringify(upload.uploadedChunkSizes)}`);
    
    upload.progress = progress;
  };
  
  async function processChunk(upload: UploadFile, job: ChunkJob): Promise<void> {
    if (upload.status !== 'uploading' || !upload.presignedUrls) return;
    
    const url = upload.presignedUrls.get(job.partNumber);
    if (!url) {
      throw new Error(`Presigned URL not found for part ${job.partNumber}.`);
    }

    job.retries++;
    try {
      const etag = await uploadService.uploadChunk(url, job.blob, upload.file.type, upload.controller!.signal);
      await uploadService.recordPart(upload.uploadKey!, job.partNumber, etag);
      
      upload.etags.push({ partNumber: job.partNumber, etag });
      upload.uploadedParts++;
      upload.uploadedChunkSizes[job.partNumber - 1] = job.blob.size;
      updateProgress(upload.id);
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log(`[UploadsStore] Chunk ${job.partNumber} aborted.`);
        upload.chunksQueue.unshift(job);
        return;
      }
      console.error(`[UploadsStore] Error processing chunk ${job.partNumber}:`, error);
      if (job.retries < 3) {
        upload.chunksQueue.unshift(job);
      } else {
        upload.status = 'failed';
        upload.errorMessage = `Failed to upload part ${job.partNumber}.`;
        updateProgress(upload.id);
      }
    }
  }

  async function processChunksConcurrently(uploadId: string) {
    const upload = findUpload(uploadId);
    if (!upload || upload.status !== 'uploading') return;

    const chunkWorker = async () => {
      while (upload.status === 'uploading') {
        const job = upload.chunksQueue.shift();
        if (!job) break;
        await processChunk(upload, job);
      }
    };
    
    if(upload.chunksQueue.length === 0) {
      for (let i = 0; i < upload.totalParts; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, upload.file.size);
        const job: ChunkJob = {
          partNumber: i + 1,
          blob: upload.file.slice(start, end),
          retries: 0
        };
        upload.chunksQueue.push(job);
      }
      updateProgress(uploadId);
    }
    
    const workers = Array(Math.min(maxConcurrentChunks, upload.chunksQueue.length))
      .fill(0)
      .map(() => chunkWorker());
    await Promise.all(workers);
    
    while (upload.status === 'uploading' && upload.chunksQueue.length > 0) {
      const job = upload.chunksQueue.shift();
      if (job) {
        await processChunk(upload, job);
        updateProgress(uploadId);
      }
    }
    
    if (upload.status === 'uploading' && upload.uploadedParts === upload.totalParts) {
      await completeUpload(upload.id);
    }
    
    if (state.value.activeUploads.length === 0) {
      state.value.isUploadPanelOpen = false;
    }
  }
  
  //
  // ACTIONS (Public API)
  //

  function toggleUploadPanel() {
    state.value.isUploadPanelOpen = !state.value.isUploadPanelOpen;
  }
  
    async function addFileToUploadQueue(fileData: { file: File; title: string; description?: string; visibility: 'public' | 'private'; thumbnail?: File; duration?: number; }) {
    state.value.isUploadPanelOpen = true;
      const totalParts = Math.ceil(fileData.file.size / chunkSize);
      const upload: UploadFile = {
        id: crypto.randomUUID(),
        file: fileData.file,
        title: fileData.title,
        description: fileData.description,
        visibility: fileData.visibility,
        thumbnail: fileData.thumbnail,
        duration: fileData.duration,
        status: 'pending',
        progress: 0,
        totalParts,
        uploadedParts: 0,
        etags: [],
        controller: new AbortController(),
        chunksQueue: [],
        uploadedChunkSizes: Array(totalParts).fill(0),
        presignedUrls: new Map<number, string>(),
      };

      state.value.activeUploads.push(upload);
      await startUpload(upload.id);
  }

  async function startUpload(uploadId: string) {
    const upload = findUpload(uploadId);
    if (!upload || !['pending', 'paused'].includes(upload.status)) return;
    
    upload.status = 'uploading';
    upload.errorMessage = undefined;
    
    try {
      if (!upload.uploadKey) {
        const { key, uploadId: remoteUploadId, thumbnailUploadUrl } = await uploadService.initiateUpload(upload);
        upload.uploadKey = key;
        upload.uploadId = remoteUploadId;

        if (upload.thumbnail && thumbnailUploadUrl) {
          await uploadService.uploadThumbnail(thumbnailUploadUrl, upload.thumbnail, upload.controller!.signal);
        }
      }
      
      const partNumbersToFetch = [];
      for (let i = 1; i <= upload.totalParts; i++) {
        if (!upload.presignedUrls!.has(i)) {
             partNumbersToFetch.push(i);
        }
      }

      if (partNumbersToFetch.length > 0) {
        console.log(`[UploadsStore] Fetching presigned URLs for ${partNumbersToFetch.length} parts.`);
        const response = await uploadService.getPresignedUrls(upload.uploadKey!, partNumbersToFetch);
        response.urls.forEach(item => {
          upload.presignedUrls!.set(item.partNumber, item.url);
        });
      }
      
      await processChunksConcurrently(uploadId);
    } catch (error: any) {
      console.error('[UploadsStore] Failed to start upload:', error);
      upload.status = 'failed';
      upload.errorMessage = error.message || 'Upload initialization failed.';
      updateProgress(uploadId);
    }
  }

  function pauseUpload(uploadId: string) {
    const upload = findUpload(uploadId);
    if (upload?.status === 'uploading') {
      upload.status = 'paused';
      upload.controller?.abort();
      upload.controller = new AbortController();
      updateProgress(uploadId);
    }
  }

  async function resumeUpload(uploadId: string) {
    const upload = findUpload(uploadId);
    if (upload?.status === 'paused') {
      await startUpload(uploadId);
    }
  }

  async function completeUpload(uploadId: string) {
    const upload = findUpload(uploadId);
    if (!upload || !upload.uploadKey) return;
    
    try {
      const videoId = await uploadService.completeUpload(upload.uploadKey);
      upload.status = 'completed';
      
      console.log(`[CompleteUpload] Before updateProgress: ${upload.progress}%`);
      updateProgress(uploadId);
      console.log(`[CompleteUpload] After updateProgress: ${upload.progress}%`);
      
      state.value.completedUploads.push(videoId);
      
      setTimeout(() => {
        console.log(`[CompleteUpload] Removing upload ${uploadId}`);
        state.value.activeUploads = state.value.activeUploads.filter(u => u.id !== uploadId);
      }, 5000);
    } catch (error: any) {
      upload.status = 'failed';
      upload.errorMessage = error.message || 'Failed to finalize upload.';
      updateProgress(uploadId);
    }
  }
  
  async function cancelUpload(uploadId: string) {
    const upload = findUpload(uploadId);
    if (!upload) return;

    upload.status = 'cancelling';
    upload.controller?.abort();

    if (upload.uploadKey) {
      try {
        await uploadService.abortUpload(upload.uploadKey);
      } catch (error) {
        console.error(`[UploadsStore] Failed to abort upload ${uploadId} on the server:`, error);
      }
    }

    setTimeout(() => {
      state.value.activeUploads = state.value.activeUploads.filter(u => u.id !== uploadId);
      if (state.value.activeUploads.length === 0) {
        state.value.isUploadPanelOpen = false;
      }
    }, 500);
  }

  async function retryUpload(uploadId: string) {
    const upload = findUpload(uploadId);
    if (upload && upload.status === 'failed') {
      upload.status = 'pending';
      upload.chunksQueue = [];
      upload.uploadedParts = 0;
      upload.etags = [];
      upload.uploadedChunkSizes.fill(0);
      upload.errorMessage = undefined;
      upload.controller = new AbortController();
      await startUpload(uploadId);
    }
  }

  return {
    activeUploads: computed(() => state.value.activeUploads),
    completedUploads: computed(() => state.value.completedUploads),
    isUploadPanelOpen: computed(() => state.value.isUploadPanelOpen),
    clearCompletedUploads: () => {
      state.value.activeUploads = state.value.activeUploads.filter(u => u.status !== 'completed');
      if (state.value.activeUploads.length === 0) {
        state.value.isUploadPanelOpen = false;
      }
    },

    overallProgress,
    hasActiveUploads,

    addFileToUploadQueue,
    pauseUpload,
    resumeUpload,
    retryUpload,
    cancelUpload,
    toggleUploadPanel,
  };

});

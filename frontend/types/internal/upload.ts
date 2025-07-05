export interface ChunkJob {
  partNumber: number;
  blob: Blob;
  retries: number;
}

export interface UploadFile {
  id: string;
  file: File;
  title: string;
  description?: string;
  visibility: 'public' | 'private';
  thumbnail?: File;
  duration?: number;
  status: 'pending' | 'uploading' | 'failed' | 'completed' | 'cancelled' | 'paused' | 'cancelling';
  progress: number;
  totalParts: number;
  uploadedParts: number;
  uploadKey?: string;
  uploadId?: string;
  chunksQueue: ChunkJob[];
  uploadedChunkSizes: number[];
  etags: { partNumber: number; etag: string }[];
  presignedUrls?: Map<number, string>;
  errorMessage?: string;
  controller?: AbortController;
}

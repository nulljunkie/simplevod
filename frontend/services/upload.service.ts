import { useApi } from '~/composables/useApi';
import type { InitiateUploadResponse, PresignedUrlsResponse, RecordPartResponse, CompleteUploadResponse, ApiResponse } from '~/types/api';
import type { UploadFile } from '~/types/internal/upload';

export interface UploadService {
  initiateUpload(upload: UploadFile): Promise<InitiateUploadResponse>;
  getPresignedUrls(key: string, partNumbers: number[]): Promise<PresignedUrlsResponse>;
  uploadChunk(url: string, blob: Blob, contentType: string, signal: AbortSignal): Promise<string>;
  recordPart(key: string, partNumber: number, etag: string): Promise<void>;
  completeUpload(key: string): Promise<string>;
  uploadThumbnail(url: string, thumbnail: File, signal: AbortSignal): Promise<void>;
  abortUpload(key: string): Promise<void>;
}

export class UploadServiceImpl implements UploadService {
  private readonly api = useApi();

  private async postAndUnwrap<T>(endpoint: string, body: object): Promise<T> {
    const response = await this.api.post<ApiResponse<T>>('upload', endpoint, body);
    if (!response || !response.data) {
      throw new Error(`API error at ${endpoint}: No data returned.`);
    }
    return response.data;
  }

  async initiateUpload(upload: UploadFile): Promise<InitiateUploadResponse> {
    return this.postAndUnwrap<InitiateUploadResponse>('/initiate', {
      filename: upload.file.name,
      contentType: upload.file.type,
      total_parts: upload.totalParts,
      title: upload.title,
      description: upload.description,
      visibility: upload.visibility,
      thumbnail_filename: upload.thumbnail?.name,
      duration: upload.duration,
    });
  }
  
  async getPresignedUrls(key: string, partNumbers: number[]): Promise<PresignedUrlsResponse> {
    return this.postAndUnwrap<PresignedUrlsResponse>('/presigned-urls', {
      key,
      part_numbers: partNumbers,
    });
  }

  async uploadChunk(url: string, blob: Blob, contentType: string, signal: AbortSignal): Promise<string> {
    const response = await fetch(url, {
      method: 'PUT',
      body: blob,
      signal,
      headers: { 'Content-Type': contentType },
    });
    if (!response.ok) throw new Error(`Chunk upload failed: ${response.statusText}`);
    const etag = response.headers.get('ETag')?.replace(/"/g, '');
    if (!etag) throw new Error('ETag not found in chunk upload response.');
    return etag;
  }

  async recordPart(key: string, partNumber: number, etag: string): Promise<void> {
    await this.postAndUnwrap<RecordPartResponse>('/record-part', {
      key,
      part_number: partNumber,
      etag,
    });
  }
  
  async completeUpload(key: string): Promise<string> {
    const responseData = await this.postAndUnwrap<CompleteUploadResponse>('/complete', { key });
    return responseData.video_id;
  }

  async uploadThumbnail(url: string, thumbnail: File, signal: AbortSignal): Promise<void> {
    const response = await fetch(url, {
      method: 'PUT',
      body: thumbnail,
      signal,
      headers: { 'Content-Type': thumbnail.type },
    });
    if (!response.ok) throw new Error(`Thumbnail upload failed: ${response.statusText}`);
  }

  async abortUpload(key: string): Promise<void> {
    await this.postAndUnwrap<any>('/abort', { key });
  }
}

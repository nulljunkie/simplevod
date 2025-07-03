export interface InitiateUploadRequest {
  filename: string;
  contentType: string;
  total_parts: number;
}

export interface InitiateUploadResponse {
  key: string;
  uploadId: string;
  objectKey: string;
  thumbnailUploadUrl?: string;
}

export interface PresignedUrlRequest {
  key: string;
  partNumbers: number[];
}

export interface PresignedUrl {
  partNumber: number;
  url: string;
}

export interface PresignedUrlsResponse {
  urls: PresignedUrl[];
}

export interface RecordPartRequest {
  key: string;
  partNumber: number;
  etag: string;
}

export interface RecordPartResponse {
  message: string;
}

export interface ListPartsRequest {
  key: string;
}

export interface UploadedPart {
  PartNumber: number;
  ETag: string;
}

export interface ListPartsResponse {
  uploadedParts: UploadedPart[];
}

export interface CompleteUploadRequest {
  key: string;
}

export interface CompleteUploadResponse {
  message: string;
  video_id: string;
}

export interface AbortUploadRequest {
  key: string;
}

export interface AbortUploadResponse {
  message: string;
}

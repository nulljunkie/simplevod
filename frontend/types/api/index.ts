export type { ApiResponse } from './generic';

export { ApiError } from './error';

export type {
  User,
  LoginRequest,
  RegisterRequest,
  LoginResponse,
  RegisterResponse,
  ActivationResponse,
  LoginApiResponse,
  RegisterApiResponse,
  ActivationApiResponse
} from './auth.ts';

export type {
  ResendActivationResponse,
  ResendActivationApiResponse,
} from './auth.ts';

export type {
  VideoListItem,
  VideoDetail, 
  VideoListResponseData,
  UploaderInfo,
  ThumbnailUrls
} from './videos.ts';

export type {
  InitiateUploadRequest,
  InitiateUploadResponse,
  PresignedUrlRequest,
  PresignedUrl,
  PresignedUrlsResponse,
  RecordPartRequest,
  RecordPartResponse,
  ListPartsRequest,
  UploadedPart,
  ListPartsResponse,
  CompleteUploadRequest,
  CompleteUploadResponse,
  AbortUploadRequest,
  AbortUploadResponse
} from './uploads.ts';

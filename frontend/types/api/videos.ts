export interface VideoListItem {
  id: string;
  title: string;
  description: string;
  thumbnail_url: string | null;
  duration_seconds: number;
  uploader_id: string;
  uploader_username?: string;
  uploader?: UploaderInfo;
  views_count: number;
  likes_count: number;
  published_at: string;
}

export interface UploaderInfo {
  id: string;
  username: string;
}

export interface ThumbnailUrls {
  small: string | null;
  large: string | null;
}

export interface VideoDetail {
  id: string;
  title: string;
  description: string;
  stream_url: string | null;
  thumbnail_urls: ThumbnailUrls;
  duration_seconds: number;
  uploader: UploaderInfo;
  tags: string[];
  visibility: 'public' | 'private' | 'unlisted';
  views_count: number;
  likes_count: number;
  published_at: string;
}

export interface VideoListResponseData {
  videos: VideoListItem[];
  total_count: number;
  page: number;
  total_pages: number;
}

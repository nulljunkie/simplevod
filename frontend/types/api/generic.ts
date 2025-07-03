export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  total_count?: number;
  page?: number;
  total_pages?: number;
}

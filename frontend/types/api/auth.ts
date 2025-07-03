import type { ApiResponse } from './generic';

export interface User {
  id: string;
  email: string;
  username?: string;
  isActive: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirmPassword: string;
}

export interface LoginResponse {
  access: string;
}

export interface RegisterResponse {
  message: string;
}

export interface ActivationResponse {
  access: string;
}

export interface ResendActivationResponse {
  message: string;
}

export type LoginApiResponse = ApiResponse<LoginResponse>;
export type RegisterApiResponse = ApiResponse<RegisterResponse>;
export type ActivationApiResponse = ApiResponse<ActivationResponse>;
export type ResendActivationApiResponse = ApiResponse<ResendActivationResponse>;

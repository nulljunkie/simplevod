import type { ApiResponse } from './generic';

export class ApiError<T = unknown> extends Error {
  success: false = false;
  message: string;
  data?: T;
  status: number;
  url: string;

  constructor(message: string, response: Response, body: ApiResponse<T>) {
    super(message);
    this.message = message;
    this.data = body.data;
    this.status = response.status;
    this.url = response.url;

    // Maintain proper prototype chain (for instanceof checks)
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

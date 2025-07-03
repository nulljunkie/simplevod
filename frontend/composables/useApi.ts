import type { NitroFetchRequest, NitroFetchOptions } from 'nitropack';
import { useAuthStore } from '~/stores/auth';
import { useRuntimeConfig } from '#imports';
import { ApiError, type ApiResponse } from '~/types/api';

/**
 * Service configuration.
 */
interface ServiceConfig {
  baseUrl: string;
}

/**
 * HTTP methods supported by fetchApi.
 */
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

/**
 * Composable for making authenticated API requests.
 * @returns Object with fetchApi function.
 */
export const useApi = () => {
  const config = useRuntimeConfig();
  const authStore = useAuthStore();

  /**
   * Get the appropriate service URL based on execution context.
   * Server-side (SSR): use internal cluster URLs
   * Client-side: use external ingress URLs
   */
  const getServiceUrl = (serviceType: string): string => {
    if (process.server) {
      // Server-side: use internal cluster URLs
      switch (serviceType) {
        case 'auth':
          return config.authServiceUrl;
        case 'stream':
          return config.streamServiceUrl;
        case 'upload':
          return config.uploadServiceUrl;
        default:
          throw new Error(`Unknown service type: ${serviceType}`);
      }
    } else {
      // Client-side: use external ingress URLs
      switch (serviceType) {
        case 'auth':
          return config.public.authServiceUrl;
        case 'stream':
          return config.public.streamServiceUrl;
        case 'upload':
          return config.public.uploadServiceUrl;
        default:
          throw new Error(`Unknown service type: ${serviceType}`);
      }
    }
  };

  // Service configurations
  const services: Record<string, ServiceConfig> = {
    stream: { baseUrl: getServiceUrl('stream') },
    auth: { baseUrl: getServiceUrl('auth') },
    upload: { baseUrl: getServiceUrl('upload') },
  };

  /**
   * Build headers with authentication and content type.
   * @param inputHeaders - Optional input headers.
   * @returns Headers object.
   */
  function buildHeaders(inputHeaders?: HeadersInit): Headers {
    const headers = new Headers(inputHeaders);
    if (authStore.token) {
      headers.set('Authorization', `Bearer ${authStore.token}`);
    }
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    return headers;
  }

  /**
   * Format error message from API response.
   * @param error - Error object from fetch.
   * @returns Formatted error message.
   */
  function formatError(error: any): string {
    const status = error.response?.status || 'Unknown';
    const statusText = error.response?.statusText || 'Error';
    const message =
      error.response?._data?.error ||
      error.response?._data?.detail ||
      error.message ||
      'Unknown error';
    return `API Error: ${status} ${statusText} - ${message}`;
  }

  /**
   * Build fetch options with error handling.
   * @param options - Request options.
   * @returns Nitro fetch options.
   */
  function buildFetchOptions(options: RequestInit): NitroFetchOptions<any> {
    const method = options.method as HttpMethod;
    const headers = buildHeaders(options.headers);
    return {
      ...options,
      method,
      headers,
      onResponseError: ({ response }) => {
        if (response.status === 401) {
          console.error('API request unauthorized. Logging out.');
          authStore.logout();
          // TODO: Open login modal
        }
        console.log(response)
        // throw new Error(formatError({ response }));

        const body = response._data as ApiResponse<unknown>;
        throw new ApiError(body?.message || response.statusText || 'Unknown error', response, body);
      },
    };
  }

  /**
   * Fetch data from a specified service and endpoint.
   * @param service - Service name (e.g., 'auth', 'upload').
   * @param endpoint - API endpoint path.
   * @param method - HTTP method (GET, POST, etc.).
   * @param options - Request options (body, headers, etc.).
   * @returns Promise<ApiResponse<T>> - API response data.
   */
  async function fetchApi<T>(
    service: string,
    endpoint: string,
    method: HttpMethod,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const serviceConfig = services[service];
    if (!serviceConfig) {
      throw new Error(`Unknown service: ${service}`);
    }
    const url = `${serviceConfig.baseUrl}${endpoint}`;
    const fetchOptions = buildFetchOptions({ ...options, method });

    // try {
    //   return await $fetch<ApiResponse<T>>(url, fetchOptions);
    // } catch (error: any) {
    //   console.log("====> ", error.message)
    //   throw new Error(formatError(error));
    // }
    return await $fetch<ApiResponse<T>>(url, fetchOptions)
  }

  /**
   * Perform a POST request.
   * @param service - Service name.
   * @param endpoint - Endpoint path.
   * @param body - Request body.
   * @returns Promise<ApiResponse<T>> - Response data.
   */
  async function post<T>(service: string, endpoint: string, body: any): Promise<ApiResponse<T>> {
    return fetchApi<T>(service, endpoint, 'POST', { body: JSON.stringify(body) });
  }

  /**
   * Perform a GET request.
   * @param service - Service name.
   * @param endpoint - Endpoint path.
   * @returns Promise<ApiResponse<T>> - Response data.
   */
  async function get<T>(service: string, endpoint: string): Promise<ApiResponse<T>> {
    return fetchApi<T>(service, endpoint, 'GET');
  }

  return { fetchApi, post, get };
};

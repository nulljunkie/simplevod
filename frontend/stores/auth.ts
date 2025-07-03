import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useApi } from '~/composables/useApi';
import {
  ApiError,
  type User,
  type LoginRequest,
  type RegisterRequest,
  type LoginApiResponse,
  type RegisterApiResponse,
  type ActivationApiResponse,
  type ResendActivationApiResponse
} from '~/types/api';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const activationMessage = ref<string | null>(null);
  const resendMessage = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  const { post, get } = useApi();

  function setToken(newToken: string | null) {
    token.value = newToken;
    const tokenCookie = useCookie('auth-token', { maxAge: 60 * 60 * 24 * 7 }); // 7 days
    tokenCookie.value = newToken;
  }

  function clearError() {
    error.value = null;
  }

  function setLoading(value: boolean) {
    isLoading.value = value;
  }

  async function initializeAuth() {
    const tokenCookie = useCookie<string | null>('auth-token');
    const storedUser = localStorage.getItem('auth-user');

    if (tokenCookie.value) {
      setToken(tokenCookie.value);
      if (storedUser) {
        user.value = JSON.parse(storedUser);
      }
      // TODO: Fetch user profile when implemented
    }
  }

  async function login(credentials: LoginRequest): Promise<boolean> {
    resendMessage.value = null; // clear resend message
    setLoading(true);
    clearError();
    try {
      const response = await post<LoginApiResponse>('auth', '/login', credentials);

      if (!response.success) {
        error.value = response.message || 'Login failed.';
        setToken(null);
        localStorage.removeItem('auth-user');
        return false;
      }
      const accessToken = response.data?.access;
      if (accessToken) {
        setToken(accessToken);
      }
      user.value = { id: 'temp-user-id', email: credentials.email, isActive: true };
      localStorage.setItem('auth-user', JSON.stringify(user.value));
      return true;
    } catch (err: any) {
      if (err instanceof ApiError) {
        error.value = err.message;
        return false;
      }
      error.value = 'An unexpected error occurred during login.';
      setToken(null);
      localStorage.removeItem('auth-user');
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function register(credentials: RegisterRequest): Promise<boolean> {
    setLoading(true);
    clearError();
    activationMessage.value = null;
    try {
      const response = await post<RegisterApiResponse>('auth', '/register', credentials);

      if (!response.success) {
        error.value = response.message || 'Registration failed.';
        return false;
      }
      activationMessage.value = response.message || 'Registration successful. Please check your email.';
      return true;
    } catch (err: unknown) {
	  if (err instanceof ApiError) {
        error.value = err.message;
      } else {
        error.value = 'An unexpected error occurred during registration.';
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function resendActivationEmail(email: string): Promise<boolean> {
    setLoading(true);
    clearError();
    resendMessage.value = null;
    try {
      const response = await post<ResendActivationApiResponse>('auth', '/resend-activation', { email });
      if (!response.success) {
        error.value = response.message || 'Resend activation failed.';
        return false;
      }
      resendMessage.value = response.message || 'Activation email resent successfully.';
      return true;
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        error.value = err.message;
      } else {
        error.value = 'An unexpected error occurred while resending activation link.';
      }
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function activateAccount(activationToken: string): Promise<boolean> {
    setLoading(true);
    clearError();
    activationMessage.value = null;
    try {
      const response = await get<ActivationApiResponse>('auth', `/activate?token=${activationToken}`);
      if (!response.success) {
        error.value = response.message || 'Activation failed.';
        return false;
      }
      const accessToken = response.data?.access;
      if (accessToken) {
        setToken(accessToken);
      }
      user.value = { id: 'activated-user-id', email: 'unknown', isActive: true };
      localStorage.setItem('auth-user', JSON.stringify(user.value));
      activationMessage.value = 'Account activated successfully!';
      return true;
    } catch (err: unknown) {
      error.value = 'An unexpected error occurred during activation.';
      return false;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    user.value = null;
    setToken(null);
    localStorage.removeItem('auth-user');
  }

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    activationMessage,
    resendMessage,
    initializeAuth,
    login,
    register,
    activateAccount,
    resendActivationEmail,
    logout,
  };
});

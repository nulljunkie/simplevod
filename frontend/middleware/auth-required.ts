import { useAuthStore } from '~/stores/auth';

export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore();

  // Fallback to token in cookie if store not yet initialized
  if (!auth.token) {
    const tokenCookie = useCookie<string | null>('auth-token');
    if (tokenCookie.value) {
      auth.token = tokenCookie.value;
    }
  }

  if (!auth.isAuthenticated) {
    return navigateTo('/'); // Or navigateTo('/login') if you have a login page
  }
});

import { useAuthStore } from '~/stores/auth';

export default defineNuxtRouteMiddleware(async () => {
  if (process.server) return;

  const auth = useAuthStore();

  if (!auth.token && !auth.isAuthenticated) {
    const tokenCookie = useCookie<string | null>('auth-token');
    if (tokenCookie.value) {
      await auth.initializeAuth();
    }
  }
});

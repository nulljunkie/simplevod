import { useAuthStore } from '~/stores/auth';

export default defineNuxtRouteMiddleware(async () => {
  // No middleware needed - useCookie handles hydration automatically
});

<template>
  <div class="max-w-md mx-auto text-center py-12 sm:py-20 px-4">
    <Head>
      <Title>Account Activation</Title>
    </Head>

    <div v-if="authStore.isLoading">
      <UiSpinner size="large" class="mx-auto mb-4" />
      <h1 class="text-2xl font-semibold text-text-DEFAULT">Activating Your Account...</h1>
      <p class="text-text-muted mt-2">Please wait a moment.</p>
    </div>

    <div v-else-if="activationStatus === 'success' && authStore.activationMessage">
      <CheckCircleIcon class="h-16 w-16 text-accent-green mx-auto mb-4" />
      <h1 class="text-2xl font-semibold text-text-DEFAULT">Account Activated!</h1>
      <p class="text-text-muted mt-2 mb-6">{{ authStore.activationMessage }}</p>
      <NuxtLink to="/">
        <UiButton variant="primary">Continue to Homepage</UiButton>
      </NuxtLink>
    </div>

    <div v-else-if="activationStatus === 'failed' && authStore.error">
      <ExclamationCircleIcon class="h-16 w-16 text-accent-red mx-auto mb-4" />
      <h1 class="text-2xl font-semibold text-text-DEFAULT">Activation Failed</h1>
      <p class="text-text-muted mt-2 mb-6">{{ authStore.error }}</p>
      <p class="text-sm text-text-muted">
        If you believe this is an error, please contact support or try registering again.
      </p>
      <NuxtLink to="/"><UiButton variant="secondary" class="mt-4">Go to Homepage</UiButton></NuxtLink>
    </div>

     <div v-else-if="!token">
        <ExclamationTriangleIcon class="h-16 w-16 text-yellow-400 mx-auto mb-4" />
        <h1 class="text-2xl font-semibold text-text-DEFAULT">Invalid Activation Link</h1>
        <p class="text-text-muted mt-2 mb-6">The activation token is missing or invalid. Please check the link from your email.</p>
        <NuxtLink to="/"><UiButton variant="secondary">Go to Homepage</UiButton></NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '~/stores/auth';
import UiButton from '~/components/ui/Button.vue';
import UiSpinner from '~/components/ui/Spinner.vue';
import { CheckCircleIcon, ExclamationCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const token = ref<string | null>(null);
const activationStatus = ref<'pending' | 'success' | 'failed'>('pending');

onMounted(async () => {
  token.value = route.query.token as string | null;
  authStore.error = null; // Clear previous errors
  authStore.activationMessage = null;

  if (token.value) {
    const success = await authStore.activateAccount(token.value);
    if (success) {
      activationStatus.value = 'success';
      // Optional: redirect after a few seconds
      setTimeout(() => {
        router.push('/');
      }, 5000);
    } else {
      activationStatus.value = 'failed';
    }
  } else {
    activationStatus.value = 'failed'; // No token implies failure to activate via this page
    authStore.error = 'Activation token not found in URL.';
  }
});
</script>

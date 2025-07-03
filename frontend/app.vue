<template>
  <NuxtLayout>
    <NuxtPage />
    <UploadDropdown />
  </NuxtLayout>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';

const authStore = useAuthStore();
const config = useRuntimeConfig();

useHead({
  titleTemplate: (titleChunk) => {
    return titleChunk ? `${titleChunk} - ${config.public.appName}` : config.public.appName || 'Video Platform';
  },
  htmlAttrs: {
    class: 'dark bg-background-DEFAULT text-text-DEFAULT'
  }
});
</script>

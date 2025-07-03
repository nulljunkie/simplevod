<template>
  <NuxtLink to="/" class="flex items-center space-x-2">
    <span class="font-bold text-2xl text-primary-red ">
      {{ appName }}
    </span>
  </NuxtLink>
</template>

<script setup lang="ts">
interface Props {
  appName: string
}

defineProps<Props>()
</script>

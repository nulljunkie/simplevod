<template>
  <template v-if="!isAuthenticated">
    <UiButton variant="secondary" size="sm" @click="emit('open-login')">Sign&nbsp;In</UiButton>
    <UiButton variant="secondary" size="sm" @click="emit('open-register')">Sign&nbsp;Up</UiButton>
  </template>
</template>

<script setup lang="ts">
import UiButton from '~/components/ui/Button.vue'

interface Props {
  isAuthenticated: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'open-login'): void
  (e: 'open-register'): void
}>()
</script>

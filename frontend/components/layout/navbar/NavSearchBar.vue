<template>
  <div class="flex-1 mx-4 max-w-md">
    <input
      type="text"
      placeholder="Search videos..."
      class="w-full px-3 py-1 border border-primary-gray rounded-md bg-primary-dark text-primary-smoke focus:outline-none focus:ring-4 focus:ring-primary-gray focus:border-none"
      v-model="innerValue"
      @keyup.enter="emit('search')"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
  (e: 'search'): void
}>()

const innerValue = computed({
  get: () => props.modelValue,
  set: (v: string) => emit('update:modelValue', v)
})
</script>

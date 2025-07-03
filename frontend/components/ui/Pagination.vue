<template>
  <div v-if="totalPages > 1" class="mt-8 flex justify-center items-center space-x-4">
    <UiButton
      @click="$emit('pageChange', currentPage - 1)"
      :disabled="currentPage <= 1"
      variant="secondary"
      size="sm"
    >
      <ChevronLeftIcon class="h-4 w-4 mr-1"/> Previous
    </UiButton>
    <span class="text-primary-silver text-sm px-4">
      {{ currentPage }} / {{ totalPages }}
    </span>
    <UiButton
      @click="$emit('pageChange', currentPage + 1)"
      :disabled="currentPage >= totalPages"
      variant="secondary"
      size="sm"
    >
      Next <ChevronRightIcon class="h-4 w-4 ml-1"/>
    </UiButton>
  </div>
</template>

<script setup lang="ts">
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline';
import UiButton from '~/components/ui/Button.vue';

defineProps<{
  currentPage: number;
  totalPages: number;
}>();

defineEmits<{
  pageChange: [page: number];
}>();
</script>
<template>
  <div class="flex items-center space-x-1 w-fit px-3 py-1 rounded-full text-xs font-medium" :class="statusClasses">
    <component :is="statusIcon" class="w-3 h-3" />
    <span>{{ statusText }}</span>
  </div>
</template>

<script setup lang="ts">
import ClockIcon from '~/components/icons/ClockIcon.vue';
import PlayIcon from '~/components/icons/PlayIcon.vue';
import CheckIcon from '~/components/icons/CheckIcon.vue';
import XMarkIcon from '~/components/icons/XMarkIcon.vue';
import QuestionMarkCircleIcon from '~/components/icons/QuestionMarkCircleIcon.vue';

interface Props {
  status: string;
}

const props = defineProps<Props>();

const statusConfig = computed(() => {
  switch (props.status?.toLowerCase()) {
    case 'uploaded':
      return {
        text: 'Uploaded',
        classes: 'bg-blue-900/30 text-blue-500 border border-blue-700/50',
        icon: ClockIcon
      };
    case 'processing':
      return {
        text: 'Processing',
        classes: 'bg-yellow-900/30 text-yellow-500 border border-yellow-700/50',
        icon: ClockIcon
      };
    case 'transcoding':
      return {
        text: 'Transcoding',
        classes: 'bg-purple-900/30 text-purple-500 border border-purple-700/50',
        icon: PlayIcon
      };
    case 'published':
      return {
        text: 'Published',
        classes: 'bg-green-900/30 text-green-500 border border-green-700/50 ',
        icon: CheckIcon
      };
    case 'failed':
      return {
        text: 'Failed',
        classes: 'bg-red-900/30 text-red-500 border border-red-700/50',
        icon: XMarkIcon
      };
    case 'pending_metadata':
      return {
        text: 'Processing',
        classes: 'bg-yellow-900/30 text-yellow-500 border border-yellow-700/50',
        icon: ClockIcon
      };
    default:
      return {
        text: props.status || 'Unknown',
        classes: 'bg-gray-900/30 text-gray-500 border border-gray-700/50',
        icon: QuestionMarkCircleIcon
      };
  }
});

const statusText = computed(() => statusConfig.value.text);
const statusClasses = computed(() => statusConfig.value.classes);
const statusIcon = computed(() => statusConfig.value.icon);
</script>

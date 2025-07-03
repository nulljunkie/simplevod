<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
    :class="[
      'inline-flex items-center justify-center rounded-md shadow-sm text-sm font-medium transition-colors duration-300 ease-in-out',
      variantClasses,
      sizeClasses,
      {
        'opacity-50 cursor-not-allowed': disabled,
        'cursor-wait': loading,
      },
      customClass
    ]"
  >
    <Spinner vSmall v-if="loading" class="mr-2 -ml-1" />
    <slot name="icon-left" />
    <slot />
    <slot name="icon-right" />
  </button>
</template>

<script setup lang="ts">
import Spinner from './Spinner.vue';

interface Props {
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'icon';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  customClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'button',
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  customClass: ''
});

defineEmits(['click']);

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-primary-dark text-primary-red  focus:outline-none focus-ring-2 focus:ring-primary-red focus:ring-offset-primary-dark disabled:bordre-primary-red/70 hover:bg-primary-red/15';
    case 'secondary':
      return 'bg-primary-dark text-primary-smoke border border-primary-gray';
    case 'icon':
      return 'bg-primary-dark text-primary-smoke';
    default:
      return 'bg-primary-dark text-primary-smoke border border-primary-gray';
  }
});

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'xs':
      return 'px-1.5 py-1.5 text-xs';
    case 'sm':
      return 'px-3 py-2 text-sm leading-4';
    case 'md':
      return 'px-4 py-3 text-sm';
    case 'lg':
      return 'px-6 py-4 text-base';
    default:
      return 'px-4 py-3 text-sm';
  }
});
</script>

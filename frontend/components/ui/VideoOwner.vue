<template>
  <div class="flex items-center space-x-2">
    <div class="relative">
      <img
        v-if="avatarUrl"
        :src="avatarUrl"
        :alt="username"
        :class="avatarClasses"
        loading="lazy"
      />
      <div v-else :class="[avatarClasses, 'bg-gray-600 flex items-center justify-center']">
        <span :class="textClasses">{{ userInitials }}</span>
      </div>
      <div v-if="isOnline" class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full"></div>
    </div>
    <div v-if="showUsername" class="min-w-0 flex-1">
      <p :class="usernameClasses" :title="username">{{ username }}</p>
      <p v-if="subtitle" :class="subtitleClasses" :title="subtitle">{{ subtitle }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  username: string;
  avatarUrl?: string;
  subtitle?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  showUsername?: boolean;
  isOnline?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showUsername: true,
  isOnline: false
});

const userInitials = computed(() => {
  return props.username
    .split(' ')
    .map(name => name.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase();
});

const avatarClasses = computed(() => {
  const baseClasses = 'rounded-full object-cover flex-shrink-0';
  const sizeClasses = {
    xs: 'w-6 h-6',
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12'
  };
  return [baseClasses, sizeClasses[props.size]];
});

const textClasses = computed(() => {
  const sizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-sm',
    lg: 'text-base'
  };
  return ['text-primary-smoke font-medium', sizeClasses[props.size]];
});

const usernameClasses = computed(() => {
  const sizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-sm',
    lg: 'text-base'
  };
  return ['text-primary-smoke font-medium truncate', sizeClasses[props.size]];
});

const subtitleClasses = computed(() => {
  const sizeClasses = {
    xs: 'text-xs',
    sm: 'text-xs',
    md: 'text-xs',
    lg: 'text-sm'
  };
  return ['text-primary-silver truncate', sizeClasses[props.size]];
});
</script>

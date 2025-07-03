<template>
  <div class="relative inline-block text-left" ref="dropdownRef">
    <div>
      <slot name="trigger" :toggle="toggleDropdown" :isOpen="isOpen">
        <UiButton @click="toggleDropdown" variant="secondary">
          Options
          <ChevronDownIcon class="-mr-1 ml-2 h-5 w-5" aria-hidden="true" />
        </UiButton>
      </slot>
    </div>

    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        :class="[
          'absolute z-40 mt-2 w-56 rounded-md shadow-lg focus:outline-none',
          props.variant === 'transparent' 
            ? 'bg-primary-dark/30 backdrop-blur-sm border border-primary-gray/30' 
            : 'bg-primary-dark border border-primary-gray',
          originClass,
          alignmentClass
        ]"
      >
        <div class="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
          <slot :close="closeDropdown" :variant="props.variant" />
          </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { ChevronDownIcon } from '@heroicons/vue/20/solid';
import UiButton from './Button.vue';

interface Props {
  origin?: 'top' | 'bottom';
  align?: 'left' | 'right';
  closeOnClickInside?: boolean;
  variant?: 'default' | 'transparent';
}

const props = withDefaults(defineProps<Props>(), {
  origin: 'bottom',
  align: 'left',
  closeOnClickInside: true,
  variant: 'default',
});

const isOpen = ref(false);
const dropdownRef = ref<HTMLElement | null>(null);

const toggleDropdown = () => {
  isOpen.value = !isOpen.value;
};

const closeDropdown = () => {
  isOpen.value = false;
};

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    if (isOpen.value) {
      closeDropdown();
    }
  } else if (props.closeOnClickInside && dropdownRef.value && dropdownRef.value.contains(event.target as Node)) {
    // If the click is inside and closeOnClickInside is true, check if it's a button or link
    let targetElement = event.target as HTMLElement;
    while (targetElement && targetElement !== dropdownRef.value) {
        if (targetElement.tagName === 'BUTTON' || targetElement.tagName === 'A') {
            closeDropdown();
            break;
        }
        targetElement = targetElement.parentElement as HTMLElement;
    }
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true); // Use capture phase
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside, true);
});

const originClass = computed(() => {
  return props.origin === 'top' ? 'bottom-full mb-2' : 'top-full';
});

const alignmentClass = computed(() => {
  return props.align === 'right' ? 'right-0' : 'left-0';
});
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200 transform"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-200 transform"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-40 overflow-y-auto bg-primary-dark/85"
        @click.self="closeModalOnOverlayClick"
      >
        <Transition
          enter-active-class="transition ease-out duration-200 transform"
          enter-from-class="opacity-0 translate-y-10 scale-95"
          enter-to-class="opacity-100 translate-y-0 scale-100"
          leave-active-class="transition ease-in duration-200 transform"
          leave-from-class="opacity-100 translate-y-0 scale-100"
          leave-to-class="opacity-0 translate-y-10 scale-95"
        >
          <div
            v-if="modelValue"
            class="flex items-center justify-center min-h-screen px-4 py-6"
          >
            <div
              class="bg-primary-dark shadow-xl rounded-lg border-4 border-primary-gray w-full overflow-hidden relative before:absolute before:inset-0 before:rounded-lg before:p-[3px] before:-z-10"
              :class="maxWidthClass"
              role="dialog"
              aria-modal="true"
              :aria-labelledby="title ? 'Modal Default Title' : undefined"
            >
              <div v-if="!hideHeader" class="px-6 py-4 border-b border-primary-gray flex items-center justify-between">
                <h3 v-if="title" id="modal-title" class="text-lg font-medium text-primary-smoke">
                  {{ title }}
                </h3>
                <slot name="header-actions"></slot>
                <button
                  v-if="showCloseButton"
                  @click="closeModal"
                  class="text-primary-silver hover:text-primary-smoke transition-colors"
                  aria-label="Close modal"
                >
                  <XMarkIcon class="h-6 w-6" />
                </button>
              </div>

              <!-- Modal Body -->
              <div class="px-6 py-5" :class="bodyClass">
                <slot />
              </div>

              <!-- Modal Footer -->
              <div v-if="!hideFooter && ($slots.footer || showDefaultFooterButtons)" class="px-6 py-4 border-t border-primary-gray sm:flex sm:flex-row-reverse">
                <!-- Named slot with fallback content -->
                <slot name="footer">
                  <!-- Default footer buttons -->
                  <template v-if="showDefaultFooterButtons">
                    <UiButton variant="primary" @click="emit('confirm')" class="sm:ml-3 sm:w-auto w-full mb-2 sm:mb-0">
                      {{ confirmText }}
                    </UiButton>
                    <UiButton variant="secondary" @click="closeModal" class="sm:w-auto w-full">
                      {{ cancelText }}
                    </UiButton>
                  </template>
                </slot>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/outline';
import UiButton from './Button.vue';

interface Props {
  modelValue: boolean; // To control open/close state
  title?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';
  persistent?: boolean; // If true, clicking overlay or pressing escape doesn't close modal
  showCloseButton?: boolean; // Show the X button in header
  hideHeader?: boolean;
  hideFooter?: boolean;
  bodyClass?: string; // Additional CSS classes for modal body
  showDefaultFooterButtons?: boolean; // Show confirm/cancel buttons
  confirmText?: string; // Text for confirm button
  cancelText?: string; // Text for cancel button
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: 'lg',
  persistent: false,
  showCloseButton: true,
  hideHeader: false,
  hideFooter: false,
  bodyClass: '',
  showDefaultFooterButtons: false,
  confirmText: 'Confirm',
  cancelText: 'Cancel',
});

const emit = defineEmits(['update:modelValue', 'close', 'confirm']);

const closeModal = () => {
  if (!props.persistent) {
    emit('update:modelValue', false);
  }
};

const closeModalOnOverlayClick = () => {
  if (!props.persistent) {
    closeModal();
  }
};

const maxWidthClass = computed(() => {
  switch (props.maxWidth) {
    case 'sm': return 'max-w-sm';
    case 'md': return 'max-w-md';
    case 'lg': return 'max-w-lg';
    case 'xl': return 'max-w-xl';
    case '2xl': return 'max-w-2xl';
    case '3xl': return 'max-w-3xl';
    case '4xl': return 'max-w-4xl';
    case '5xl': return 'max-w-5xl';
    case 'full': return 'max-w-full';
    default: return 'max-w-lg';
  }
});

// Handle Escape key
const handleEsc = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.modelValue) {
    closeModal();
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleEsc);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleEsc);
});
</script>

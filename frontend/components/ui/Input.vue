<template>
  <div class="w-full">
    <label v-if="label" :for="inputId" class="block text-sm font-medium text-primary-silver mb-1">
      {{ label }}
    </label>
    <div class="relative rounded-md shadow-sm">
      <div v-if="$slots.leadingIcon" class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <slot name="leadingIcon" />
      </div>
      <input
        :id="inputId"
        :type="internalType"
        :value="modelValue"
        @input="onInput"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :autocomplete="autocomplete"
        :class="[
          'block w-full px-3 py-2 border rounded-md focus:outline-none sm:text-sm',
          'bg-primary-dark border-primary-gray placeholder:text-primary-silver/70 text-primary-smoke',
          'focus:ring-primary-gray focus:ring-4 focus:border-none',
          { 'ring-2 ring-primary-error': hasErrorInternal },
          
          { 'pl-10': $slots.leadingIcon },
          { 'pr-10': $slots.trailingIcon || (type === 'password' && showPasswordToggle) },
          customClass,
        ]"
      />
      <div v-if="$slots.trailingIcon || (type === 'password' && showPasswordToggle)" class="absolute inset-y-0 right-0 pr-3 flex items-center">
        <slot name="trailingIcon" />
        <button
            v-if="type === 'password' && showPasswordToggle"
            type="button"
            @click="togglePasswordVisibility"
            class="text-primary-silver hover:text-primary-smoke"
            aria-label="Toggle password visibility"
        >
            <EyeIcon v-if="isPasswordVisible" class="h-5 w-5" />
            <EyeSlashIcon v-else class="h-5 w-5" />
        </button>
      </div>
    </div>
    <p v-if="hint" class="mt-1 text-xs text-primary-silver">{{ hint }}</p>
    <div v-if="displayErrors.length" class="mt-1 text-sm text-primary-error space-y-0.5">
      <p v-for="(err, idx) in displayErrors" :key="idx">{{ err }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline';

interface Props {
  modelValue: string | number | null;
  label?: string;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
  autocomplete?: string;
  hint?: string;
  errorMessage?: string;
  errors?: string[];
  hasError?: boolean;
  customClass?: string;
  showPasswordToggle?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  id: undefined,
  showPasswordToggle: true,
});

const emit = defineEmits(['update:modelValue']);

const inputId = computed(() => props.id || `input-${Math.random().toString(36).substring(2, 9)}`);

const hasErrorInternal = computed(() => props.hasError || (props.errors && props.errors.length > 0));

const displayErrors = computed<string[]>(() => {
  if (props.errors && props.errors.length) return props.errors;
  if (props.errorMessage && hasErrorInternal.value) return [props.errorMessage];
  return [];
});

const isPasswordVisible = ref(false);
const internalType = ref(props.type);

const onInput = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLInputElement).value);
};

const togglePasswordVisibility = () => {
    isPasswordVisible.value = !isPasswordVisible.value;
    internalType.value = isPasswordVisible.value ? 'text' : 'password';
};

watch(() => props.type, (newType) => {
    internalType.value = newType;
    if (newType !== 'password') {
        isPasswordVisible.value = false; // Reset if type changes from password
    }
});

</script>

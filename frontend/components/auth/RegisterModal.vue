<template>
  <UiModal v-model="isModalOpen" title="Create Your Account" max-width="md" :persistent="authStore.isLoading">
    <form @submit.prevent="handleRegister" class="space-y-6">
      <UiInput
        v-model="email"
        label="Email Address"
        type="email"
        id="register-email"
        placeholder="you@example.com"
        autocomplete="email"
        required
        :disabled="authStore.isLoading"
        :errors="emailErrors"
      />
      <UiInput
        v-model="password"
        label="Password"
        type="password"
        id="register-password"
        placeholder="Create a strong password"
        autocomplete="new-password"
        required
        :disabled="authStore.isLoading"
        :errors="passwordErrors"
        hint="Minimum 8 characters"
        show-password-toggle
      />
      <UiInput
        v-model="confirmPassword"
        label="Confirm Password"
        type="password"
        id="register-confirm-password"
        placeholder="Confirm your password"
        autocomplete="new-password"
        required
        :disabled="authStore.isLoading"
        :errors="confirmPasswordErrors"
        show-password-toggle
      />

      <div v-if="authStore.error && !authStore.error.toLowerCase().includes('email') && !authStore.error.toLowerCase().includes('password')" class="text-sm text-primary-error">
        {{ authStore.error }}
      </div>

      <div v-if="authStore.activationMessage" class="text-sm text-primary-success p-3 bg-primary-success/10 rounded-md">
        {{ authStore.activationMessage }}
      </div>

      <div>
        <UiButton 
          type="submit" 
          variant="primary" 
          size="md"
          class="w-full !font-bold"
          :loading="authStore.isLoading" 
          :disabled="authStore.isLoading || !!authStore.activationMessage"
        >
          Create Account
        </UiButton>
      </div>

      <p class="text-sm text-center text-primary-smoke">
        Already have an account?
        <button type="button" @click="switchToLogin" class="font-medium text-primary-red">
          Sign In
        </button>
      </p>

    </form>
  </UiModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useAuthStore } from '~/stores/auth';
import UiModal from '~/components/ui/Modal.vue';
import UiInput from '~/components/ui/Input.vue';
import UiButton from '~/components/ui/Button.vue';


const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits(['update:modelValue', 'openLogin']);

const authStore = useAuthStore();

const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const passwordMismatchError = ref<string | null>(null);

const isModalOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const emailErrors = computed(() => parseFieldErrors('email'));
const passwordErrors = computed(() => parseFieldErrors('password'));
const confirmPasswordErrors = computed(() => {
  const errs = [...passwordErrors.value];
  if (passwordMismatchError.value) errs.unshift(passwordMismatchError.value);
  return errs;
});

watch(isModalOpen, (newValue) => {
  if (newValue) {
    email.value = '';
    password.value = '';
    confirmPassword.value = '';
    authStore.error = null;
    authStore.activationMessage = null;
    passwordMismatchError.value = null;
  }
});

function parseFieldErrors(field: string): string[] {
  if (!authStore.error) return [];
  return authStore.error.split('; ').filter((msg: string) => msg.toLowerCase().includes(field));
}

const handleRegister = async () => {
  authStore.error = null;
  authStore.activationMessage = null;
  passwordMismatchError.value = null;

  if (password.value !== confirmPassword.value) {
    passwordMismatchError.value = 'Passwords do not match.';
    return;
  }
  if (password.value.length < 8) {
    authStore.error = 'Password must be at least 8 characters long.';
    return;
  }

  const success = await authStore.register({ email: email.value, password: password.value, confirmPassword: confirmPassword.value });
  if (success) {
    // Don't close modal, show success message (activationMessage)
    // Clear form fields if desired, or let user see what they entered.
    // For now, we keep them and show the message.
  }
};

const switchToLogin = () => {
  isModalOpen.value = false;
  emit('openLogin');
};
</script>

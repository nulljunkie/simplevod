<template>
  <UiModal v-model="isModalOpen" title="Login to Your Account" max-width="md" :persistent="authStore.isLoading">
    <form @submit.prevent="handleLogin" class="space-y-6">
      <UiInput
        v-model="email"
        label="Email Address"
        type="email"
        id="login-email"
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
        id="login-password"
        placeholder="••••••••"
        autocomplete="current-password"
        required
        :disabled="authStore.isLoading"
        :errors="passwordErrors"
        show-password-toggle
      />

      <div v-if="authStore.error && authStore.error.toLowerCase().includes('not active')" class="text-sm text-primary-error flex items-start gap-2">
        <span>{{ authStore.error }}</span>
        <button type="button" @click="handleResendActivation" class="text-primary-red underline" :disabled="authStore.isLoading">
          Resend activation email
        </button>
        <span v-if="authStore.resendMessage" class="text-primary-success">{{ authStore.resendMessage }}</span>
      </div>

      <div v-else-if="generalError" class="text-sm text-primary-error">
        {{ generalError }}
      </div>

      <div>
        <UiButton 
          type="submit" 
          variant="primary" 
          size="md"
          class="w-full !font-bold"
          :loading="authStore.isLoading" 
          :disabled="authStore.isLoading"
        >
          Sign In
        </UiButton>
      </div>

      <p class="text-sm text-center text-primary-smoke">
        Don't have an account?
        <button type="button" @click="switchToRegister" class="font-medium text-primary-red">
          Sign Up
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
const emit = defineEmits(['update:modelValue', 'openRegister']);

const authStore = useAuthStore();

const email = ref('');
const password = ref('');

const isModalOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const emailErrors = computed(() => parseFieldErrors('email'));
const passwordErrors = computed(() => parseFieldErrors('password'));

const generalError = computed(() => {
  if (!authStore.error) return null;
  const lower = authStore.error.toLowerCase();
  // handled separately
  if (lower.includes('not active')) return null;
  // field-specific errors handled by inputs
  if (lower.includes('password') || lower.includes('email')) return null;
  return authStore.error;
});

watch(isModalOpen, (newValue) => {
  if (newValue) {
    email.value = '';
    password.value = '';
    authStore.error = null;
  }
});

function parseFieldErrors(field: string): string[] {
  if (!authStore.error) return [];
  // backend joins messages with '; '
  return authStore.error.split('; ').filter((msg: string) => msg.toLowerCase().includes(field));
}

const handleLogin = async () => {
  if (!email.value || !password.value) {
    authStore.error = 'Please fill in all fields.';
    return;
  }
  const success = await authStore.login({ email: email.value, password: password.value });
  if (success) {
    isModalOpen.value = false;
  }
};

const switchToRegister = () => {
  isModalOpen.value = false;
  emit('openRegister');
};
const handleResendActivation = async () => {
  await authStore.resendActivationEmail(email.value);
};
</script>

<template>
  <UiDropdown origin="bottom" align="right">
    <template #trigger="{ toggle }">
      <button
        @click="toggle"
        class="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-primary-dark focus:ring-primary-red"
      >
        <img
          class="h-8 w-8 rounded-full bg-primary-gray text-primary-smoke flex items-center justify-center"
          :src="avatar"
          :alt="email || 'User'"
        />
      </button>
    </template>
    <template #default="{ close }">
      <div class="px-4 py-3 border-b border-primary-gray">
        <p class="text-sm text-primary-smoke">Signed in as</p>
        <p class="text-sm font-medium text-primary-smoke truncate">{{ email }}</p>
      </div>
      <NuxtLink
        to="/profile"
        @click="close"
        class="block px-4 py-2 text-sm text-primary-smoke hover:font-bold"
        role="menuitem"
      >
        Your Profile
      </NuxtLink>
      <NuxtLink
        to="/uploads"
        @click="close"
        class="block px-4 py-2 text-sm text-primary-smoke hover:font-bold"
        role="menuitem"
      >
        My Uploads
      </NuxtLink>
      <NuxtLink
        to="/settings"
        @click="close"
        class="block px-4 py-2 text-sm text-primary-smoke hover:font-bold"
        role="menuitem"
      >
        Settings
      </NuxtLink>
      <button
        @click="emit('logout')"
        class="block w-full text-left px-4 py-2 text-sm text-primary-red hover:bg-primary-red/20 hover:font-bold"
        role="menuitem"
      >
        Sign Out
      </button>
    </template>
  </UiDropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UiDropdown from '~/components/ui/Dropdown.vue'

interface Props {
  email: string | undefined
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'logout'): void
}>()

const avatar = computed(() => {
  // Extract name from email or use a better fallback
  const emailUsername = props.email ? props.email.split('@')[0] : 'Anonymous User';
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(emailUsername)}&background=150050&color=FB2576&size=32`;
})
</script>

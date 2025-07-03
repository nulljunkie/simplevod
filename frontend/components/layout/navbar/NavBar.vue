<template>
  <nav class="flex items-center justify-between h-14 pl-8 pr-4 shadow-lg">
    <!-- left: brand -->
    <NavBrand :appName="appName" />

    <!-- center: search -->
    <NavSearchBar v-model="searchQuery" @search="performSearch" />

    <!-- right: actions -->
    <div class="flex items-center space-x-4">
      <UploadProgress />

      <NavAuthButtons
        :isAuthenticated="authStore.isAuthenticated"
        @open-login="isLoginModalOpen = true"
        @open-register="isRegisterModalOpen = true"
      />

      <template v-if="authStore.isAuthenticated" >
        <NavUploadButton @upload="openUploadModal" />
        <NavProfileMenu :email="authStore.user?.email" @logout="logout" />
      </template>
    </div>
  </nav>

  <!-- Modals / teleports -->
  <Teleport to="body">
    <UploadModal v-model="isUploadModalOpen" />
  </Teleport>
  <AuthLoginModal
    v-model="isLoginModalOpen"
    @open-register="isLoginModalOpen = false; isRegisterModalOpen = true;"
  />
  <AuthRegisterModal
    v-model="isRegisterModalOpen"
    @open-login="isRegisterModalOpen = false; isLoginModalOpen = true;"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '~/stores/auth'

import NavBrand from './NavBrand.vue'
import NavSearchBar from './NavSearchBar.vue'
import NavAuthButtons from './NavAuthButtons.vue'
import NavUploadButton from './NavUploadButton.vue'
import NavProfileMenu from './NavProfileMenu.vue'

import UploadProgress from '~/components/upload/Progress.vue'
import UploadModal from '~/components/upload/Modal.vue'
import AuthLoginModal from '~/components/auth/LoginModal.vue'
import AuthRegisterModal from '~/components/auth/RegisterModal.vue'

const config = useRuntimeConfig()
const appName = config.public.appName

const authStore = useAuthStore()
const router = useRouter()

const searchQuery = ref('')
const isLoginModalOpen = ref(false)
const isRegisterModalOpen = ref(false)
const isUploadModalOpen = ref(false)

function performSearch() {
  if (searchQuery.value.trim()) {
    router.push(`/search?q=${encodeURIComponent(searchQuery.value.trim())}`)
  }
}

function openUploadModal() {
  if (!authStore.isAuthenticated) {
    isLoginModalOpen.value = true
  } else {
    isUploadModalOpen.value = true
  }
}

async function logout() {
  await authStore.logout()
  router.push('/')
}
</script>

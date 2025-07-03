<template>
  <Transition
    enter-active-class="transition ease-out duration-100"
    enter-from-class="transform opacity-0 scale-95"
    enter-to-class="transform opacity-100 scale-100"
    leave-active-class="transition ease-in duration-75"
    leave-from-class="transform opacity-100 scale-100"
    leave-to-class="transform opacity-0 scale-95"
  >
    <div
      v-if="uploadsStore.isUploadPanelOpen && uploadsStore.activeUploads.length > 0"
      class="absolute top-14 right-0 sm:right-4 mt-2 w-80 sm:w-96 bg-primary-dark rounded-md shadow-xl z-30 border border-primary-gray"
    >
      <!-- Header  -->
      <div class="px-4 py-3 border-b border-primary-gray flex justify-between items-center">
        <h3 class="text-sm font-medium text-primary-smoke">
          {{ uploadingCount > 0 ? `Uploading ${uploadingCount} file(s)` : 'Uploads' }}
        </h3>
        <button @click="uploadsStore.toggleUploadPanel()" class="text-primary-silver hover:text-primary-smoke">
          <XMarkIcon class="h-5 w-5" />
        </button>
      </div>

      <!-- Body  -->
      <div class="max-h-80 overflow-y-auto p-2 space-y-2 custom-scrollbar">
        <div v-if="uploadsStore.activeUploads.length === 0" class="p-4 text-center text-sm text-text-muted">
          No active uploads.
        </div>

        <!-- Items -->
        <div
          v-for="upload in uploadsStore.activeUploads"
          :key="upload.id"
          class="p-3 border border-primary-gray bg-primary-dark rounded-md"
        >
          <div class="flex items-center justify-between">
            <p class="text-xs font-medium text-primary-smoke truncate w-4/5" :title="upload.file.name">
              {{ upload.file.name }}
            </p>
            <div class="flex items-center space-x-1">

              <!-- Pause button -->
              <template v-if="upload.status === 'uploading' || upload.status === 'pending'">
                 <UiButton variant="icon" size="xs" @click="uploadsStore.pauseUpload(upload.id)" title="Pause">
                    <PauseIcon class="h-4 w-4 text-primary-silver hover:text-primary-smoke"/>
                 </UiButton>
              </template>

              <!-- Resume button -->
              <template v-if="upload.status === 'paused'">
                 <UiButton variant="icon" size="xs" @click="uploadsStore.resumeUpload(upload.id)" title="Resume">
                    <PlayIcon class="h-4 w-4 text-primary-silver hover:text-primary-smoke"/>
                 </UiButton>
              </template>

              <!-- Retry button -->
               <template v-if="upload.status === 'failed'">
                 <UiButton variant="icon" size="xs" @click="uploadsStore.retryUpload(upload.id)" title="Retry">
                    <ArrowPathIcon class="h-4 w-4 text-primary-error/95 hover:text-primary-error"/>
                 </UiButton>
              </template>

              <!-- Cancel button -->
              <UiButton variant="icon" size="xs" @click="uploadsStore.cancelUpload(upload.id)" title="Cancel">
                <XCircleIcon class="h-4 w-4 text-primary-silver hover:text-primary-error" />
              </UiButton>

            </div>
          </div>

          <!-- Progress Bar -->
          <UiProgressBar :progress="upload.progress" class="mt-1.5 h-1.5" />
          <!-- Progress ratio -->
          <div class="mt-1 flex justify-between text-xs text-primary-silver">
            <span>{{ formatFileSize(upload.file.size * (upload.progress / 100)) }} / {{ formatFileSize(upload.file.size) }}</span>
            <!-- Progress state -->
            <span :class="{
              'text-primary-smoke': upload.status === 'uploading',
              'text-primary-silver': upload.status === 'paused',
              'text-primary-success': upload.status === 'completed',
              'text-primary-error': upload.status === 'failed' || upload.status === 'cancelling',
            }">{{ uploadStatusText(upload) }}</span>
          </div>
          <!-- Error Message -->
          <p v-if="upload.errorMessage" class="mt-1 text-xs text-primary-error">
            Error: {{ upload.errorMessage }}
          </p>
        </div>
      </div>
      
      <!-- Clear compeleted uploads button -->
      <div v-if="completedCount > 0 && uploadingCount === 0" class="p-3 border-t border-primary-gray text-center">
        <UiButton 
          variant="secondary" 
          size="sm" @click="clearCompleted"
          customClass="!text-primary-success !border-primary-success hover:bg-primary-success/10"
          >
          Clear Completed
        </UiButton>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useUploadsStore } from '~/stores/uploads';
import type { UploadFile } from '~/types/upload';
import UiProgressBar from '~/components/ui/ProgressBar.vue';
import UiButton from '~/components/ui/Button.vue';
import { XMarkIcon, PauseIcon, PlayIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/vue/20/solid';

const uploadsStore = useUploadsStore();

const uploadingCount = computed(() => uploadsStore.activeUploads.filter(u => u.status === 'uploading' || u.status === 'pending').length);
const completedCount = computed(() => uploadsStore.activeUploads.filter(u => u.status === 'completed').length);


const formatFileSize = (bytes: number, decimals = 1) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const uploadStatusText = (upload: UploadFile): string => {
  switch (upload.status) {
    case 'pending': return 'Pending...';
    case 'uploading': return `${upload.progress}%`;
    case 'paused': return 'Paused';
    case 'completed': return 'Completed';
    case 'failed': return 'Failed';
    case 'cancelling': return 'Cancelling...';
    default: return '';
  }
};

const clearCompleted = () => {
    uploadsStore.clearCompletedUploads();
};
</script>



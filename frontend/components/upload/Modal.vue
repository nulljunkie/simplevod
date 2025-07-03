<template>
  <UiModal v-model="isModalOpen" title="Upload Video" max-width="2xl">
    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Video File Drag & Drop -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-primary-smoke">Video File *</label>
        <div
          @drop="handleVideoDrop"
          @dragover.prevent
          @dragenter.prevent="videoIsDragging = true"
          @dragleave.prevent="videoIsDragging = false"
          @click="triggerVideoUpload"
          :class="[
            'relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200',
            videoIsDragging || videoFile 
              ? 'border-primary-red bg-primary-red/5' 
              : 'border-primary-gray hover:border-primary-red/50 hover:bg-primary-red/5'
          ]"
        >
          <input
            ref="videoInput"
            type="file"
            accept="video/*"
            class="hidden"
            @change="handleVideoSelect"
            required
          />
          
          <div v-if="!videoFile" class="space-y-3">
            <VideoCameraIcon class="h-12 w-12 text-primary-silver mx-auto" />
            <div>
              <p class="text-primary-smoke font-medium">
                {{ videoIsDragging ? 'Drop your video here' : 'Drag & drop your video here' }}
              </p>
              <p class="text-primary-silver text-sm">or click to browse files</p>
            </div>
            <p class="text-xs text-primary-silver">Supports MP4, MOV, AVI, and more</p>
          </div>
          
          <div v-else class="space-y-3">
            <CheckCircleIcon class="h-12 w-12 text-primary-red mx-auto" />
            <div>
              <p class="text-primary-smoke font-medium">{{ videoFile.name }}</p>
              <p class="text-primary-silver text-sm">{{ formatFileSize(videoFile.size) }}</p>
            </div>
            <button
              type="button"
              @click.stop="clearVideo"
              class="text-sm text-primary-red hover:text-primary-red/80 transition-colors"
            >
              Remove video
            </button>
          </div>
        </div>
      </div>

      <!-- Thumbnail Drag & Drop -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-primary-smoke">Thumbnail (Optional)</label>
        <div
          @drop="handleThumbnailDrop"
          @dragover.prevent
          @dragenter.prevent="thumbnailIsDragging = true"
          @dragleave.prevent="thumbnailIsDragging = false"
          @click="triggerThumbnailUpload"
          :class="[
            'relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200',
            thumbnailIsDragging || thumbnail 
              ? 'border-primary-red bg-primary-red/5' 
              : 'border-primary-gray hover:border-primary-red/50 hover:bg-primary-red/5'
          ]"
        >
          <input
            ref="thumbnailInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleThumbnailSelect"
          />
          
          <div v-if="!thumbnail" class="space-y-2">
            <PhotoIcon class="h-8 w-8 text-primary-silver mx-auto" />
            <div>
              <p class="text-primary-smoke text-sm">
                {{ thumbnailIsDragging ? 'Drop thumbnail here' : 'Drag & drop thumbnail' }}
              </p>
              <p class="text-primary-silver text-xs">or click to browse</p>
            </div>
          </div>
          
          <div v-else class="space-y-2">
            <img 
              :src="thumbnailPreview" 
              alt="Thumbnail Preview" 
              class="h-20 w-auto mx-auto rounded-md border border-primary-gray"
            />
            <div>
              <p class="text-primary-smoke text-sm font-medium">{{ thumbnail.name }}</p>
              <button
                type="button"
                @click.stop="clearThumbnail"
                class="text-sm text-primary-red hover:text-primary-red/80 transition-colors"
              >
                Remove thumbnail
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Title Input -->
      <div class="space-y-2">
        <label for="title" class="block text-sm font-medium text-primary-smoke">Title *</label>
        <input
          id="title"
          v-model="title"
          type="text"
          placeholder="Enter a compelling title for your video"
          class="w-full px-4 py-3 border border-primary-gray rounded-lg bg-primary-dark text-primary-smoke placeholder-primary-silver focus:outline-none focus:ring-2 focus:ring-primary-red focus:border-transparent transition-colors"
          required
        />
      </div>

      <!-- Description Input -->
      <div class="space-y-2">
        <label for="description" class="block text-sm font-medium text-primary-smoke">Description (Optional)</label>
        <textarea
          id="description"
          v-model="description"
          rows="4"
          placeholder="Tell viewers about your video (optional)"
          class="w-full px-4 py-3 border border-primary-gray rounded-lg bg-primary-dark text-primary-smoke placeholder-primary-silver focus:outline-none focus:ring-2 focus:ring-primary-red focus:border-transparent transition-colors resize-none"
        ></textarea>
      </div>

      <!-- Visibility Toggle -->
      <div class="space-y-3">
        <label class="block text-sm font-medium text-primary-smoke">Visibility</label>
        <div class="flex space-x-6">
          <label class="flex items-center cursor-pointer">
            <input
              type="radio"
              v-model="visibility"
              value="public"
              class="sr-only"
            />
            <div :class="[
              'flex items-center space-x-3 px-4 py-3 rounded-lg border-2 transition-all duration-200',
              visibility === 'public' 
                ? 'border-primary-red bg-primary-red/10' 
                : 'border-primary-gray hover:border-primary-red/50'
            ]">
              <GlobeAltIcon class="h-5 w-5 text-primary-smoke" />
              <div>
                <p class="text-sm font-medium text-primary-smoke">Public</p>
                <p class="text-xs text-primary-silver">Anyone can view</p>
              </div>
            </div>
          </label>
          
          <label class="flex items-center cursor-pointer">
            <input
              type="radio"
              v-model="visibility"
              value="private"
              class="sr-only"
            />
            <div :class="[
              'flex items-center space-x-3 px-4 py-3 rounded-lg border-2 transition-all duration-200',
              visibility === 'private' 
                ? 'border-primary-red bg-primary-red/10' 
                : 'border-primary-gray hover:border-primary-red/50'
            ]">
              <LockClosedIcon class="h-5 w-5 text-primary-smoke" />
              <div>
                <p class="text-sm font-medium text-primary-smoke">Private</p>
                <p class="text-xs text-primary-silver">Only you can view</p>
              </div>
            </div>
          </label>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-end space-x-3 pt-4 border-t border-primary-gray">
        <UiButton variant="secondary" @click="isModalOpen = false">Cancel</UiButton>
        <UiButton 
          type="submit" 
          variant="primary" 
          :disabled="!videoFile || !title.trim()"
          class="min-w-[100px]"
        >
          Upload Video
        </UiButton>
      </div>
    </form>
  </UiModal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import UiModal from '~/components/ui/Modal.vue';
import UiButton from '~/components/ui/Button.vue';
import { useUploadsStore } from '~/stores/uploads';
import { 
  VideoCameraIcon, 
  PhotoIcon, 
  CheckCircleIcon, 
  GlobeAltIcon, 
  LockClosedIcon 
} from '@heroicons/vue/24/outline';

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits(['update:modelValue']);

const isModalOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const uploadsStore = useUploadsStore();

// Form state
const videoFile = ref<File | null>(null);
const videoDuration = ref<number | null>(null);
const title = ref<string>('');
const description = ref<string>('');
const visibility = ref<'public' | 'private'>('public');
const thumbnail = ref<File | null>(null);
const thumbnailPreview = ref<string | null>(null);

// Drag state
const videoIsDragging = ref(false);
const thumbnailIsDragging = ref(false);

// Refs for file inputs
const videoInput = ref<HTMLInputElement>();
const thumbnailInput = ref<HTMLInputElement>();

// Utility function to format file size
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Utility function to get video duration
function getVideoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';
    video.onloadedmetadata = () => {
      resolve(video.duration);
      URL.revokeObjectURL(video.src);
    };
    video.onerror = () => {
      reject(new Error('Failed to load video metadata'));
      URL.revokeObjectURL(video.src);
    };
    video.src = URL.createObjectURL(file);
  });
}

// Video file handlers
function triggerVideoUpload() {
  videoInput.value?.click();
}

async function handleVideoSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    const file = input.files[0];
    videoFile.value = file;
    
    // Extract duration
    try {
      const duration = await getVideoDuration(file);
      videoDuration.value = duration;
    } catch (error) {
      console.warn('Could not extract video duration:', error);
      videoDuration.value = null;
    }
  }
}

async function handleVideoDrop(event: DragEvent) {
  event.preventDefault();
  videoIsDragging.value = false;
  
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (file.type.startsWith('video/')) {
      videoFile.value = file;
      
      // Extract duration
      try {
        const duration = await getVideoDuration(file);
        videoDuration.value = duration;
      } catch (error) {
        console.warn('Could not extract video duration:', error);
        videoDuration.value = null;
      }
    }
  }
}

function clearVideo() {
  videoFile.value = null;
  videoDuration.value = null;
  if (videoInput.value) {
    videoInput.value.value = '';
  }
}

// Thumbnail file handlers
function triggerThumbnailUpload() {
  thumbnailInput.value?.click();
}

function handleThumbnailSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    thumbnail.value = input.files[0];
    thumbnailPreview.value = URL.createObjectURL(thumbnail.value);
  }
}

function handleThumbnailDrop(event: DragEvent) {
  event.preventDefault();
  thumbnailIsDragging.value = false;
  
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (file.type.startsWith('image/')) {
      thumbnail.value = file;
      thumbnailPreview.value = URL.createObjectURL(file);
    }
  }
}

function clearThumbnail() {
  thumbnail.value = null;
  thumbnailPreview.value = null;
  if (thumbnailInput.value) {
    thumbnailInput.value.value = '';
  }
}

// Form submission
function handleSubmit() {
  if (!videoFile.value || !title.value.trim()) return;

  uploadsStore.addFileToUploadQueue({
    file: videoFile.value,
    title: title.value.trim(),
    description: description.value.trim() || undefined,
    visibility: visibility.value,
    thumbnail: thumbnail.value || undefined,
    duration: videoDuration.value || undefined,
  });

  // Reset form
  videoFile.value = null;
  videoDuration.value = null;
  title.value = '';
  description.value = '';
  visibility.value = 'public';
  clearThumbnail();
  
  isModalOpen.value = false;
}
</script>

<template>
  <div class="bg-primary-dark border border-primary-gray rounded-lg p-6 animate-pulse">
    <div class="flex items-start space-x-6">
      <!-- Thumbnail Skeleton -->
      <div class="flex-shrink-0">
        <div class="w-48 h-32 bg-primary-skeleton rounded-lg"></div>
      </div>

      <!-- Video Details Skeleton -->
      <div class="flex-1 space-y-4">
        <!-- Title with Edit Icon -->
        <div class="flex items-center space-x-2">
          <div class="h-6 bg-primary-skeleton rounded w-64"></div>
          <div class="w-4 h-4 bg-primary-skeleton rounded"></div>
        </div>

        <!-- File Info Row -->
        <div class="grid grid-cols-2 gap-8">
          <div class="flex items-center space-x-2">
            <div class="h-4 bg-primary-skeleton rounded w-16"></div>
            <div class="h-4 bg-primary-skeleton rounded w-24"></div>
          </div>
          <div class="flex items-center space-x-2">
            <div class="h-4 bg-primary-skeleton rounded w-12"></div>
            <div class="h-6 bg-primary-skeleton rounded-full w-20"></div>
          </div>
        </div>

        <!-- Duration and Upload Time Row -->
        <div class="grid grid-cols-2 gap-8">
          <div class="flex items-center space-x-2">
            <div class="h-4 bg-primary-skeleton rounded w-16"></div>
            <div class="h-4 bg-primary-skeleton rounded w-16"></div>
          </div>
          <div class="flex items-center space-x-2">
            <div class="h-4 bg-primary-skeleton rounded w-16"></div>
            <div class="h-4 bg-primary-skeleton rounded w-20"></div>
          </div>
        </div>

        <!-- Visibility Row -->
        <div class="flex items-center space-x-4">
          <div class="h-4 bg-primary-skeleton rounded w-16"></div>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div class="w-4 h-4 bg-primary-skeleton rounded-full"></div>
              <div class="h-4 bg-primary-skeleton rounded w-12"></div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-4 h-4 bg-primary-skeleton rounded-full"></div>
              <div class="h-4 bg-primary-skeleton rounded w-14"></div>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <div class="h-4 bg-primary-skeleton rounded w-20"></div>
            <div class="w-3 h-3 bg-primary-skeleton rounded"></div>
          </div>
          <div class="space-y-1">
            <div class="h-4 bg-primary-skeleton rounded w-full"></div>
            <div class="h-4 bg-primary-skeleton rounded w-3/4"></div>
            <div class="h-4 bg-primary-skeleton rounded w-1/2"></div>
          </div>
        </div>
      </div>

      <!-- Delete Button Skeleton -->
      <div class="flex-shrink-0">
        <div class="w-9 h-9 bg-primary-skeleton rounded"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// No props needed for skeleton
</script>

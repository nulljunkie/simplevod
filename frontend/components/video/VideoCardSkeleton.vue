<template>
  <div class="space-y-3 animate-pulse">
    <!-- Thumbnail Section - matches UiVideoThumbnail -->
    <div class="relative border border-primary-skeleton rounded-lg overflow-hidden aspect-[16/9]">
      <!-- Thumbnail placeholder -->
      <div class="w-full h-full bg-primary-skeleton"></div>
      <!-- Duration placeholder (bottom-right) -->
      <div class="absolute bottom-2 right-2 bg-primary-skeleton rounded h-4 w-12"></div>
    </div>
    
    <!-- Info Section - matches VideoCard info structure -->
    <div class="space-y-2">
      <!-- Video title - 2 lines like line-clamp-2 -->
      <div class="space-y-1">
        <div class="h-4 bg-primary-skeleton rounded w-full"></div>
        <div class="h-4 bg-primary-skeleton rounded w-3/4"></div>
      </div>
      
      <!-- User section - matches UiVideoOwner structure -->
      <div class="flex items-center space-x-2">
        <!-- Avatar placeholder -->
        <div class="w-8 h-8 bg-primary-skeleton rounded-full flex-shrink-0"></div>
        <!-- Username placeholder -->
        <div class="h-3 bg-primary-skeleton rounded w-24"></div>
      </div>
      
      <!-- Views and upload date - matches the flex layout -->
      <div class="flex items-center space-x-2">
        <div class="h-3 bg-primary-skeleton rounded w-16"></div>
        <div class="w-1 h-1 bg-primary-skeleton rounded-full"></div>
        <div class="h-3 bg-primary-skeleton rounded w-20"></div>
      </div>
    </div>
  </div>
</template>

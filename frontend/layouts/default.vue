<template>
  <div class="min-h-screen flex flex-col bg-primary-dark text-primary-smoke">
    <LayoutNavbarNavBar />
    <main class="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <slot /> 
    </main>
  </div>
</template>

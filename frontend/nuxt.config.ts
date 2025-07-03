export default defineNuxtConfig({
  devtools: { enabled: true },
  ssr: true,

  app: {
    head: {
      title: process.env.NUXT_PUBLIC_APP_NAME || 'Video Platform',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { hid: 'description', name: 'description', content: 'Simple Video on Demand Platform' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon-32x32.png' }
      ]
    }
  },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],

  tailwindcss: {
    cssPath: '~/assets/css/tailwind.css',
    configPath: 'tailwind.config',
    exposeConfig: false,
    viewer: true, // Enables Tailwind CSS viewer in dev mode
  },

  runtimeConfig: {
    // Server-only URLs (internal cluster communication)
    authServiceUrl: process.env.NUXT_AUTH_SERVICE_URL,
    streamServiceUrl: process.env.NUXT_STREAM_SERVICE_URL,
    uploadServiceUrl: process.env.NUXT_UPLOAD_SERVICE_URL,
    
    // Keys within public are also exposed client-side (external URLs)
    public: {
      authServiceUrl: process.env.NUXT_PUBLIC_AUTH_SERVICE_URL,
      streamServiceUrl: process.env.NUXT_PUBLIC_STREAM_SERVICE_URL,
      uploadServiceUrl: process.env.NUXT_PUBLIC_UPLOAD_SERVICE_URL,
      appName: process.env.NUXT_PUBLIC_APP_NAME,
      uploadChunkSizeMb: parseInt(process.env.NUXT_PUBLIC_UPLOAD_CHUNK_SIZE_MB || '5'),
      uploadConcurrentChunks: parseInt(process.env.NUXT_PUBLIC_UPLOAD_CONCURRENT_CHUNKS || '3'),
    }
  },

  // If you need to transpile hls.js (usually not necessary with modern bundlers)
  // build: {
  //   transpile: ['hls.js'],
  // },

  // Define aliases for easier imports
  alias: {
    '@': '/<rootDir>',
    '~/types': '/<rootDir>/types',
  }
})

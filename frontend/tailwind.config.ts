import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: [
    './components/**/*.{js,vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.{js,ts}',
    './nuxt.config.{js,ts}',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          dark: '#000000',     // bg
          red: '#b3003d',      // main
          smoke: '#f2ede4',    // text
          silver: '#9ca3af',   // text
          gray: '#2a2e2f',     // borders
          success: '#10b981',  // successes
          error: '#ef4444',    // errors
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
  ],
} satisfies Config

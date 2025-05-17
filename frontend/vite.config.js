import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // Proxy API requests to the local backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    // Generate manifest.json for Cloudflare
    manifest: true,
    rollupOptions: {
      // External dependencies that shouldn't be bundled
      external: []
    }
  }
})

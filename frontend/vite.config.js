import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  // Specify the correct entry point
  root: __dirname,
  build: {
    outDir: './dist',
    target: 'esnext',
    minify: 'terser',
    emptyOutDir: true
  },
  resolve: {
    extensions: ['.ts', '.js', '.json']
  },
  server: {
    proxy: {
      // Proxy API requests to the local backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

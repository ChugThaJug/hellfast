import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  
  // Fix dependency optimization issues
  optimizeDeps: {
    exclude: ['clsx', 'lucide-svelte'],
    include: ['devalue'],
  },
  
  // Increase build timeouts
  build: {
    rollupOptions: {
      // This helps with large dependencies
      maxParallelFileOps: 3,
    },
    // Increase timeout for large dependencies
    timeout: 120000,
  },
  
  // Dev server settings
  server: {
    fs: {
      strict: false, // This can help with certain module resolution issues
    },
    hmr: {
      overlay: true, // Show errors as overlay
    },
  }
});
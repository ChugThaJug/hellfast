import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  // Load env variables
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [sveltekit()],
    
    // Define global environment variables to be replaced in the build
    define: {
      // Ensure these values are available in both dev and build
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://localhost:8000'),
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || 'http://localhost:8000'),
    },
    
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
    },
    
    // SSR specific options
    ssr: {
      // Avoid SSR of certain dependencies that use browser APIs
      noExternal: ['lucide-svelte'],
      // External packages that shouldn't be bundled
      external: ['firebase', '@firebase/app'],
    }
  };
});
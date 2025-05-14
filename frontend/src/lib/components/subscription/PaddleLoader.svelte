<!-- frontend/src/lib/components/subscription/PaddleLoader.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  export let vendorId: string;
  export let sandbox: boolean = true;
  
  onMount(() => {
    if (browser) {
      // Load Paddle.js script
      const script = document.createElement('script');
      script.src = 'https://cdn.paddle.com/paddle/paddle.js';
      script.async = true;
      
      script.onload = () => {
        // Initialize Paddle
        if (window.Paddle) {
          // Set environment
          window.Paddle.Environment.set(sandbox ? 'sandbox' : 'production');
          
          // Setup Paddle
          window.Paddle.Setup({ vendor: vendorId });
          console.log('Paddle initialized');
        }
      };
      
      document.head.appendChild(script);
      
      // Cleanup on component unmount
      return () => {
        document.head.removeChild(script);
      };
    }
  });
</script>
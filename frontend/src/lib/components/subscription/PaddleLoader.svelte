<!-- frontend/src/lib/components/subscription/PaddleLoader.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  export let vendorId: string;
  export let sandbox: boolean = true;
  
  let loaded = false;
  
  onMount(() => {
    if (browser) {
      // Check if Paddle is already loaded
      if (window.Paddle) {
        initializePaddle();
        return;
      }
      
      // Load Paddle.js script
      const script = document.createElement('script');
      script.src = 'https://cdn.paddle.com/paddle/paddle.js';
      script.async = true;
      script.defer = true;
      
      script.onload = () => {
        initializePaddle();
      };
      
      document.head.appendChild(script);
      
      // Cleanup on component unmount
      return () => {
        if (!loaded) {
          document.head.removeChild(script);
        }
      };
    }
  });
  
  function initializePaddle() {
    // Initialize Paddle
    if (window.Paddle) {
      try {
        // Set environment
        window.Paddle.Environment.set(sandbox ? 'sandbox' : 'production');
        
        // Setup Paddle
        window.Paddle.Setup({ vendor: vendorId });
        loaded = true;
        console.log('Paddle initialized successfully');
        
        // Dispatch event that Paddle is loaded
        window.dispatchEvent(new CustomEvent('paddle-initialized'));
      } catch (error) {
        console.error('Error initializing Paddle:', error);
      }
    }
  }
</script>

{#if !loaded}
  <!-- Hidden loading indicator -->
  <div class="hidden">Loading Paddle...</div>
{/if}
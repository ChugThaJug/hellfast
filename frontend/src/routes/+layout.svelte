<script lang="ts">
  import '../app.css';
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  
  // Use $props() rune instead of export let
  let { data = {} } = $props<{ data?: any }>();
  
  // Track if component is mounted
  let mounted = $state(false);
  
  onMount(() => {
    mounted = true;
  });
</script>

{#if browser && mounted}
  <!-- Only render when in browser and component is mounted -->
  <slot />
{:else}
  <!-- Simple loading state for SSR or before hydration -->
  <div class="loading-container">
    <p>Loading...</p>
  </div>
{/if}

<style>
  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    width: 100%;
    font-family: system-ui, -apple-system, sans-serif;
  }
</style>
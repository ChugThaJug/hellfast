<script lang="ts">
  import '../app.css';
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import Header from '$lib/components/layout/Header.svelte';
  import Footer from '$lib/components/layout/Footer.svelte';
  
  // Use $props() rune instead of export let
  let { data = {} } = $props<{ data?: any }>();
  
  // Track if component is mounted
  let mounted = $state(false);
  
  onMount(() => {
    mounted = true;
  });
</script>

{#if browser && mounted}
  <!-- Add Header to all pages -->
  <div class="flex min-h-screen flex-col">
    <Header />
    <main class="flex-1">
      <slot />
    </main>
    <Footer />
  </div>
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
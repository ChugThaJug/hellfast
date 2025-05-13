<!-- frontend/src/lib/components/auth/ProtectedRoute.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  
  export let requireAuth = true;
  export let redirectTo = '/auth/login';
  
  let initialized = false;

  onMount(async () => {
    if (browser) {
      // Initialize auth if not already done
      if (!$auth.authenticated && !$auth.loading) {
        await auth.initialize();
      }
      
      initialized = true;
    }
  });
  
  // Handle authenticated route
  $: if (browser && initialized && requireAuth && !$auth.authenticated && !$auth.loading) {
    goto(redirectTo);
  }
  
  // Handle non-authenticated route (like /login when already logged in)
  $: if (browser && initialized && !requireAuth && $auth.authenticated && !$auth.loading) {
    goto('/dashboard');
  }
</script>

{#if $auth.loading}
  <div class="flex justify-center items-center min-h-[50vh]">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
{:else if (!requireAuth || $auth.authenticated)}
  <slot />
{/if}
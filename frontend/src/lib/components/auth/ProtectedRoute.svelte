<!-- src/lib/components/auth/ProtectedRoute.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  
  // Using Svelte 5 props
  let { 
    requireAuth = true,
    redirectTo = '/auth/login'
  } = $props<{
    requireAuth?: boolean;
    redirectTo?: string;
  }>();
  
  let initialized = $state(false);

  onMount(async () => {
    if (browser) {
      // Initialize auth if not already done
      if (!$auth.authenticated && !$auth.loading) {
        await auth.initialize();
      }
      
      initialized = true;
    }
  });
  
  // Using $effect for reactive code
  $effect(() => {
    if (browser && initialized && requireAuth && !$auth.authenticated && !$auth.loading) {
      goto(redirectTo);
    }
  });
  
  $effect(() => {
    if (browser && initialized && !requireAuth && $auth.authenticated && !$auth.loading) {
      goto('/dashboard');
    }
  });
</script>

{#if $auth.loading}
  <div class="flex justify-center items-center min-h-[50vh]">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
{:else if (!requireAuth || $auth.authenticated)}
  <slot />
{/if}
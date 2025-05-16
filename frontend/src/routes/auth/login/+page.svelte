// frontend/src/routes/auth/login/+page.svelte
<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { auth } from "$lib/stores/auth";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  
  let loading = false;
  let apiBaseUrl = '';
  
  onMount(() => {
    // Get API URL from environment variable or use default
    apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    console.log("API Base URL:", apiBaseUrl);
    
    // Check for error in URL params
    if ($page.url.searchParams.get("error")) {
      auth.setError("Authentication failed. Please try again.");
    }
  });
  
  function handleGoogleLogin() {
    try {
      console.log("Google login button clicked");
      loading = true;
      
      // Direct OAuth flow - ensure we use window.location.href for proper page navigation
      const loginUrl = `${apiBaseUrl}/oauth/google/login`;
      console.log("Redirecting to:", loginUrl);
      window.location.href = loginUrl;
    } catch (error) {
      console.error("Login error:", error);
      auth.setError("Login failed: " + (error instanceof Error ? error.message : "Unknown error"));
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Sign In - Stepify</title>
</svelte:head>

<div class="container mx-auto px-4 py-16">
  <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm">
    <h1 class="text-2xl font-bold mb-6 text-center">Sign In to Stepify</h1>
    
    {#if $auth.error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {$auth.error}
      </div>
    {/if}
    
    <p class="text-center mb-8">
      Use your Google account to sign in securely to your Stepify account.
    </p>
    
    <div class="mt-4">
      <button 
        class="w-full px-4 py-2 border border-border rounded-md hover:bg-muted flex items-center justify-center"
        on:click={handleGoogleLogin}
        disabled={loading}
        type="button"
      >
        {#if loading}
          <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
          <span>Connecting to Google...</span>
        {:else}
          <!-- Google icon -->
          <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path d="M12.545 10.239v3.821h5.445c-0.712 2.315-2.647 3.972-5.445 3.972-3.332 0-6.033-2.701-6.033-6.032s2.701-6.032 6.033-6.032c1.498 0 2.866 0.549 3.921 1.453l2.814-2.814c-1.798-1.677-4.198-2.701-6.735-2.701-5.539 0-10.032 4.493-10.032 10.032s4.493 10.032 10.032 10.032c5.539 0 9.366-3.895 9.366-9.373 0-0.703-0.077-1.377-0.219-2.017h-9.147z" fill="currentColor"></path>
          </svg>
          <span>Sign in with Google</span>
        {/if}
      </button>
    </div>
    
    <div class="mt-8 text-center text-sm">
      <p>
        By signing in, you agree to our 
        <a href="/terms" class="text-primary hover:underline">Terms of Service</a> and 
        <a href="/privacy" class="text-primary hover:underline">Privacy Policy</a>
      </p>
    </div>
  </div>
</div>
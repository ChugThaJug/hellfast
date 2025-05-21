<!-- src/routes/auth/oauth-success/+page.svelte -->
<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { auth } from "$lib/stores/auth";
  
  let loading = $state(true);
  let error = $state(null);
  
  onMount(async () => {
    try {
      console.log("OAuth success page loaded");
      
      // Get access token from URL parameters
      const accessToken = $page.url.searchParams.get("access_token");
      const tokenType = $page.url.searchParams.get("token_type");
      
      if (!accessToken) {
        console.error("No access token found in URL");
        error = "No access token found in URL";
        loading = false;
        return;
      }
      
      console.log("Access token received, logging in...");
      
      // Store token in localStorage and login
      await auth.loginWithToken(accessToken);
      
      // Get redirect path or default to dashboard
      const redirectPath = localStorage.getItem('auth_redirect') || '/dashboard';
      localStorage.removeItem('auth_redirect');
      
      console.log(`Redirecting to: ${redirectPath}`);
      
      // Redirect to saved path or dashboard
      goto(redirectPath);
    } catch (err) {
      console.error("OAuth success error:", err);
      error = err instanceof Error ? err.message : "Failed to process OAuth login";
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Logging In - Stepify</title>
</svelte:head>

<div class="container mx-auto px-4 py-16">
  <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm">
    {#if loading}
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <h1 class="text-2xl font-bold mb-2">Logging you in...</h1>
        <p class="text-foreground/70">Please wait while we complete the authentication process.</p>
      </div>
    {:else if error}
      <div class="text-center">
        <h1 class="text-2xl font-bold mb-2 text-destructive">Authentication Failed</h1>
        <p class="text-foreground/70 mb-4">{error}</p>
        <a 
          href="/auth/login" 
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 inline-block"
        >
          Back to Login
        </a>
      </div>
    {/if}
  </div>
</div>
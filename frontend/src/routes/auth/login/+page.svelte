<!-- src/routes/auth/login/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { auth } from "$lib/stores/auth";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  
  let email = "";
  let password = "";
  let loading = false;
  
  // Check for error in URL params
  $: if ($page.url.searchParams.get("error")) {
    auth.setError("Authentication failed. Please try again.");
  }
  
  async function handleLogin() {
    if (!email || !password) {
      auth.setError("Please enter both email and password");
      return;
    }
    
    loading = true;
    auth.clearError();
    
    try {
      // For development mode, use the development login
      if (import.meta.env.DEV || window.location.hostname === 'localhost') {
        await auth.loginDevelopment();
        goto("/dashboard");
        return;
      }
      
      // For production, implement proper Firebase auth
      // This is a placeholder - you would implement real Firebase login here
      auth.setError("Firebase auth not implemented yet. In development mode, you can login without credentials.");
      loading = false;
    } catch (err) {
      console.error("Login error:", err);
      loading = false;
    }
  }
  
  function handleGoogleLogin() {
    // Redirect to Google OAuth URL
    window.location.href = "/oauth/google/login";
  }
</script>

<svelte:head>
  <title>Sign In - Stepify</title>
</svelte:head>

<ProtectedRoute requireAuth={false} redirectTo="/dashboard">
  <div class="container mx-auto px-4 py-16">
    <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm">
      <h1 class="text-2xl font-bold mb-6 text-center">Sign In to Stepify</h1>
      
      {#if $auth.error}
        <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
          {$auth.error}
        </div>
      {/if}
      
      <form on:submit|preventDefault={handleLogin} class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-medium mb-1">Email</label>
          <input
            id="email"
            type="email"
            bind:value={email}
            class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2"
            required
          />
        </div>
        
        <div>
          <label for="password" class="block text-sm font-medium mb-1">Password</label>
          <input
            id="password"
            type="password"
            bind:value={password}
            class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2"
            required
          />
        </div>
        
        <button 
          type="submit" 
          disabled={loading} 
          class="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
      
      <div class="mt-6">
        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <span class="w-full border-t"></span>
          </div>
          <div class="relative flex justify-center text-xs uppercase">
            <span class="bg-background px-2 text-foreground/60">Or continue with</span>
          </div>
        </div>
        
        <div class="mt-4">
          <button 
            class="w-full px-4 py-2 border border-border rounded-md hover:bg-muted"
            on:click={handleGoogleLogin}
          >
            <!-- Google icon would go here -->
            <span>Google</span>
          </button>
        </div>
      </div>
      
      <div class="mt-6 text-center text-sm">
        <p>
          Don't have an account? 
          <a href="/auth/register" class="text-primary hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  </div>
</ProtectedRoute>
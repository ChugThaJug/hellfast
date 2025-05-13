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
      // Login with email and password (will use development login in dev mode)
      await auth.login(email, password);
      goto("/dashboard");
    } catch (err) {
      console.error("Login error:", err);
      // Error is already set in the auth store
      loading = false;
    }
  }
  
  async function handleGoogleLogin() {
    try {
      // In development mode, use development login
      if (import.meta.env.DEV && import.meta.env.VITE_USE_DEV_AUTH === 'true') {
        console.log("Using development login");
        await auth.loginDevelopment();
        goto("/dashboard");
        return;
      }
      
      // For Firebase auth
      if (import.meta.env.VITE_USE_FIREBASE_AUTH === 'true') {
        console.log("Using Firebase auth");
        await auth.loginWithGoogle();
        goto("/dashboard");
        return;
      } 
      
      // For backend OAuth
      console.log("Using backend OAuth");
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      window.location.href = `${apiBaseUrl}/oauth/google/login`;
    } catch (error) {
      console.error("Google login error:", error);
      auth.setError("Google login failed: " + (error instanceof Error ? error.message : "Unknown error"));
    }
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
        
        {#if import.meta.env.DEV}
          <div class="text-center text-sm text-foreground/60 mt-2">
            <p>In development mode, any email/password will work</p>
          </div>
        {/if}
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
            class="w-full px-4 py-2 border border-border rounded-md hover:bg-muted flex items-center justify-center"
            on:click={handleGoogleLogin}
          >
            <!-- Google icon -->
            <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path d="M12.545 10.239v3.821h5.445c-0.712 2.315-2.647 3.972-5.445 3.972-3.332 0-6.033-2.701-6.033-6.032s2.701-6.032 6.033-6.032c1.498 0 2.866 0.549 3.921 1.453l2.814-2.814c-1.798-1.677-4.198-2.701-6.735-2.701-5.539 0-10.032 4.493-10.032 10.032s4.493 10.032 10.032 10.032c5.539 0 9.366-3.895 9.366-9.373 0-0.703-0.077-1.377-0.219-2.017h-9.147z" fill="currentColor"></path>
            </svg>
            <span>Sign in with Google</span>
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
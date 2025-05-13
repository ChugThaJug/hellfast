<!-- src/routes/auth/login/+page.svelte -->
<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { Button } from "bits-ui";
  import { authApi } from "$lib/api";
  
  let email = "";
  let password = "";
  let error = "";
  let loading = false;
  
  // Check for error in URL params
  $: if ($page.url.searchParams.get("error")) {
    error = "Authentication failed. Please try again.";
  }
  
  async function handleLogin() {
    if (!email || !password) {
      error = "Please enter both email and password";
      return;
    }
    
    loading = true;
    error = "";
    
    try {
      // Implement your login logic here
      // For Firebase, you would use firebase.auth().signInWithEmailAndPassword
      // Then use the auth token with your backend
      
      // Redirect to dashboard on success
      goto("/dashboard");
    } catch (err) {
      console.error("Login error:", err);
      error = err instanceof Error ? err.message : "Authentication failed";
    } finally {
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

<div class="container mx-auto px-4 py-16">
  <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm">
    <h1 class="text-2xl font-bold mb-6 text-center">Sign In to Stepify</h1>
    
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {error}
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
      
      <Button type="submit" class="w-full" disabled={loading}>
        {loading ? "Signing in..." : "Sign In"}
      </Button>
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
        <Button variant="outline" class="w-full" on:click={handleGoogleLogin}>
          <!-- Google icon would go here -->
          <span class="ml-2">Google</span>
        </Button>
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
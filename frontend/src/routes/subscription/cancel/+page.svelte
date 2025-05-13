<!-- frontend/src/routes/subscription/cancel/+page.svelte -->
<script lang="ts">
  import { goto } from "$app/navigation";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
</script>

<svelte:head>
  <title>Subscription Cancelled - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-16">
    <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm text-center">
      <div class="w-16 h-16 bg-yellow-100 text-yellow-700 mx-auto rounded-full flex items-center justify-center mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      
      <h1 class="text-2xl font-bold mb-2">Subscription Cancelled</h1>
      
      <p class="text-foreground/70 mb-6">
        Your subscription process was cancelled. No charges have been made.
        You can try again anytime.
      </p>
      
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button 
          class="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition"
          on:click={() => goto('/subscription')}
        >
          Back to Plans
        </button>
        
        <button 
          class="px-4 py-2 border border-primary text-primary rounded-md hover:bg-primary/10 transition"
          on:click={() => goto('/dashboard')}
        >
          Go to Dashboard
        </button>
      </div>
    </div>
  </div>
</ProtectedRoute>
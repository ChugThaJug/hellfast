<!-- frontend/src/routes/subscription/success/+page.svelte -->
<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  
  let planId = '';
  
  onMount(() => {
    // Get plan ID from URL parameter
    planId = $page.url.searchParams.get("plan_id") || '';
  });
  
  // Function to get plan name
  function getPlanName(id: string): string {
    switch (id) {
      case 'pro': return 'Pro';
      case 'max': return 'Max';
      case 'free': return 'Free';
      default: return 'Subscription';
    }
  }
</script>

<svelte:head>
  <title>Subscription Activated - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-16">
    <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm text-center">
      <div class="w-16 h-16 bg-green-100 text-green-700 mx-auto rounded-full flex items-center justify-center mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      
      <h1 class="text-2xl font-bold mb-2">Subscription Activated!</h1>
      
      {#if planId}
        <p class="text-foreground/70 mb-6">
          Your {getPlanName(planId)} plan has been successfully activated.
          You now have access to all the features and benefits.
        </p>
      {:else}
        <p class="text-foreground/70 mb-6">
          Your subscription has been successfully activated.
          You now have access to all the features and benefits.
        </p>
      {/if}
      
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button 
          class="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition"
          on:click={() => goto('/dashboard')}
        >
          Go to Dashboard
        </button>
        
        <button 
          class="px-4 py-2 border border-primary text-primary rounded-md hover:bg-primary/10 transition"
          on:click={() => goto('/')}
        >
          Process a Video
        </button>
      </div>
    </div>
  </div>
</ProtectedRoute>
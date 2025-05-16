<!-- frontend/src/routes/subscription/dev-checkout/+page.svelte -->
<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  import { subscriptionApi } from "$lib/api";
  
  let planId = '';
  let userId = '';
  let billing = '';
  let loading = true;
  let error = null;
  
  onMount(async () => {
    // Get parameters from URL
    planId = $page.url.searchParams.get("plan_id") || '';
    userId = $page.url.searchParams.get("user_id") || '';
    billing = $page.url.searchParams.get("billing") || 'monthly';
    
    try {
      loading = true;
      
      // In development mode, simulate a subscription success
      // by calling the API with the plan_id directly
      await subscriptionApi.createSubscription({
        plan_id: planId,
        yearly: billing === 'yearly'
      });
      
      // Simulate a slight delay
      setTimeout(() => {
        // After "processing", go to success page
        goto(`/subscription/success?plan_id=${planId}`);
      }, 2000);
    } catch (err) {
      console.error("Development checkout error:", err);
      error = err instanceof Error ? err.message : "Failed to process mock checkout";
      loading = false;
    }
  });
  
  // Function to get plan name
  function getPlanDisplayName(id: string): string {
    switch (id) {
      case 'pro': return 'Pro';
      case 'max': return 'Max';
      case 'free': return 'Free';
      default: return id.charAt(0).toUpperCase() + id.slice(1);
    }
  }
</script>

<svelte:head>
  <title>Development Checkout - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-16">
    <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm text-center">
      <h1 class="text-2xl font-bold mb-6">Development Checkout</h1>
      
      {#if loading}
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-foreground/70">
          Processing your {getPlanDisplayName(planId)} plan subscription...
        </p>
        <p class="text-xs text-foreground/40 mt-2">
          Plan: {planId}, Billing: {billing}
        </p>
      {:else if error}
        <div class="text-destructive mb-4">
          <p class="font-semibold">Error</p>
          <p>{error}</p>
        </div>
        <div class="flex justify-center mt-4">
          <button 
            class="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            on:click={() => goto('/subscription')}
          >
            Back to Plans
          </button>
        </div>
      {/if}
      
      <div class="mt-8 text-xs text-foreground/40">
        <p>Development Mode Checkout</p>
        <p>No actual payments are processed in development mode</p>
      </div>
    </div>
  </div>
</ProtectedRoute>
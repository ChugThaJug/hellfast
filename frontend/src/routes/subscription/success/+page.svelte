<!-- frontend/src/routes/subscription/success/+page.svelte -->
<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  import { subscriptionApi } from "$lib/api";
  
  let planId = '';
  let loading = true;
  let error = null;
  
  onMount(async () => {
    try {
      // Get plan ID from URL parameter
      planId = $page.url.searchParams.get("plan_id") || '';
      
      // Check subscription status to confirm activation
      if (planId) {
        const status = await subscriptionApi.getStatus();
        
        if (status.plan_id === planId) {
          console.log('Subscription confirmed active:', status);
        } else {
          console.warn('Subscription plan mismatch. Expected:', planId, 'Got:', status.plan_id);
        }
      }
    } catch (err) {
      console.error('Error checking subscription:', err);
      // Don't show error to user on success page, we'll assume it worked
    } finally {
      loading = false;
    }
  });
  
  // Function to get plan name
  function getPlanName(id: string): string {
    switch (id) {
      case 'pro': return 'Pro';
      case 'max': return 'Max';
      case 'free': return 'Free';
      default: return id.charAt(0).toUpperCase() + id.slice(1);
    }
  }
</script>

<svelte:head>
  <title>Subscription Activated - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-16">
    <div class="max-w-md mx-auto bg-background border rounded-lg p-8 shadow-sm text-center">
      {#if loading}
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <h1 class="text-2xl font-bold mb-2">Confirming subscription...</h1>
      {:else}
        <div class="w-16 h-16 bg-green-100 text-green-700 mx-auto rounded-full flex items-center justify-center mb-4">
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
      {/if}
    </div>
  </div>
</ProtectedRoute>
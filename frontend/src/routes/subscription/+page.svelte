<!-- frontend/src/routes/subscription/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { subscriptionApi } from "$lib/api";
  import { auth } from "$lib/stores/auth";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  import SubscriptionStatus from "$lib/components/subscription/SubscriptionStatus.svelte";
  
  let plans = [];
  let currentStatus = null;
  let loading = true;
  let error = null;
  let processing = false;
  
  onMount(async () => {
    try {
      // Load plans first
      plans = await subscriptionApi.getPlans();
      
      // Then try to load status (if authenticated)
      if ($auth.authenticated) {
        try {
          currentStatus = await subscriptionApi.getStatus();
        } catch (statusErr) {
          console.error("Error loading subscription status:", statusErr);
          // Continue even if status loading fails
        }
      }
    } catch (err) {
      console.error("Error loading subscription data:", err);
      error = err instanceof Error ? err.message : "Failed to load subscription data";
    } finally {
      loading = false;
    }
  });
  
  async function handleSubscribe(plan, isYearly = false) {
    if (!$auth.authenticated) {
      window.location.href = "/auth/login";
      return;
    }
    
    try {
      processing = true;
      error = null;
      
      const result = await subscriptionApi.createSubscription({
        plan_id: plan.id,
        yearly: isYearly
      });
      
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      } else if (result.message) {
        // Handle free plan or direct activation
        window.location.href = "/subscription/success?plan_id=" + plan.id;
      }
    } catch (err) {
      console.error("Subscription error:", err);
      error = err instanceof Error ? err.message : "Failed to process subscription";
      processing = false;
    }
  }
</script>

<svelte:head>
  <title>Subscription - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-6">Your Subscription</h1>
    
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {error}
      </div>
    {/if}
    
    {#if loading}
      <div class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    {:else}
      <!-- Current Subscription Status -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">Current Plan</h2>
        <SubscriptionStatus />
      </div>
      
      <!-- Available Plans -->
      <div>
        <h2 class="text-xl font-semibold mb-4">Available Plans</h2>
        
        <div class="grid md:grid-cols-3 gap-6">
          {#each plans as plan}
            <div class="border rounded-lg overflow-hidden p-6">
              <h3 class="text-lg font-semibold mb-2">{plan.name}</h3>
              
              <div class="mb-4">
                <div class="text-2xl font-bold">${plan.price.toFixed(2)}<span class="text-sm font-normal">/month</span></div>
                {#if plan.yearly_price}
                  <div class="text-sm text-foreground/60">
                    or ${plan.yearly_price.toFixed(2)} billed yearly
                  </div>
                {/if}
              </div>
              
              <div class="mb-4">
                <span class="text-sm">
                  Process up to {plan.monthly_quota} videos per month
                </span>
              </div>
              
              <div class="space-y-4 mb-6">
                <button 
                  class="w-full py-2 px-4 bg-primary text-white rounded-md hover:bg-primary/90" 
                  on:click={() => handleSubscribe(plan, false)}
                  disabled={processing || (currentStatus?.plan_id === plan.id)}
                >
                  {#if processing}
                    <span>Processing...</span>
                  {:else if currentStatus?.plan_id === plan.id}
                    <span>Current Plan</span>
                  {:else if plan.id === "free"}
                    <span>Switch to Free</span>
                  {:else}
                    <span>Subscribe Monthly</span>
                  {/if}
                </button>
                
                {#if plan.yearly_price && plan.id !== "free"}
                  <button 
                    class="w-full py-2 px-4 border border-primary text-primary rounded-md hover:bg-primary/10" 
                    on:click={() => handleSubscribe(plan, true)}
                    disabled={processing}
                  >
                    {processing ? "Processing..." : "Subscribe Yearly"}
                  </button>
                {/if}
              </div>
              
              <ul class="space-y-2 text-sm">
                {#each plan.features as feature}
                  <li class="flex items-center">
                    <span class="h-4 w-4 mr-2 text-primary">✓</span>
                    <span>{feature.replace(/_/g, ' ')}</span>
                  </li>
                {/each}
                
                {#if plan.max_video_length}
                  <li class="flex items-center">
                    <span class="h-4 w-4 mr-2 text-primary">✓</span>
                    <span>Videos up to {plan.max_video_length} minutes</span>
                  </li>
                {/if}
              </ul>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</ProtectedRoute>
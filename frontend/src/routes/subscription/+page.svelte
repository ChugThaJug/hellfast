<!-- src/routes/subscription/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { subscriptionApi } from "$lib/api";
  import { Button } from "bits-ui";
  import { Check } from "lucide-svelte";
  
  let plans = [];
  let currentStatus = null;
  let loading = true;
  let error = null;
  
  onMount(async () => {
    try {
      const [plansData, statusData] = await Promise.all([
        subscriptionApi.getPlans(),
        subscriptionApi.getStatus()
      ]);
      
      plans = plansData;
      currentStatus = statusData;
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to load subscription data";
    } finally {
      loading = false;
    }
  });
  
  async function selectPlan(planId) {
    try {
      const result = await subscriptionApi.createSubscription(planId);
      
      // If there's a checkout URL, redirect to it
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      } else {
        // Otherwise, subscription was created directly
        goto("/subscription/success");
      }
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to create subscription";
    }
  }
</script>

<svelte:head>
  <title>Subscription Plans - Stepify</title>
</svelte:head>

<div class="container mx-auto px-4 py-12">
  <h1 class="text-3xl font-bold mb-2 text-center">Choose Your Plan</h1>
  <p class="text-center text-foreground/70 mb-12 max-w-2xl mx-auto">
    Select the plan that works best for you. All plans include access to our core features.
  </p>
  
  {#if error}
    <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4 max-w-md mx-auto" role="alert">
      {error}
    </div>
  {/if}
  
  {#if loading}
    <div class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
  {:else if plans.length}
    <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
      {#each plans as plan}
        <div class={`border rounded-lg overflow-hidden ${currentStatus?.plan_id === plan.id ? 'border-primary border-2' : ''}`}>
          <div class="p-6">
            <h3 class="text-xl font-bold mb-2">{plan.name}</h3>
            <div class="mb-4">
              <span class="text-3xl font-bold">${plan.price}</span>
              <span class="text-foreground/60">/month</span>
            </div>
            <p class="text-foreground/70 mb-6">Process up to {plan.monthly_quota} videos each month</p>
            
            <Button 
              class="w-full mb-6" 
              variant={currentStatus?.plan_id === plan.id ? "outline" : "default"}
              disabled={currentStatus?.plan_id === plan.id}
              on:click={() => selectPlan(plan.id)}
            >
              {currentStatus?.plan_id === plan.id ? 'Current Plan' : 'Select Plan'}
            </Button>
            
            <ul class="space-y-2">
              {#each plan.features as feature}
                <li class="flex items-center">
                  <Check class="h-4 w-4 text-primary mr-2" />
                  <span>{feature.replace(/_/g, ' ')}</span>
                </li>
              {/each}
            </ul>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-center py-8">No subscription plans available</p>
  {/if}
  
  {#if currentStatus}
    <div class="mt-12 max-w-md mx-auto bg-muted/30 rounded-lg p-6">
      <h2 class="text-xl font-semibold mb-4">Your Current Plan</h2>
      <div class="space-y-2">
        <p>
          <span class="text-foreground/60">Plan:</span> 
          <span class="font-medium">{currentStatus.plan_id}</span>
        </p>
        <p>
          <span class="text-foreground/60">Status:</span> 
          <span class="font-medium">{currentStatus.status}</span>
        </p>
        <p>
          <span class="text-foreground/60">Monthly Quota:</span> 
          <span class="font-medium">{currentStatus.monthly_quota} videos</span>
        </p>
        <p>
          <span class="text-foreground/60">Used Quota:</span> 
          <span class="font-medium">{currentStatus.used_quota} videos</span>
        </p>
        {#if currentStatus.plan_id !== "free"}
          <Button 
            variant="outline" 
            class="mt-4" 
            on:click={() => subscriptionApi.cancelSubscription().then(() => goto("/subscription/cancelled"))}
          >
            Cancel Subscription
          </Button>
        {/if}
      </div>
    </div>
  {/if}
</div>
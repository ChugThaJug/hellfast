<!-- frontend/src/routes/pricing/+page.svelte -->
<script lang="ts">
  import { Check } from "lucide-svelte";
  import { onMount } from "svelte";
  import { subscriptionApi } from "$lib/api";
  import { goto } from "$app/navigation";
  import { auth } from "$lib/stores/auth";
  
  let plans = [];
  let loading = true;
  let error = null;
  
  // Function to format price with currency
  function formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  }
  
  // Function to get the nice name of a feature
  function formatFeatureName(feature: string): string {
    return feature
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
  }
  
  onMount(async () => {
    try {
      // Load plans from API
      plans = await subscriptionApi.getPlans();
    } catch (err) {
      console.error('Error loading plans:', err);
      error = err instanceof Error ? err.message : "Failed to load subscription plans";
    } finally {
      loading = false;
    }
  });
  
  // Handle subscription button click
  function handleSubscribe(planId: string) {
    if ($auth.authenticated) {
      goto('/subscription');  // Go to subscription page if logged in
    } else {
      goto('/auth/login');    // Otherwise go to login page
    }
  }
</script>

<svelte:head>
  <title>Pricing - Stepify</title>
</svelte:head>

<div class="container mx-auto px-4 py-12">
  <h1 class="text-4xl font-bold mb-4 text-center">Simple, Transparent Pricing</h1>
  <p class="text-center text-foreground/60 mb-10 max-w-2xl mx-auto">
    Choose the plan that works best for you. No hidden fees, no commitments. Upgrade, downgrade, or cancel anytime.
  </p>
  
  {#if loading}
    <div class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
  {:else if error}
    <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4 max-w-md mx-auto">
      {error}
    </div>
  {:else}
    <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
      {#each plans as plan}
        <div class={`border rounded-lg overflow-hidden ${plan.id === 'pro' ? 'relative shadow-lg' : ''}`}>
          {#if plan.id === 'pro'}
            <div class="absolute top-0 right-0 bg-primary text-primary-foreground px-3 py-1 text-sm">
              MOST POPULAR
            </div>
          {/if}
          
          <div class="p-6">
            <div class="bg-muted/30 px-3 py-1 rounded-full text-sm inline-block mb-2">{plan.name}</div>
            <h3 class="text-xl font-bold mb-2">{plan.name}</h3>
            <div class="mb-4">
              <span class="text-3xl font-bold">{formatPrice(plan.price)}</span>
              <span class="text-foreground/60">/month</span>
              {#if plan.yearly_price}
                <div class="text-sm text-foreground/60">or {formatPrice(plan.yearly_price)} billed yearly</div>
              {/if}
            </div>
            <p class="text-foreground/70 mb-6">Process up to {plan.monthly_quota} videos per month</p>
            
            <button 
              class={`w-full mb-6 py-2 px-4 rounded-md transition ${plan.id === 'pro' ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'border border-primary text-primary hover:bg-primary/10'}`}
              on:click={() => handleSubscribe(plan.id)}
            >
              {plan.id === 'free' ? 'Start for Free' : `Get ${plan.name}`}
            </button>
            
            <ul class="space-y-2">
              {#if plan.id === 'pro'}
                <li class="flex items-center">
                  <Check class="h-4 w-4 text-primary mr-2" />
                  <span>Everything in Free</span>
                </li>
              {:else if plan.id === 'max'} 
                <li class="flex items-center">
                  <Check class="h-4 w-4 text-primary mr-2" />
                  <span>Everything in Pro</span>
                </li>
              {/if}
              
              {#each plan.features as feature}
                <li class="flex items-center">
                  <Check class="h-4 w-4 text-primary mr-2" />
                  <span>{formatFeatureName(feature)}</span>
                </li>
              {/each}
              
              {#if plan.max_video_length}
                <li class="flex items-center">
                  <Check class="h-4 w-4 text-primary mr-2" />
                  <span>Videos up to {plan.max_video_length} minutes</span>
                </li>
              {/if}
            </ul>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  
  <div class="mt-16 max-w-3xl mx-auto text-center">
    <h2 class="text-2xl font-bold mb-4">Frequently Asked Questions</h2>
    <div class="grid md:grid-cols-2 gap-8 text-left">
      <div>
        <h3 class="font-semibold mb-2">Can I upgrade or downgrade my plan?</h3>
        <p class="text-foreground/60">Yes, you can change your plan at any time. Changes will be applied immediately.</p>
      </div>
      <div>
        <h3 class="font-semibold mb-2">How does the video quota work?</h3>
        <p class="text-foreground/60">Your quota resets monthly on your billing date. Unused videos don't roll over.</p>
      </div>
      <div>
        <h3 class="font-semibold mb-2">Is there a free trial?</h3>
        <p class="text-foreground/60">Our Free plan is always available with 3 videos per month, no credit card required.</p>
      </div>
      <div>
        <h3 class="font-semibold mb-2">Can I cancel anytime?</h3>
        <p class="text-foreground/60">Yes, you can cancel your subscription at any time. You'll be downgraded to the Free plan.</p>
      </div>
    </div>
  </div>
</div>
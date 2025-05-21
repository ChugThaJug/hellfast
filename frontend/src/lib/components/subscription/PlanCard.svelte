<!-- src/lib/components/subscription/PlanCard.svelte -->
<script lang="ts">
  import type { SubscriptionPlan } from "$lib/api/schema";
  
  // Props using Svelte 5 $props() rune
  let { 
    plan,
    currentPlanId = null,
    processing = false,
    featured = false,
    onMonthlySubscribe,
    onYearlySubscribe
  } = $props<{
    plan: SubscriptionPlan;
    currentPlanId: string | null;
    processing: boolean;
    featured: boolean;
    onMonthlySubscribe: (plan: SubscriptionPlan) => void;
    onYearlySubscribe: (plan: SubscriptionPlan) => void;
  }>();
  
  // Function to format price
  function formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  }
  
  // Format feature names
  function formatFeatureName(feature: string): string {
    return feature
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
  }
</script>

<div class={`border rounded-lg overflow-hidden ${featured ? 'shadow-lg border-primary/20' : ''}`}>
  {#if featured}
    <div class="bg-primary text-primary-foreground px-4 py-2 text-center font-medium text-sm">
      MOST POPULAR
    </div>
  {/if}
  
  <div class="p-6">
    <div class="flex justify-between items-start">
      <div>
        <h3 class="text-lg font-semibold mb-1">{plan.name}</h3>
        {#if plan.id === 'free'}
          <div class="text-foreground/60 text-sm">Free forever</div>
        {:else}
          <div class="text-foreground/60 text-sm">Cancel anytime</div>
        {/if}
      </div>
      
      {#if featured}
        <div class="bg-primary/20 h-8 w-8 rounded-full flex items-center justify-center">
          <!-- Check Icon -->
          <svg class="h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
      {/if}
    </div>
    
    <div class="mt-4 mb-6">
      <div class="text-2xl font-bold">{formatPrice(plan.price)}<span class="text-sm font-normal">/month</span></div>
      {#if plan.yearly_price}
        <div class="text-sm text-foreground/60">
          or {formatPrice(plan.yearly_price)} billed yearly
          <span class="text-green-600 font-medium">
            (Save {formatPrice(plan.price * 12 - plan.yearly_price)})
          </span>
        </div>
      {/if}
    </div>
    
    <div class="border-t border-border pt-4 mb-6">
      <div class="flex items-center gap-2 mb-2">
        <div class="h-6 w-6 bg-primary/10 rounded-full flex items-center justify-center">
          <span class="text-primary text-xs font-medium">{plan.monthly_quota}</span>
        </div>
        <span>videos per month</span>
      </div>
      
      {#if plan.max_video_length}
        <div class="flex items-center gap-2 mb-4">
          <div class="h-6 w-6 bg-primary/10 rounded-full flex items-center justify-center">
            <span class="text-primary text-xs font-medium">{plan.max_video_length}</span>
          </div>
          <span>minute maximum video length</span>
        </div>
      {/if}
    </div>
    
    <div class="space-y-3 mb-6">
      <button 
        class={`w-full py-2 px-4 rounded-md transition ${currentPlanId === plan.id ? 'bg-foreground/10 text-foreground/60' : 'bg-primary text-primary-foreground hover:bg-primary/90'}`}
        on:click={() => onMonthlySubscribe(plan)}
        disabled={processing || currentPlanId === plan.id}
      >
        {#if processing}
          <span>Processing...</span>
        {:else if currentPlanId === plan.id}
          <span>Current Plan</span>
        {:else if plan.id === "free"}
          <span>Switch to Free</span>
        {:else}
          <span>Subscribe Monthly</span>
        {/if}
      </button>
      
      {#if plan.yearly_price && plan.id !== "free"}
        <button 
          class={`w-full py-2 px-4 rounded-md transition ${currentPlanId === plan.id ? 'bg-foreground/10 text-foreground/60 border border-foreground/20' : 'border border-primary text-primary hover:bg-primary/10'}`}
          on:click={() => onYearlySubscribe(plan)}
          disabled={processing || currentPlanId === plan.id}
        >
          {#if processing}
            <span>Processing...</span>
          {:else if currentPlanId === plan.id}
            <span>Current Plan</span>
          {:else}
            <span>Subscribe Yearly</span>
          {/if}
        </button>
      {/if}
    </div>
    
    <div class="border-t border-border pt-4">
      <p class="text-sm font-medium mb-2">Features:</p>
      <ul class="space-y-2 text-sm">
        {#each plan.features as feature}
          <li class="flex items-start">
            <svg class="h-4 w-4 mr-2 text-primary mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>{formatFeatureName(feature)}</span>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</div>
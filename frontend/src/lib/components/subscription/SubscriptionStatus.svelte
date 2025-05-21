<!-- src/lib/components/subscription/SubscriptionStatus.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { subscriptionApi } from '$lib/api';
  import type { SubscriptionStatus } from '$lib/api/schema';
  
  let { minimal = false } = $props<{ minimal?: boolean }>();
  
  let status = $state<SubscriptionStatus | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  
  onMount(async () => {
    try {
      status = await subscriptionApi.getStatus();
    } catch (err) {
      console.error("Failed to load subscription status:", err);
      error = err instanceof Error ? err.message : "Failed to load subscription status";
      
      // If the error is 401 Unauthorized, we don't need to show an error
      // The ProtectedRoute component will handle the redirect
      if (err instanceof Error && err.message.includes("401")) {
        error = "Authentication required";
      }
    } finally {
      loading = false;
    }
  });
  
  // Format the date
  function formatDate(dateStr: string): string {
    if (dateStr === "-") return "N/A";
    return new Date(dateStr).toLocaleDateString();
  }
  
  // Calculate progress percentage for quota usage
  function calculateUsagePercentage(): number {
    if (!status) return 0;
    return (status.used_quota / status.monthly_quota) * 100;
  }
  
  // Format plan name for display
  function getPlanDisplayName(planId: string): string {
    switch (planId) {
      case 'pro': return 'Pro';
      case 'max': return 'Max';
      case 'free': return 'Free';
      default: return planId.charAt(0).toUpperCase() + planId.slice(1);
    }
  }
</script>

{#if loading}
  <div class="py-2">
    <div class="h-4 w-24 bg-muted animate-pulse rounded"></div>
  </div>
{:else if error}
  <div class="p-4 border rounded-lg bg-background">
    <div class="text-destructive text-sm mb-2">{error}</div>
    <button 
      class="text-sm text-primary hover:underline" 
      on:click={() => location.reload()}
    >
      Try again
    </button>
  </div>
{:else if status}
  {#if minimal}
    <div class="flex items-center gap-2">
      <span class="bg-primary/20 text-primary px-2 py-0.5 rounded-full text-xs">
        {getPlanDisplayName(status.plan_id)}
      </span>
      <span class="text-sm text-foreground/60">
        {status.used_quota}/{status.monthly_quota} videos
      </span>
    </div>
  {:else}
    <div class="p-4 border rounded-lg bg-background">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-medium">Your Subscription</h3>
        <a href="/subscription" class="text-sm text-primary hover:underline">Manage</a>
      </div>
      
      <div class="space-y-3">
        <div>
          <p class="text-sm text-foreground/60 mb-1">Plan</p>
          <p class="font-medium">{getPlanDisplayName(status.plan_id)}</p>
        </div>
        
        <div>
          <p class="text-sm text-foreground/60 mb-1">Videos Usage</p>
          <div class="w-full bg-muted rounded-full h-2 mb-1">
            <div 
              class="bg-primary h-2 rounded-full transition-all duration-300"
              style={`width: ${calculateUsagePercentage()}%`}
            ></div>
          </div>
          <p class="text-xs">{status.used_quota} of {status.monthly_quota} videos used</p>
        </div>
        
        {#if status.plan_id !== 'free'}
          <div>
            <p class="text-sm text-foreground/60 mb-1">Current Period Ends</p>
            <p class="font-medium">{formatDate(status.current_period_end)}</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
{:else}
  <div class="p-4 border rounded-lg bg-background">
    <p class="text-foreground/60">No subscription information available</p>
  </div>
{/if}
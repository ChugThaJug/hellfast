<!-- frontend/src/routes/subscription/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { subscriptionApi } from "$lib/api";
  import { Check } from "lucide-svelte";
  import type { SubscriptionPlan, SubscriptionStatus } from "$lib/api/schema";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  import PaddleLoader from "$lib/components/subscription/PaddleLoader.svelte";
  import { paddleService } from "$lib/services/paddle";
  import { browser } from "$app/environment";
  
  let plans: SubscriptionPlan[] = [];
  let currentStatus: SubscriptionStatus | null = null;
  let loading = true;
  let processing = false;
  let error: string | null = null;
  let yearlyBilling = false;
  
  // Get Paddle vendor ID from environment
  const paddleVendorId = browser ? import.meta.env.VITE_PADDLE_VENDOR_ID || '11111' : '11111';
  const paddleSandbox = browser ? import.meta.env.VITE_PADDLE_SANDBOX === 'true' : true;
  
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
      // Get plans and status from API
      const [plansData, statusData] = await Promise.all([
        subscriptionApi.getPlans(),
        subscriptionApi.getStatus()
      ]);
      
      plans = plansData;
      currentStatus = statusData;
      
      console.log('Plans loaded:', plans);
      console.log('Current status:', currentStatus);
      
      // Initialize Paddle service
      await paddleService.initialize();
    } catch (err) {
      console.error('Error loading subscription data:', err);
      error = err instanceof Error ? err.message : "Failed to load subscription data";
    } finally {
      loading = false;
    }
  });
  
  async function selectPlan(planId: string) {
    if (processing) return;
    
    try {
      processing = true;
      error = null;
      
      // For free plan, just create subscription directly
      if (planId === 'free') {
        const result = await subscriptionApi.createSubscription({
          plan_id: planId,
          yearly: false // Free plan is always "monthly"
        });
        
        if (result.message) {
          // Refresh the page to show updated subscription
          window.location.reload();
        }
        return;
      }
      
      // For paid plans
      const result = await subscriptionApi.createSubscription({
        plan_id: planId,
        yearly: yearlyBilling
      });
      
      // If checkout URL is provided, open Paddle checkout
      if (result.checkout_url) {
        console.log('Opening Paddle checkout:', result.checkout_url);
        
        // Try to open Paddle checkout
        const checkoutOpened = await paddleService.openCheckout(
          result.checkout_url,
          {
            successCallback: () => {
              // Redirect to success page
              goto(`/subscription/success?plan_id=${planId}`);
            },
            closeCallback: () => {
              processing = false;
            },
            errorCallback: (err) => {
              console.error('Paddle checkout error:', err);
              error = "An error occurred with the payment process. Please try again.";
              processing = false;
            }
          }
        );
        
        // If checkout couldn't be opened, redirect to the URL
        if (!checkoutOpened) {
          window.location.href = result.checkout_url;
        }
      } 
      // If message is provided, subscription was created directly
      else if (result.message) {
        console.log('Subscription created:', result.message);
        window.location.reload();
      } else {
        throw new Error("No checkout URL or message returned from subscription API");
      }
    } catch (err) {
      console.error('Error creating subscription:', err);
      error = err instanceof Error ? err.message : "Failed to process subscription";
      processing = false;
    }
  }
  
  async function cancelCurrentSubscription() {
    if (processing) return;
    
    if (!confirm('Are you sure you want to cancel your subscription? You will be downgraded to the free plan.')) {
      return;
    }
    
    try {
      processing = true;
      error = null;
      const result = await subscriptionApi.cancelSubscription();
      alert(result.message);
      window.location.reload();
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to cancel subscription";
      processing = false;
    }
  }
  
  // Toggle yearly/monthly billing
  function toggleBilling() {
    yearlyBilling = !yearlyBilling;
  }
</script>

<svelte:head>
  <title>Choose Your Plan - Stepify</title>
</svelte:head>

<!-- Load Paddle JavaScript -->
<PaddleLoader vendorId={paddleVendorId} sandbox={paddleSandbox} />

<ProtectedRoute>
  <div class="container mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-2 text-center">Choose Your Plan</h1>
    <p class="text-center text-foreground/70 mb-6 max-w-2xl mx-auto">
      Select the plan that works best for you. All plans include access to our core features.
    </p>
    
    <!-- Billing toggle -->
    <div class="flex justify-center mb-8">
      <div class="flex items-center p-1 bg-muted rounded-full">
        <button 
          class={`px-4 py-2 rounded-full transition ${!yearlyBilling ? 'bg-background shadow-sm' : ''}`}
          on:click={() => yearlyBilling = false}
          disabled={processing}
        >
          Monthly
        </button>
        <button 
          class={`px-4 py-2 rounded-full transition ${yearlyBilling ? 'bg-background shadow-sm' : ''}`}
          on:click={() => yearlyBilling = true}
          disabled={processing}
        >
          Yearly
          <span class="text-sm text-green-500">Save 16%</span>
        </button>
      </div>
    </div>
    
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4 max-w-md mx-auto" role="alert">
        {error}
      </div>
    {/if}
    
    {#if loading}
      <div class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    {:else}
      <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        <!-- Loop through plans -->
        {#each plans as plan, index}
          <div class={`border rounded-lg overflow-hidden ${currentStatus?.plan_id === plan.id ? 'border-primary border-2' : ''} ${index === 1 ? 'relative shadow-lg' : ''}`}>
            {#if index === 1}
              <div class="absolute top-0 right-0 bg-primary text-white px-3 py-1 text-sm">
                MOST POPULAR
              </div>
            {/if}
            
            <div class="p-6">
              <div class="bg-muted/30 px-3 py-1 rounded-full text-sm inline-block mb-2">{plan.name}</div>
              <h3 class="text-xl font-bold mb-2">{plan.name}</h3>
              <div class="mb-4">
                {#if yearlyBilling && plan.yearly_price}
                  <span class="text-3xl font-bold">{formatPrice(plan.yearly_price / 12)}</span>
                  <span class="text-foreground/60">/month</span>
                  <div class="text-sm text-green-500">{formatPrice(plan.yearly_price)} billed yearly (save 16%)</div>
                {:else}
                  <span class="text-3xl font-bold">{formatPrice(plan.price)}</span>
                  <span class="text-foreground/60">/month</span>
                {/if}
              </div>
              <p class="text-foreground/70 mb-6">Process up to {plan.monthly_quota} videos per month</p>
              
              <button 
                class={`w-full mb-6 py-2 px-4 rounded-md transition ${processing ? 'opacity-70 cursor-not-allowed' : ''} ${index === 1 ? 'bg-primary text-white hover:bg-primary/90' : 'border border-primary text-primary hover:bg-primary/10'}`}
                on:click={() => selectPlan(plan.id)}
                disabled={currentStatus?.plan_id === plan.id || processing}
              >
                {#if processing}
                  <span class="flex items-center justify-center">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                    Processing...
                  </span>
                {:else if currentStatus?.plan_id === plan.id}
                  Current Plan
                {:else if plan.id === 'free'}
                  Start for Free
                {:else}
                  Get {plan.name}
                {/if}
              </button>
              
              <ul class="space-y-2">
                {#if index > 0}
                  <li class="flex items-center">
                    <Check class="h-4 w-4 text-primary mr-2" />
                    <span>Everything in {index === 1 ? 'Free' : 'Pro'}</span>
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
    
    <!-- Current subscription section -->
    {#if currentStatus && currentStatus.plan_id !== 'free'}
      <div class="mt-16 max-w-md mx-auto bg-muted/30 rounded-lg p-6 border">
        <h2 class="text-xl font-semibold mb-4">Your Current Subscription</h2>
        <div class="space-y-3">
          <p>
            <span class="text-foreground/60">Plan:</span> 
            <span class="font-medium">{currentStatus.plan_id.charAt(0).toUpperCase() + currentStatus.plan_id.slice(1)}</span>
          </p>
          <p>
            <span class="text-foreground/60">Status:</span> 
            <span class="font-medium">{currentStatus.status}</span>
          </p>
          <p>
            <span class="text-foreground/60">Current Period Ends:</span> 
            <span class="font-medium">{new Date(currentStatus.current_period_end).toLocaleDateString()}</span>
          </p>
          <p>
            <span class="text-foreground/60">Video Quota:</span> 
            <span class="font-medium">{currentStatus.used_quota} / {currentStatus.monthly_quota} videos used</span>
          </p>
          
          <div class="pt-4">
            <button 
              class={`px-4 py-2 border border-destructive text-destructive rounded-md hover:bg-destructive/10 transition ${processing ? 'opacity-70 cursor-not-allowed' : ''}`}
              on:click={cancelCurrentSubscription}
              disabled={processing}
            >
              {#if processing}
                <span class="flex items-center justify-center">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  Processing...
                </span>
              {:else}
                Cancel Subscription
              {/if}
            </button>
          </div>
        </div>
      </div>
    {/if}
  </div>
</ProtectedRoute>
<!-- src/routes/subscription/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { subscriptionApi } from "$lib/api";
  import { auth } from "$lib/stores/auth";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  import SubscriptionStatus from "$lib/components/subscription/SubscriptionStatus.svelte";
  import PlanCard from "$lib/components/subscription/PlanCard.svelte";
  import type { SubscriptionPlan, SubscriptionStatus as SubscriptionStatusType } from "$lib/api/schema";

  let plans = $state<SubscriptionPlan[]>([]);
  let currentStatus = $state<SubscriptionStatusType | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let processing = $state(false);
  let plansLoaded = $state(false);
  let authInitialized = $state(false);
  let paddleInitialized = $state(false);
  const isDevelopment = import.meta.env.DEV || window.location.hostname === 'localhost';
  let devCheckoutUrl = $state<string | null>(null);

  // Function to load plans separately from the initial mount
  async function loadPlans() {
    if (plansLoaded || !$auth.authenticated) return;

    try {
      console.log("Loading subscription plans...");
      plans = await subscriptionApi.getPlans();

      // Sort plans by price (free first, then increasing)
      plans.sort((a, b) => {
        if (a.id === 'free') return -1;
        if (b.id === 'free') return 1;
        return a.price - b.price;
      });

      console.log(`Loaded ${plans.length} subscription plans`);
      plansLoaded = true;

      // Then try to load status (if authenticated)
      if ($auth.authenticated) {
        try {
          console.log("Loading subscription status...");
          currentStatus = await subscriptionApi.getStatus();
          console.log("Subscription status loaded:", currentStatus?.plan_id);
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
  }

  // On component mount - initialize Paddle first
  onMount(() => {
    try {
      // Check if we're already authenticated
      if ($auth.authenticated) {
        console.log("User is already authenticated, loading plans...");
        loadPlans();
      } else if (!$auth.loading) {
        console.log("User is not authenticated and auth is not loading");
        loading = false;
      }

      authInitialized = true;
    } catch (err) {
      console.error("Error during initialization:", err);
      error = err instanceof Error ? err.message : "Initialization failed";
      loading = false;
    }
  });

  // React to auth changes
  $effect(() => {
    if (authInitialized && $auth.authenticated && !plansLoaded && !loading) {
      console.log("Auth state changed to authenticated, loading plans...");
      loading = true;
      loadPlans();
    }
  });

  // React to auth loading state
  $effect(() => {
    if (authInitialized && !$auth.loading && !$auth.authenticated) {
      console.log("Auth loading complete but not authenticated");
      loading = false;
    }
  });

  async function handleSubscribe(plan: SubscriptionPlan, isYearly = false) {
    if (!$auth.authenticated) {
      console.log("User not authenticated, redirecting to login");
      // Store current URL to return after login
      localStorage.setItem('auth_redirect', $page.url.pathname);
      goto("/auth/login");
      return;
    }

    try {
      console.log(`Subscribing to ${plan.id} plan (yearly: ${isYearly})`);
      processing = true;
      error = null;
      devCheckoutUrl = null;

      // Directly use the backend API to create a checkout session
      const response = await subscriptionApi.createSubscription(plan.id, isYearly);
      console.log("Subscription creation result:", response);

      // Check if we have a checkout URL
      if (response?.checkout_url) {
        // Check if the URL is correct (should contain sandbox-buy.paddle.com for sandbox)
        const url = response.checkout_url;

        if (url.includes('localhost:5000')) {
          console.warn("Development/test Paddle URL detected:", url);
          
          if (isDevelopment) {
            devCheckoutUrl = url;
            error = "Development mode: Paddle is returning localhost URLs. This indicates a configuration issue.";
          } else {
            error = "The payment system returned an invalid checkout URL. Please contact support.";
            console.error("Invalid checkout URL received:", url);
          }
        } else {
          console.log("Redirecting to Paddle checkout:", url);
          window.location.href = url;
        }
      } else {
        throw new Error("No checkout URL was returned from the server");
      }
    } catch (err) {
      console.error("Subscription error:", err);
      error = err instanceof Error ? err.message : "Failed to process subscription";
    } finally {
      processing = false;
    }
  }

  function openDevCheckout() {
    if (devCheckoutUrl) {
      window.open(devCheckoutUrl, '_blank');
    }
  }

  function copyDevCheckoutUrl() {
    if (devCheckoutUrl && navigator.clipboard) {
      navigator.clipboard.writeText(devCheckoutUrl)
        .then(() => alert("URL copied to clipboard!"))
        .catch(err => console.error("Failed to copy URL:", err));
    }
  }

  function getFeaturedPlanId(): string {
    // Find the pro plan, or second plan if no pro exists
    const proIndex = plans.findIndex(plan => plan.id === 'pro');
    if (proIndex >= 0) return plans[proIndex].id;

    // If there's no pro plan but there are at least 2 plans, return the second one
    return plans.length >= 2 ? plans[1].id : (plans[0]?.id || '');
  }
</script>

<svelte:head>
  <title>Subscription - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-2">Your Subscription</h1>
    <p class="text-foreground/60 mb-6">Manage your subscription and billing details.</p>

    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        <div class="font-medium">Error</div>
        <div>{error}</div>
        <button 
          class="mt-2 text-sm underline" 
          on:click={() => { error = null; loading = true; loadPlans(); }}
        >
          Try again
        </button>
        
        {#if isDevelopment && devCheckoutUrl}
          <div class="mt-4 p-4 border border-yellow-500 bg-yellow-50 rounded-md">
            <h3 class="font-bold text-yellow-800">Development Options:</h3>
            <p class="mb-2 text-yellow-800">You're seeing this because you're in development mode.</p>
            <ul class="list-disc pl-5 mb-4 text-yellow-800 text-sm">
              <li>For proper Paddle sandbox integration: Use a custom domain with HTTPS</li>
              <li>Check Paddle dashboard for domain configuration</li>
              <li class="mt-2">
                <span class="font-medium">Your current checkout URL is:</span> 
                <code class="bg-gray-100 px-1 text-xs break-all block mt-1 p-2">{devCheckoutUrl}</code>
              </li>
            </ul>
            <div class="flex space-x-4">
              <button 
                class="px-3 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 font-medium"
                on:click={openDevCheckout}
              >
                Open checkout in new tab
              </button>
              <button 
                class="px-3 py-2 border border-gray-300 rounded hover:bg-gray-100"
                on:click={copyDevCheckoutUrl}
              >
                Copy URL
              </button>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    {#if loading}
      <div class="flex flex-col items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
        <p class="text-foreground/60">Loading your subscription information...</p>
      </div>
    {:else if !$auth.authenticated}
      <div class="bg-muted/30 rounded-lg p-8 text-center">
        <h2 class="text-xl font-semibold mb-4">Sign In to Manage Your Subscription</h2>
        <p class="mb-6 max-w-lg mx-auto">You need to sign in to view and manage your subscription details.</p>
        <a 
          href="/auth/login" 
          class="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 inline-block"
        >
          Sign In
        </a>
      </div>
    {:else}
      <!-- Current Subscription Status -->
      <div class="mb-10">
        <h2 class="text-xl font-semibold mb-4">Current Plan</h2>
        <SubscriptionStatus />
      </div>

      <!-- Available Plans -->
      {#if plans.length > 0}
        <div>
          <h2 class="text-xl font-semibold mb-6">Available Plans</h2>

          <div class="grid md:grid-cols-3 gap-6">
            {#each plans as plan}
              <PlanCard 
                {plan}
                currentPlanId={currentStatus?.plan_id || null}
                {processing}
                featured={plan.id === getFeaturedPlanId()}
                onMonthlySubscribe={() => handleSubscribe(plan, false)}
                onYearlySubscribe={() => handleSubscribe(plan, true)}
              />
            {/each}
          </div>
        </div>
      {:else}
        <div class="bg-muted/30 rounded-lg p-6 text-center">
          <p class="text-foreground/60">No subscription plans are currently available. Please try again later.</p>
          <button 
            class="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90" 
            on:click={() => { loading = true; loadPlans(); }}
          >
            Refresh Plans
          </button>
        </div>
      {/if}

      {#if currentStatus && currentStatus.plan_id !== 'free'}
        <div class="mt-16 border-t pt-8">
          <h2 class="text-xl font-semibold mb-4">Cancel Subscription</h2>
          <p class="text-foreground/70 mb-4 max-w-2xl">
            If you cancel your subscription, you'll keep access to your current plan until the end of your billing period,
            after which you'll be downgraded to the Free plan.
          </p>
          <button 
            class="px-4 py-2 border border-destructive text-destructive rounded-md hover:bg-destructive/10"
            on:click={async () => {
              if (confirm("Are you sure you want to cancel your subscription? You'll keep access until the end of your billing period.")) {
                try {
                  processing = true;
                  const result = await subscriptionApi.cancelSubscription();
                  alert("Your subscription has been cancelled. You'll keep your current plan until the end of your billing period.");
                  window.location.reload();
                } catch (err) {
                  console.error("Error cancelling subscription:", err);
                  error = err instanceof Error ? err.message : "Failed to cancel subscription";
                  processing = false;
                }
              }
            }}
            disabled={processing}
          >
            {processing ? 'Processing...' : 'Cancel Subscription'}
          </button>
        </div>
      {/if}

      <!-- FAQ Section -->
      <div class="mt-16 max-w-3xl border-t pt-8">
        <h2 class="text-xl font-semibold mb-6">Frequently Asked Questions</h2>
        <div class="space-y-6">
          <div>
            <h3 class="font-medium mb-2">How does the video quota work?</h3>
            <p class="text-foreground/70">Your quota resets monthly on your billing date. You can process up to your quota limit each month, and unused videos don't roll over.</p>
          </div>
          <div>
            <h3 class="font-medium mb-2">Can I upgrade or downgrade my plan?</h3>
            <p class="text-foreground/70">Yes, you can change your plan at any time. If you upgrade, you'll be charged the prorated difference. If you downgrade, your new plan will take effect at the end of your current billing period.</p>
          </div>
          <div>
            <h3 class="font-medium mb-2">How do I cancel my subscription?</h3>
            <p class="text-foreground/70">You can cancel your subscription at any time from this page. You'll keep access to your current plan until the end of your billing period, after which you'll be downgraded to the Free plan.</p>
          </div>
          <div>
            <h3 class="font-medium mb-2">What payment methods do you accept?</h3>
            <p class="text-foreground/70">We accept all major credit cards, including Visa, Mastercard, and American Express, as well as PayPal and several other payment methods through our payment provider, Paddle.</p>
          </div>
        </div>
      </div>
    {/if}
  </div>
</ProtectedRoute>
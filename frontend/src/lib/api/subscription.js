/**
 * Subscription API client
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get subscription plans
 * @returns {Promise<Array>} Array of subscription plans
 */
export async function getSubscriptionPlans() {
    const response = await fetch(`${API_URL}/subscription/plans`);
    
    if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to fetch subscription plans:', errorText);
        throw new Error(`Failed to fetch subscription plans: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
}

/**
 * Create a subscription checkout session
 * @param {string} planId - The plan ID (pro or max)
 * @param {string} billingCycle - The billing cycle (monthly or yearly)
 * @param {string} token - The authentication token
 * @returns {Promise<Object>} Checkout session data
 */
export async function createSubscription(planId, billingCycle, token) {
    // Validate inputs before sending
    if (!['pro', 'max'].includes(planId)) {
        throw new Error(`Invalid plan ID: ${planId}. Must be 'pro' or 'max'.`);
    }
    
    if (!['monthly', 'yearly'].includes(billingCycle)) {
        throw new Error(`Invalid billing cycle: ${billingCycle}. Must be 'monthly' or 'yearly'.`);
    }
    
    // Prepare request payload exactly matching backend expectations
    const payload = {
        plan_id: planId,        // Must use snake_case to match backend
        billing_cycle: billingCycle
    };
    
    console.log('Creating subscription with payload:', payload);
    
    const response = await fetch(`${API_URL}/subscription/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });
    
    // Check for errors
    if (!response.ok) {
        let errorDetail;
        try {
            // Try to parse error detail
            const errorResponse = await response.json();
            errorDetail = JSON.stringify(errorResponse);
        } catch (e) {
            // Fallback to status text
            errorDetail = await response.text() || response.statusText;
        }
        
        console.error(`Subscription creation failed (${response.status}):`, errorDetail);
        throw new Error(`Failed to create subscription: ${errorDetail}`);
    }
    
    return response.json();
}

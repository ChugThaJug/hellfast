<!-- src/lib/components/layout/Header.svelte -->
<script lang="ts">
  import { theme, toggleTheme } from "$lib/stores/theme";
  import { auth } from "$lib/stores/auth";
  
  // Track dropdown visibility
  let userMenuVisible = $state(false);
  
  // Toggle user menu
  function toggleUserMenu() {
    userMenuVisible = !userMenuVisible;
  }
  
  // Close menu when clicking outside
  function handleClickOutside(event) {
    if (userMenuVisible && event.target.closest('.user-menu') === null) {
      userMenuVisible = false;
    }
  }
</script>

<!-- Add event listener for closing dropdown when clicking outside -->
<svelte:window on:click={handleClickOutside} />

<header class="sticky top-0 z-50 border-b border-border bg-background/75 backdrop-blur-md">
  <div class="container px-4">
    <div class="flex h-[70px] items-center justify-between gap-3">
      <a href="/" class="text-2xl font-bold tracking-tight">
        stepify.tech
      </a>
      
      <nav class="hidden md:flex items-center space-x-6">
        <a href="/" class="text-foreground/60 hover:text-foreground">Home</a>
        {#if $auth.authenticated}
          <a href="/dashboard" class="text-foreground/60 hover:text-foreground">My Videos</a>
        {/if}
        <a href="/pricing" class="text-foreground/60 hover:text-foreground">Pricing</a>
      </nav>
      
      <div class="flex items-center gap-4">
        <button on:click={toggleTheme} class="p-2 rounded-md hover:bg-muted">
          {#if $theme === "light"}
            <!-- Moon Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          {:else}
            <!-- Sun Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          {/if}
        </button>
        
        {#if $auth.authenticated}
          <div class="relative user-menu">
            <button 
              class="flex items-center gap-1 p-2 rounded-md hover:bg-muted"
              on:click={toggleUserMenu}
            >
              <!-- User Icon -->
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              <span class="hidden md:inline">{$auth.user?.username || 'Account'}</span>
            </button>
            
            {#if userMenuVisible}
              <div class="absolute right-0 top-full mt-1 w-48 bg-background border rounded-md shadow-md">
                <div class="p-4 border-b">
                  <p class="font-medium">{$auth.user?.username || 'User'}</p>
                  <p class="text-sm text-foreground/60">{$auth.user?.email || ''}</p>
                </div>
                <div class="p-2">
                  <a href="/dashboard" class="block w-full text-left px-4 py-2 rounded-md hover:bg-muted">Dashboard</a>
                  <a href="/subscription" class="block w-full text-left px-4 py-2 rounded-md hover:bg-muted">Subscription</a>
                  <button 
                    on:click={() => auth.logout()} 
                    class="flex items-center w-full text-left px-4 py-2 rounded-md hover:bg-muted text-destructive"
                  >
                    <!-- Logout Icon -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                      <polyline points="16 17 21 12 16 7"></polyline>
                      <line x1="21" y1="12" x2="9" y2="12"></line>
                    </svg>
                    Sign Out
                  </button>
                </div>
              </div>
            {/if}
          </div>
        {:else}
          <a 
            href="/auth/login" 
            class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Sign In
          </a>
        {/if}
      </div>
    </div>
  </div>
</header>
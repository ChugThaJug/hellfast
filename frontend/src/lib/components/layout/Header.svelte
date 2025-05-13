<!-- frontend/src/lib/components/layout/Header.svelte -->
<script>
  import { theme, toggleTheme } from "$lib/stores/theme";
  import { auth } from "$lib/stores/auth";
  import { Moon, Sun, User, LogOut } from "lucide-svelte";
</script>

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
            <Moon class="h-5 w-5" />
          {:else}
            <Sun class="h-5 w-5" />
          {/if}
        </button>
        
        {#if $auth.authenticated}
          <div class="relative group">
            <button class="flex items-center gap-1 p-2 rounded-md hover:bg-muted">
              <User class="h-5 w-5" />
              <span class="hidden md:inline">{$auth.user?.username || 'Account'}</span>
            </button>
            
            <div class="absolute right-0 top-full mt-1 w-48 bg-background border rounded-md shadow-md hidden group-hover:block">
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
                  <LogOut class="h-4 w-4 mr-2" /> Sign Out
                </button>
              </div>
            </div>
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
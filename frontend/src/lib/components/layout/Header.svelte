<!-- frontend/src/lib/components/layout/Header.svelte -->
<script>
  import { theme, toggleTheme } from "$lib/stores/theme";
  import { Moon, Sun } from "lucide-svelte";
</script>

<header class="sticky top-0 z-50 border-b border-border bg-background/75 backdrop-blur-md">
  <div class="container px-4">
    <div class="flex h-[70px] items-center justify-between gap-3">
      <a href="/" class="text-2xl font-bold tracking-tight">
        stepify.tech
      </a>
      
      <nav class="hidden md:flex items-center space-x-6">
        <a href="/" class="text-foreground/60 hover:text-foreground">Home</a>
        <a href="/videos" class="text-foreground/60 hover:text-foreground">My Videos</a>
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
        
        <a 
          href="/auth/login" 
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Sign In
        </a>
      </div>
    </div>
  </div>
</header>
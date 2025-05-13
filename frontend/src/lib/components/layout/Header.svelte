<!-- src/lib/components/layout/Header.svelte -->
<script>
  import { Button } from "bits-ui";
  import { Moon, Sun } from "lucide-svelte";
  import { mode, toggleMode } from "mode-watcher";
</script>

<header class="sticky top-0 z-50 border-b border-border bg-background/75 backdrop-blur-md">
  <div class="container px-4">
    <div class="flex h-[70px] items-center justify-between gap-3">
      <a href="/" class="text-2xl font-bold tracking-tight">
        Stepify
      </a>
      
      <nav class="hidden md:flex items-center space-x-6">
        <a href="/" class="text-foreground/60 hover:text-foreground">Home</a>
        <a href="/about" class="text-foreground/60 hover:text-foreground">About</a>
        <a href="/pricing" class="text-foreground/60 hover:text-foreground">Pricing</a>
      </nav>
      
      <div class="flex items-center gap-4">
        <Button on:click={toggleMode} variant="ghost" size="icon">
          {#if $mode === "light"}
            <Moon class="h-5 w-5" />
          {:else}
            <Sun class="h-5 w-5" />
          {/if}
        </Button>
        
        <Button href="/auth/login" variant="default">
          Sign In
        </Button>
      </div>
    </div>
  </div>
</header>
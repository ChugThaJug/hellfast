<!-- frontend/src/routes/+page.svelte -->
<script lang="ts">
  import { Search } from "lucide-svelte";
  
  let youtubeUrl = "";
  let processing = false;
  let error = "";
  
  async function handleSubmit() {
    if (!youtubeUrl) {
      error = "Please enter a YouTube URL";
      return;
    }
    
    // Add processing logic here
    processing = true;
    error = "";
    
    try {
      // This is a placeholder for actual API call
      setTimeout(() => {
        processing = false;
        window.location.href = "/video/demo123";
      }, 1500);
    } catch (err) {
      processing = false;
      error = "Error processing video";
    }
  }
</script>

<svelte:head>
  <title>Stepify - Transform YouTube videos into step-by-step guides</title>
</svelte:head>

<section class="container mx-auto px-4 py-24 text-center">
  <h1 class="text-5xl font-bold tracking-tight mb-6">
    Transform YouTube videos into step-by-step guides
  </h1>
  
  <p class="text-xl text-foreground/70 max-w-2xl mx-auto mb-12">
    No time to watch long videos? Let AI convert any YouTube video into a concise, 
    structured guide you can follow at your own pace.
  </p>
  
  <div class="max-w-xl mx-auto">
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {error}
      </div>
    {/if}
    
    <form on:submit|preventDefault={handleSubmit} class="flex gap-2">
      <input
        type="text"
        bind:value={youtubeUrl}
        placeholder="Paste YouTube URL here"
        class="flex-grow px-4 py-3 rounded-md border border-border focus:outline-none focus:ring-2"
      />
      
      <button 
        type="submit" 
        disabled={processing}
        class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 flex items-center"
      >
        {#if processing}
          <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2"></div>
          <span>Processing</span>
        {:else}
          <Search class="mr-2 h-4 w-4" />
          <span>Process</span>
        {/if}
      </button>
    </form>
    
    <p class="mt-4 text-sm text-foreground/60">
      Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    </p>
  </div>
</section>

<!-- Features Section -->
<section class="bg-muted py-16">
  <div class="container mx-auto px-4">
    <h2 class="text-3xl font-bold mb-12 text-center">How It Works</h2>
    
    <div class="grid md:grid-cols-3 gap-8">
      <div class="bg-background p-6 rounded-lg shadow-sm">
        <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
          <Search class="h-6 w-6 text-primary" />
        </div>
        <h3 class="text-xl font-semibold mb-2">1. Paste a YouTube URL</h3>
        <p class="text-foreground/70">
          Simply copy and paste the URL of any YouTube video you want to process.
        </p>
      </div>
      
      <div class="bg-background p-6 rounded-lg shadow-sm">
        <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
          <div class="h-6 w-6 text-primary">AI</div>
        </div>
        <h3 class="text-xl font-semibold mb-2">2. AI Processing</h3>
        <p class="text-foreground/70">
          Our AI analyzes the video content and extracts the key information.
        </p>
      </div>
      
      <div class="bg-background p-6 rounded-lg shadow-sm">
        <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
          <div class="h-6 w-6 text-primary">✓</div>
        </div>
        <h3 class="text-xl font-semibold mb-2">3. Get Structured Content</h3>
        <p class="text-foreground/70">
          Receive a well-organized step-by-step guide, summary, or bullet points.
        </p>
      </div>
    </div>
  </div>
</section>
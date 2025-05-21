<script lang="ts">
  import { videoApi } from "$lib/api";
  import { goto } from "$app/navigation";
  
  // Using Svelte 5 props
  let { compact = false } = $props();
  
  // Using Svelte 5 state
  let youtubeUrl = $state("");
  let mode = $state("detailed");
  let outputFormat = $state("step_by_step");
  let processing = $state(false);
  let error = $state("");
  
  // YouTube URL validation
  function isValidYoutubeUrl(url: string): boolean {
    const regExp = /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})$/;
    return regExp.test(url);
  }
  
  async function handleSubmit() {
    // Reset error
    error = "";
    
    // Validate YouTube URL
    if (!youtubeUrl) {
      error = "Please enter a YouTube URL";
      return;
    }
    
    if (!isValidYoutubeUrl(youtubeUrl)) {
      error = "Please enter a valid YouTube URL";
      return;
    }
    
    // Start processing
    processing = true;
    
    try {
      const result = await videoApi.processVideo(youtubeUrl, mode, outputFormat);
      
      // Redirect to job status page
      goto(`/video/job/${result.job_id}`);
    } catch (err) {
      console.error("Video processing error:", err);
      error = err instanceof Error ? err.message : "Error processing video. Please try again later.";
      processing = false;
    }
  }
</script>

<div class={compact ? "max-w-lg" : "max-w-xl mx-auto"}>
  {#if error}
    <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
      {error}
    </div>
  {/if}
  
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div>
      <label for="youtube-url" class="block text-sm font-medium mb-1">YouTube URL</label>
      <div class="flex gap-2">
        <input
          id="youtube-url"
          type="text"
          bind:value={youtubeUrl}
          placeholder="https://www.youtube.com/watch?v=..."
          class="flex-grow px-4 py-3 rounded-md border border-border focus:outline-none focus:ring-2"
          disabled={processing}
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
            <!-- Inline SVG for Search icon -->
            <svg class="mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <span>Process</span>
          {/if}
        </button>
      </div>
      <p class="mt-1 text-sm text-foreground/60">
        Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      </p>
    </div>
    
    {#if !compact}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="mode" class="block text-sm font-medium mb-1">Processing Mode</label>
          <select 
            id="mode" 
            bind:value={mode}
            class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2"
            disabled={processing}
          >
            <option value="simple">Simple (Faster)</option>
            <option value="detailed">Detailed (Better Quality)</option>
          </select>
        </div>
        
        <div>
          <label for="output-format" class="block text-sm font-medium mb-1">Output Format</label>
          <select 
            id="output-format" 
            bind:value={outputFormat}
            class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2"
            disabled={processing}
          >
            <option value="step_by_step">Step-by-Step Guide</option>
            <option value="bullet_points">Bullet Points</option>
            <option value="summary">Summary</option>
            <option value="podcast_article">Article Format</option>
          </select>
        </div>
      </div>
    {/if}
  </form>
</div>
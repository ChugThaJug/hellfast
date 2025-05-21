<!-- src/routes/video/[videoId]/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { videoApi } from "$lib/api";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  
  const videoId = $page.params.videoId;
  let videoResult = $state(null);
  let error = $state(null);
  let copied = $state(false);
  
  onMount(async () => {
    try {
      videoResult = await videoApi.getVideoResult(videoId);
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to get video result";
    }
  });
  
  function copyContent() {
    if (!videoResult) return;
    
    // Create a text representation of the content based on output format
    let contentText = "";
    
    if (videoResult.output_format === "step_by_step") {
      if (videoResult.content.sections) {
        videoResult.content.sections.forEach(section => {
          contentText += `## ${section.title}\n\n`;
          section.steps.forEach(step => contentText += `${step}\n\n`);
        });
      } else {
        contentText = JSON.stringify(videoResult.content, null, 2);
      }
    } else if (videoResult.output_format === "bullet_points") {
      if (videoResult.content.sections) {
        videoResult.content.sections.forEach(section => {
          contentText += `## ${section.title}\n\n`;
          section.bullets.forEach(bullet => contentText += `• ${bullet}\n`);
          contentText += "\n";
        });
      } else if (videoResult.content.bullets) {
        videoResult.content.bullets.forEach(bullet => contentText += `• ${bullet}\n`);
      } else {
        contentText = JSON.stringify(videoResult.content, null, 2);
      }
    } else if (videoResult.output_format === "podcast_article") {
      if (videoResult.content.sections) {
        videoResult.content.sections.forEach(section => {
          contentText += `## ${section.title}\n\n`;
          section.paragraphs.forEach(paragraph => contentText += `${paragraph}\n\n`);
        });
      } else if (videoResult.content.paragraphs) {
        videoResult.content.paragraphs.forEach(paragraph => contentText += `${paragraph}\n\n`);
      } else {
        contentText = JSON.stringify(videoResult.content, null, 2);
      }
    } else {
      contentText = videoResult.content.text || JSON.stringify(videoResult.content, null, 2);
    }
    
    navigator.clipboard.writeText(contentText);
    copied = true;
    setTimeout(() => { copied = false }, 2000);
  }
</script>

<svelte:head>
  <title>{videoResult ? videoResult.title : 'Loading...'} - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-8">
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {error}
      </div>
    {:else if videoResult}
      <div class="mb-8">
        <h1 class="text-3xl font-bold mb-2">{videoResult.title}</h1>
        
        <div class="flex flex-wrap gap-2 mb-4">
          <a 
            href={`https://www.youtube.com/watch?v=${videoId}`} 
            target="_blank" 
            rel="noopener noreferrer"
            class="inline-flex items-center text-sm bg-muted px-3 py-1 rounded-full"
          >
            <!-- External Link Icon -->
            <svg class="h-3.5 w-3.5 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
            View on YouTube
          </a>
          
          <span class="inline-flex items-center text-sm bg-muted px-3 py-1 rounded-full">
            Format: {videoResult.output_format.replace(/_/g, ' ')}
          </span>
          
          <span class="inline-flex items-center text-sm bg-muted px-3 py-1 rounded-full">
            Mode: {videoResult.stats.mode}
          </span>
        </div>
        
        <div class="flex justify-end mb-4">
          <button 
            class="inline-flex items-center px-3 py-2 border border-border rounded-md hover:bg-muted" 
            on:click={copyContent}
          >
            <!-- Copy Icon -->
            <svg class="h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            {copied ? 'Copied!' : 'Copy content'}
          </button>
        </div>
        
        <div class="bg-muted/30 border rounded-lg p-6">
          {#if videoResult.output_format === "step_by_step"}
            {#if videoResult.content.sections}
              {#each videoResult.content.sections as section}
                <div class="mb-6">
                  <h2 class="text-xl font-semibold mb-3">{section.title}</h2>
                  <div class="space-y-4">
                    {#each section.steps as step}
                      <div class="bg-background p-4 rounded border">
                        <p>{step}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/each}
            {:else}
              <div class="prose max-w-none">
                <pre>{JSON.stringify(videoResult.content, null, 2)}</pre>
              </div>
            {/if}
          {:else if videoResult.output_format === "bullet_points"}
            {#if videoResult.content.sections}
              {#each videoResult.content.sections as section}
                <div class="mb-6">
                  <h2 class="text-xl font-semibold mb-3">{section.title}</h2>
                  <ul class="list-disc pl-5 space-y-2">
                    {#each section.bullets as bullet}
                      <li>{bullet}</li>
                    {/each}
                  </ul>
                </div>
              {/each}
            {:else if videoResult.content.bullets}
              <ul class="list-disc pl-5 space-y-2">
                {#each videoResult.content.bullets as bullet}
                  <li>{bullet}</li>
                {/each}
              </ul>
            {:else}
              <div class="prose max-w-none">
                <pre>{JSON.stringify(videoResult.content, null, 2)}</pre>
              </div>
            {/if}
          {:else if videoResult.output_format === "podcast_article"}
            {#if videoResult.content.sections}
              {#each videoResult.content.sections as section}
                <div class="mb-6">
                  <h2 class="text-xl font-semibold mb-3">{section.title}</h2>
                  <div class="space-y-4">
                    {#each section.paragraphs as paragraph}
                      <p>{paragraph}</p>
                    {/each}
                  </div>
                </div>
              {/each}
            {:else if videoResult.content.paragraphs}
              <div class="space-y-4">
                {#each videoResult.content.paragraphs as paragraph}
                  <p>{paragraph}</p>
                {/each}
              </div>
            {:else}
              <div class="prose max-w-none">
                <pre>{JSON.stringify(videoResult.content, null, 2)}</pre>
              </div>
            {/if}
          {:else}
            <div class="prose max-w-none">
              <pre>{JSON.stringify(videoResult.content, null, 2)}</pre>
            </div>
          {/if}
        </div>
      </div>
      
      <div class="bg-muted/30 border rounded-lg p-6 mb-8">
        <h2 class="text-xl font-semibold mb-3">Processing Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p class="text-sm text-foreground/60">Input Tokens</p>
            <p class="text-lg font-medium">{videoResult.stats.input_tokens.toLocaleString()}</p>
          </div>
          <div>
            <p class="text-sm text-foreground/60">Output Tokens</p>
            <p class="text-lg font-medium">{videoResult.stats.output_tokens.toLocaleString()}</p>
          </div>
          <div>
            <p class="text-sm text-foreground/60">Processing Cost</p>
            <p class="text-lg font-medium">${videoResult.stats.cost.toFixed(4)}</p>
          </div>
        </div>
      </div>
    {:else}
      <div class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    {/if}
  </div>
</ProtectedRoute>
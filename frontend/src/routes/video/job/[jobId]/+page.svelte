<!-- frontend/src/routes/video/job/[jobId]/+page.svelte -->
<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { page } from "$app/stores";
  import { videoApi } from "$lib/api";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  
  const jobId = $page.params.jobId;
  let job = null;
  let error = null;
  let intervalId;
  
  onMount(async () => {
    await checkJobStatus();
    
    // Poll for job status every 3 seconds
    intervalId = setInterval(checkJobStatus, 3000);
  });
  
  onDestroy(() => {
    if (intervalId) clearInterval(intervalId);
  });
  
  async function checkJobStatus() {
    try {
      const status = await videoApi.getJobStatus(jobId);
      job = status;
      
      // If job is completed, redirect to the result page
      if (status.status === "completed") {
        clearInterval(intervalId);
        setTimeout(() => {
          window.location.href = `/video/${status.video_id}`;
        }, 1000);
      }
      
      // If job failed, stop polling
      if (status.status === "failed") {
        clearInterval(intervalId);
      }
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to get job status";
      clearInterval(intervalId);
    }
  }
</script>

<svelte:head>
  <title>Processing Video - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-8">Processing Your Video</h1>
    
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {error}
      </div>
    {:else if job}
      <div class="max-w-xl mx-auto">
        <div class="mb-6">
          <p class="text-lg mb-2">Status: <span class="font-semibold">{job.status}</span></p>
          
          <!-- Progress bar -->
          <div class="w-full bg-muted rounded-full h-4 mb-2">
            <div 
              class="bg-primary h-4 rounded-full transition-all duration-300"
              style={`width: ${job.progress * 100}%`}
            ></div>
          </div>
          
          <p class="text-sm text-foreground/60">
            {job.progress ? `${Math.round(job.progress * 100)}% complete` : 'Starting...'}
          </p>
        </div>
        
        {#if job.status === "processing"}
          <p class="text-foreground/70">
            We're processing your video. This might take a few minutes depending on the length of the video.
          </p>
        {:else if job.status === "completed"}
          <p class="text-foreground/70">
            Processing complete! Redirecting to results...
          </p>
        {:else if job.status === "failed"}
          <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md">
            <p class="font-semibold">Processing failed</p>
            <p>{job.error || "An unknown error occurred"}</p>
          </div>
        {/if}
      </div>
    {:else}
      <div class="flex justify-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    {/if}
  </div>
</ProtectedRoute>
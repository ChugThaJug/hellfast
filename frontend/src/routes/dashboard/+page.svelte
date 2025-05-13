<!-- src/routes/dashboard/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { videoApi } from "$lib/api";
  import { Eye, Trash2 } from "lucide-svelte";
  import ProtectedRoute from "$lib/components/auth/ProtectedRoute.svelte";
  
  let videos = [];
  let loading = true;
  let error = null;
  
  onMount(async () => {
    try {
      const result = await videoApi.getUserVideos();
      videos = result;
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to load videos";
    } finally {
      loading = false;
    }
  });
  
  function viewVideo(videoId) {
    goto(`/video/${videoId}`);
  }
  
  async function deleteVideo(videoId) {
    if (!confirm("Are you sure you want to delete this video?")) {
      return;
    }
    
    try {
      await videoApi.deleteVideo(videoId);
      videos = videos.filter(v => v.video_id !== videoId);
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to delete video";
    }
  }
  
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  }
</script>

<svelte:head>
  <title>Your Dashboard - Stepify</title>
</svelte:head>

<ProtectedRoute>
  <div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-3xl font-bold">Your Videos</h1>
      <a 
        href="/" 
        class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
      >
        Process New Video
      </a>
    </div>
    
    {#if error}
      <div class="bg-destructive/15 text-destructive px-4 py-3 rounded-md mb-4" role="alert">
        {error}
      </div>
    {/if}
    
    {#if loading}
      <div class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    {:else if videos.length === 0}
      <div class="text-center py-12 bg-muted/30 rounded-lg">
        <h2 class="text-xl font-semibold mb-2">No videos processed yet</h2>
        <p class="text-foreground/70 mb-4">
          Start by processing your first YouTube video
        </p>
        <a 
          href="/" 
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Process a Video
        </a>
      </div>
    {:else}
      <div class="bg-muted/30 border rounded-lg overflow-hidden">
        <table class="w-full">
          <thead>
            <tr class="bg-muted/50">
              <th class="px-4 py-3 text-left font-semibold">Title</th>
              <th class="px-4 py-3 text-left font-semibold">Format</th>
              <th class="px-4 py-3 text-left font-semibold">Status</th>
              <th class="px-4 py-3 text-left font-semibold">Date</th>
              <th class="px-4 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each videos as video}
              <tr class="border-t">
                <td class="px-4 py-4">
                  <div class="max-w-md truncate">{video.title || 'Untitled Video'}</div>
                </td>
                <td class="px-4 py-4">
                  {video.output_format.replace(/_/g, ' ')}
                </td>
                <td class="px-4 py-4">
                  <span class={`inline-block px-2 py-1 rounded-full text-xs 
                    ${video.status === 'completed' ? 'bg-green-100 text-green-800' : 
                      video.status === 'failed' ? 'bg-red-100 text-red-800' : 
                      'bg-yellow-100 text-yellow-800'}`}>
                    {video.status}
                  </span>
                </td>
                <td class="px-4 py-4 text-foreground/70">
                  {formatDate(video.created_at)}
                </td>
                <td class="px-4 py-4 text-right">
                  <div class="flex justify-end gap-2">
                    <button 
                      class="p-1 rounded-md hover:bg-muted" 
                      on:click={() => viewVideo(video.video_id)}
                      disabled={video.status !== 'completed'}
                    >
                      <Eye class="h-4 w-4" />
                    </button>
                    <button 
                      class="p-1 rounded-md hover:bg-muted" 
                      on:click={() => deleteVideo(video.video_id)}
                    >
                      <Trash2 class="h-4 w-4 text-destructive" />
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</ProtectedRoute>
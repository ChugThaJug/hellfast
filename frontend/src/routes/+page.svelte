<!-- frontend/src/routes/+page.svelte -->
<script lang="ts">
  import { Search } from "lucide-svelte";
  import VideoProcessForm from "$lib/components/video/VideoProcessForm.svelte";
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
    <VideoProcessForm />
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
<script lang="ts">
  import { Search } from "lucide-svelte";
  import VideoProcessForm from "$lib/components/video/VideoProcessForm.svelte";
  import { onMount } from 'svelte';
  
  let backendUrl = 'Loading...';
  let currentDomain = 'Loading...';
  
  onMount(() => {
    currentDomain = window.location.origin;
    backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  });
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

<!-- Additional Section -->
<div class="container">
  <h1>Hellfast Application</h1>
  <p>SvelteKit application successfully deployed to Cloudflare Pages!</p>
  
  <div class="card">
    <h2>Backend Connection</h2>
    <p>The backend should be running at:</p>
    <div class="info">
      <code>{backendUrl}</code>
    </div>
    
    <div style="margin-top: 2rem;">
      <a href="/auth/login" class="btn">Go to Login</a>
    </div>
  </div>
  
  <div class="card">
    <h2>Paddle Integration</h2>
    <p>Configure your Paddle integration by adding this domain to your approved domains list.</p>
    <div class="info">
      <p>Current domain: <code>{currentDomain}</code></p>
    </div>
  </div>
</div>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    text-align: center;
  }
  .card {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin: 2rem 0;
  }
  .btn {
    background: #0078ff;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: bold;
    display: inline-block;
    cursor: pointer;
  }
  .info {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 4px;
    margin-top: 1rem;
  }
</style>
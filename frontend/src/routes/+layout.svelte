<!-- src/routes/+layout.svelte -->
<script>
  import "../app.css";
  import { ModeWatcher } from "mode-watcher";
  import Header from "$lib/components/layout/Header.svelte";
  import Footer from "$lib/components/layout/Footer.svelte";
</script>

<div class="flex flex-col min-h-screen">
  <ModeWatcher />
  <Header />
  <main class="flex-grow">
    <slot />
  </main>
  <Footer />
</div>
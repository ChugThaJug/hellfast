<!-- src/lib/components/layout/Footer.svelte -->
<footer class="border-t border-border bg-background py-6">
  <div class="container px-4">
    <div class="flex flex-col md:flex-row justify-between items-center">
      <div class="mb-4 md:mb-0">
        <p class="text-sm text-foreground/60">
          © {new Date().getFullYear()} Stepify. All rights reserved.
        </p>
      </div>
      
      <div class="flex space-x-4">
        <a href="/terms" class="text-sm text-foreground/60 hover:text-foreground">
          Terms
        </a>
        <a href="/privacy" class="text-sm text-foreground/60 hover:text-foreground">
          Privacy
        </a>
        <a href="/contact" class="text-sm text-foreground/60 hover:text-foreground">
          Contact
        </a>
      </div>
    </div>
  </div>
</footer>
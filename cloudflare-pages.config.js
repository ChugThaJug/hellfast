// Cloudflare Pages configuration
module.exports = {
  build: {
    command: "cd frontend && npm install && npm run build",
    directory: "frontend/.svelte-kit/output/client",
    environment: {
      NODE_VERSION: "18"
    }
  },
  routes: [
    { pattern: "/*", path: "/index.html", status: 200 }
  ]
};

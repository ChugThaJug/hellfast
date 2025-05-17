/**
 * Simple app creator for Cloudflare Pages deployment
 */
export function createApp() {
  // Create a simple container element
  const app = document.createElement('div');
  app.innerHTML = `
    <div style="padding: 2rem; text-align: center; font-family: system-ui, sans-serif;">
      <h1>Hellfast Application</h1>
      <p>Deployment successful! The frontend is now running on Cloudflare Pages.</p>
      <p>Backend URL: <code id="api-url">${import.meta.env.VITE_API_URL || 'Not configured'}</code></p>
      <div style="margin-top: 2rem;">
        <a href="/auth/login" style="padding: 0.5rem 1rem; background: #0078ff; color: white; text-decoration: none; border-radius: 4px;">
          Go to Login
        </a>
      </div>
    </div>
  `;
  
  return app;
}

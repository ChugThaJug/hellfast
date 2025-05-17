// Simple standalone entry point for Cloudflare Pages build
import { createApp } from './lib/app';

// Create and mount the app
const app = createApp();
document.getElementById('app')?.appendChild(app);

// Export for potential SSR usage
export default app;

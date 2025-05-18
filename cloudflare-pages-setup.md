# Cloudflare Pages Frontend-Only Deployment

When deploying to Cloudflare Pages, use these settings in the dashboard:

## Build Configuration
- **Root directory**: `frontend`
- **Build command**: `npm install && npm run build`
- **Build output directory**: `build`

## Environment Variables
- **NODE_VERSION**: `18`
- **VITE_API_URL**: `http://localhost:8000` (or your production backend URL)

This setup ensures that Cloudflare Pages only processes the frontend code and ignores any Python backend code.

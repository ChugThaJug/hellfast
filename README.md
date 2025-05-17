# Hellfast Application

## Deploying to Cloudflare Pages

When deploying to Cloudflare Pages, use these build settings:

- **Build command**: `cd frontend && npm install && npm run build`
- **Build output directory**: `frontend/dist`
- **Root directory**: (leave blank)

### Environment Variables

Set the following environment variables in your Cloudflare Pages dashboard:

- `VITE_API_URL`: Your backend API URL (e.g., `https://api.yourdomain.com` or `http://localhost:8000` for local development)

## Local Development

1. Start the backend: `python main.py`
2. Start the frontend: `cd frontend && npm run dev`

# Hellfast Deployment Test Plan

This document outlines steps to verify that the deployment process works correctly for both the backend and frontend components.

## Prerequisites

1. Cloudflare account with Pages access
2. Render.com account (for backend)
3. GitHub repository with the Hellfast codebase
4. Paddle account for payment integration (optional for testing)

## Backend Deployment Test

### 1. Local Verification
```powershell
# Ensure dependencies are up to date
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Verify API endpoints
curl http://localhost:8000/docs
```

### 2. Docker Verification
```powershell
# Build and run with Docker Compose
docker-compose up --build

# Verify API endpoints
curl http://localhost:8000/docs
```

### 3. Render.com Deployment
1. Connect GitHub repository to Render.com
2. Create a new Web Service with:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `SECRET_KEY`: Secret key for JWT
   - `FRONTEND_URL`: Cloudflare Pages URL
   - `PADDLE_PUBLIC_KEY`: Paddle public key
   - `PADDLE_SECRET_KEY`: Paddle secret key
4. Deploy and verify endpoints at `https://hellfast-api.onrender.com/docs`

## Frontend Deployment Test

### 1. Local Build Verification
```powershell
cd frontend
npm install
npm run build
npm run preview
```

### 2. Cloudflare Pages Deployment (Manual)
1. Navigate to Cloudflare Pages dashboard
2. Connect GitHub repository
3. Configure build settings:
   - Framework preset: None (Custom)
   - Build command: `PowerShell -ExecutionPolicy Bypass -File ./cloudflare-build.ps1`
   - Build output directory: `build`
   - Root directory: `/frontend`
4. Set environment variables:
   - `VITE_API_URL`: Backend API URL
   - `VITE_API_BASE_URL`: Same as above
   - `VITE_APP_ENV`: `production`
5. Deploy and verify at the provided Cloudflare Pages URL

### 3. Direct Wrangler Deployment
```powershell
cd frontend
npm install -g wrangler
wrangler login
./deploy-cloudflare.ps1
```

## Integration Tests

After both deployments are complete:

1. **User Registration Test**: Create a new account on the frontend
2. **Authentication Test**: Log in with the created account
3. **API Integration Test**: Process a test video from the dashboard
4. **Payment Flow Test** (if Paddle is configured): Test the subscription process

## Troubleshooting

### Common Backend Issues
- Database connection errors: Verify PostgreSQL connection string
- CORS errors: Ensure the frontend URL is correctly added to allowed origins
- Environment variable issues: Check all required variables are set in Render.com

### Common Frontend Issues
- "window is not defined" errors: Check client.ts for browser environment checks
- API connection issues: Verify VITE_API_URL points to correct backend
- Build failures: Check SvelteKit version compatibility with Svelte

## Rollback Plan

If deployment issues occur:

1. **Backend**: Revert to the previous Render.com deployment
2. **Frontend**: Use Cloudflare Pages rollback feature to return to the previous version

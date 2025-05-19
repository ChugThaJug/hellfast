# Hellfast - YouTube Processing Application

## Project Overview
Hellfast is a full-stack application for processing YouTube videos, with various output formats and subscription plans. It consists of a FastAPI backend and a SvelteKit frontend.

## System Architecture
- **Backend**: FastAPI (Python 3.11+) with PostgreSQL for production
- **Frontend**: SvelteKit 2.0.0 with Svelte 4.2.7 and TailwindCSS
- **Deployment**: Backend on Render.com, Frontend on Cloudflare Pages

## Local Development Setup

### Backend Setup
1. Create a Python virtual environment:
   ```powershell
   python -m venv hellfast
   .\hellfast\Scripts\Activate.ps1  # On Windows
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```powershell
   # For Windows PowerShell
   $env:DATABASE_URL = "sqlite:///./test.db"
   $env:SECRET_KEY = "your-development-secret-key"
   $env:PADDLE_PUBLIC_KEY = "your-paddle-public-key"
   $env:PADDLE_SECRET_KEY = "your-paddle-secret-key"
   ```

4. Run the application:
   ```powershell
   uvicorn app.main:app --reload
   ```

### Using Docker Compose
Alternatively, use Docker Compose for local development:
```powershell
docker-compose up --build
```

### Frontend Setup
1. Navigate to frontend directory:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Create a `.env.development` file:
   ```
   VITE_API_URL=http://localhost:8000
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_ENV=development
   ```

4. Start development server:
   ```powershell
   npm run dev
   ```

## Production Deployment

### Backend Deployment
1. **Render.com**:
   - Connect your GitHub repository
   - Create a new Web Service
   - Choose Docker runtime
   - Set required environment variables:
     - `DATABASE_URL`: PostgreSQL connection string
     - `SECRET_KEY`: Secret key for JWT token generation
     - `PADDLE_PUBLIC_KEY`: Your Paddle public key
     - `PADDLE_SECRET_KEY`: Your Paddle secret key
     - `FRONTEND_URL`: Your frontend URL (e.g., https://hellfast.pages.dev)
   - Deploy

### Frontend Deployment on Cloudflare Pages
1. **Git Integration Method**:
   - Connect GitHub repository to Cloudflare Pages
   - Configure build settings:
     - Framework preset: None (Custom)
     - Build command: `PowerShell -ExecutionPolicy Bypass -File ./cloudflare-build.ps1`
     - Build output directory: `build`
     - Root directory: `/frontend`
     - Node.js version: 18
   - Add environment variables:
     - `VITE_API_URL`: Backend API URL (e.g., https://hellfast-api.onrender.com)
     - `VITE_API_BASE_URL`: Same as above
     - `VITE_APP_ENV`: `production`

2. **Direct Deployment via Wrangler**:
   - Run the deployment script:
     ```powershell
     cd frontend
     ./deploy-cloudflare.ps1
     ```

## Environment Variables

### Backend (Production)
- `DATABASE_URL`: PostgreSQL database connection URL
- `SECRET_KEY`: Secret key for JWT token generation
- `APP_ENV`: Application environment (development, production)
- `PADDLE_PUBLIC_KEY`: Your Paddle public key for payment integration
- `PADDLE_SECRET_KEY`: Your Paddle secret key
- `FRONTEND_URL`: Your frontend application URL
- `PADDLE_CHECKOUT_SUCCESS_URL`: Success URL for Paddle payments
- `PADDLE_CHECKOUT_CANCEL_URL`: Cancel URL for Paddle payments

### Frontend
- `VITE_API_URL`: Backend API URL
- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_APP_ENV`: Environment (development, production)

## Project Structure
- `app/`: Backend FastAPI application
  - `api/`: API routes and endpoints
  - `core/`: Core settings and configurations
  - `db/`: Database models and connections
  - `dependencies/`: Dependency injection components
  - `models/`: Data models
  - `services/`: Business logic services
    - `auth.py`: Authentication service
    - `paddle.py`: Payment integration with Paddle
    - `subscription.py`: Subscription management
    - `youtube.py`: YouTube video processing
  - `utils/`: Utility functions
- `frontend/`: SvelteKit frontend application
  - `src/`: Source code
    - `lib/`: Shared libraries
    - `routes/`: Application routes
  - `static/`: Static files
  - `build/`: Production build output

## Recent Fixes and Updates (May 2025)

1. **Backend Improvements**:
   - Updated `settings.py` to use environment variables instead of hard-coded values
   - Created Dockerfile and docker-compose.yml for containerized deployment
   - Updated requirements.txt to use newer Pydantic 2.x
   - Improved environment variable handling

2. **Frontend Fixes**:
   - Fixed SvelteKit/Svelte version compatibility issues by using Svelte 4.2.7 with SvelteKit 2.0.0
   - Updated client.ts to properly handle SSR by checking browser environment
   - Added hooks.client.ts with proper initialization function
   - Fixed "window is not defined" errors during SSR
   - Added missing dependencies for proper styling

3. **Deployment Configuration**:
   - Created PowerShell scripts for Cloudflare Pages deployment
   - Updated cloudflare.toml and wrangler.toml configurations
   - Added deployment documentation
  - `static/`: Static assets

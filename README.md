# Hellfast - YouTube Processing API

## Project Overview
Hellfast is an API service for processing YouTube videos with various output formats and subscription plans.

## Local Development Setup

### Backend Setup
1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   # For Windows PowerShell
   $env:DATABASE_URL = "sqlite:///./test.db"
   $env:SECRET_KEY = "your-development-secret-key"
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Using Docker Compose
Alternatively, use Docker Compose for local development:
```bash
docker-compose up --build
```

### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Deployment Options

### Backend Deployment
1. **Render.com**:
   - Connect your GitHub repository
   - Create a new Web Service
   - Choose Docker runtime
   - Set required environment variables
   - Deploy

2. **Railway.app**:
   - Import repository from GitHub
   - Configure environment variables
   - Deploy

### Frontend Deployment
1. **Netlify**:
   - Connect GitHub repository
   - Use build settings from netlify.toml
   - Deploy

2. **Cloudflare Pages**:
   - Connect GitHub repository
   - Set build command: `npm run build`
   - Set build directory: `build`
   - Deploy

## Environment Variables
### Backend
- `DATABASE_URL`: PostgreSQL database connection URL
- `SECRET_KEY`: Secret key for JWT token generation
- `APP_ENV`: Application environment (development, production)
- Additional API keys as needed

### Frontend
- `VITE_API_URL`: Backend API URL

## Project Structure
- `app/`: Backend FastAPI application
  - `api/`: API routes
  - `core/`: Core settings and configurations
  - `db/`: Database models and connections
  - `dependencies/`: Dependency injection components
  - `models/`: Data models
  - `services/`: Business logic
  - `utils/`: Utility functions
- `frontend/`: SvelteKit frontend application
  - `src/`: Source code
  - `static/`: Static assets

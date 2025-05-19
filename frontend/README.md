# Hellfast Frontend

This is the frontend application for Hellfast, built with SvelteKit 2.0.0 and Svelte 4.2.7. This README provides comprehensive instructions for development, building, and deployment.

## Development Setup

1. **Clone the repository**

2. **Install dependencies**
   ```powershell
   cd frontend
   npm install
   ```

3. **Set up environment variables**
   - Create a `.env.development` file with:
   ```
   VITE_API_URL=http://localhost:8000
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_ENV=development
   ```

4. **Start the development server**
   ```powershell
   npm run dev
   
   # or open it in a browser automatically
   npm run dev -- --open
   ```

## Building for Production

To create a production build:

```powershell
npm run build
```

You can preview the production build with:

```powershell
npm run preview
```

For serving the built application:

```powershell
npm run serve
```

## Deployment Options

### Cloudflare Pages Deployment

Hellfast is configured for deployment on Cloudflare Pages using either Git integration or direct deployment via Wrangler CLI.

#### Method 1: Git Integration (Recommended)

1. **Sign up for Cloudflare Pages**
   - Go to [Cloudflare Pages](https://pages.cloudflare.com/) and sign up
   - Connect your GitHub account

2. **Create a new project**
   - Select your GitHub repository
   - Configure build settings:
     - Framework preset: None (Custom)
     - Build command: `PowerShell -ExecutionPolicy Bypass -File ./cloudflare-build.ps1`
     - Build output directory: `build`
     - Root directory: `/frontend` (if your repository has the frontend in a subfolder)
     - Node.js version: 18

3. **Add Environment Variables**
   - `VITE_API_URL`: Your backend API URL (e.g., `https://hellfast-api.onrender.com`)
   - `VITE_API_BASE_URL`: Same as above
   - `VITE_APP_ENV`: `production`

4. **Deploy**
   - Click "Save and Deploy"
   - Wait for the build to complete

#### Method 2: Direct Deployment via Wrangler

1. **Install Wrangler CLI**
   ```powershell
   npm install -g wrangler
   ```

2. **Login to Cloudflare**
   ```powershell
   wrangler login
   ```

3. **Deploy using the script**
   ```powershell
   ./deploy-cloudflare.ps1
   ```
   
   Or manually:
   ```powershell
   npm run build
   wrangler pages deploy build --project-name hellfast
   ```

### Environment Configuration

The application uses different environment variables depending on the deployment context:

- **Development**: Values in `.env.development`
- **Production**: Values in `.env.production` or set via the deployment platform

## Troubleshooting

### "window is not defined" Errors
This project uses SvelteKit 2.0.0 with Svelte 4.2.7 to avoid SSR compatibility issues. The `client.ts` file includes checks to ensure browser-specific code only runs in the browser environment.

### Package Synchronization Issues
If you encounter package synchronization problems, run:

```powershell
./fix-packages.ps1
```

## Custom Domain Setup

1. In Cloudflare Pages, go to your project settings
2. Click on "Custom domains"
3. Add your custom domain
4. Update DNS settings according to Cloudflare instructions

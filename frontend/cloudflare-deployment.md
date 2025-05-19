# Cloudflare Pages Deployment Guide (May 2025 Update)

This guide explains how to deploy the frontend on Cloudflare Pages with the latest configuration.

## Setup Steps

1. **Sign up for Cloudflare Pages**
   - Go to [Cloudflare Pages](https://pages.cloudflare.com/) and sign up if you haven't already
   - Connect your GitHub account

2. **Create a new project**
   - Click "Create a project"
   - Select your GitHub repository
   - Configure the build settings:
     - Framework preset: None (Custom)
     - Build command: `bash ./build-cloudflare.sh` (recommended) or `PowerShell -ExecutionPolicy Bypass -File ./cloudflare-build.ps1`
     - Build output directory: `build`
     - Root directory: `/frontend` (if your repository has the frontend in a subfolder)
     - Node.js version: 18

3. **Add Environment Variables**
   - For production: `VITE_API_URL=https://hellfast-api.onrender.com` (or your actual API URL)
   - For local testing: `VITE_API_URL=http://localhost:8000`
   
## Alternative Method: Direct Upload

If you're having issues with the Git-based deployment, you can use Wrangler to deploy directly:

1. **Install Wrangler CLI**
   ```powershell
   npm install -g wrangler
   ```

2. **Login to Cloudflare**
   ```powershell
   wrangler login
   ```

3. **Build and Deploy**
   ```powershell
   cd frontend
   npm run build
   wrangler pages deploy build --project-name hellfast
   ```
   - For production, you'll update this to your actual backend URL

4. **Deploy**
   - Click "Save and Deploy"
   - Wait for the build to complete

## Local Development

When running locally:
1. Start your backend: `python main.py` from the project root
2. Use the Cloudflare deployment URL for the frontend

## Testing Paddle Integration

1. Update your Paddle dashboard with your new Cloudflare domain (e.g., `your-project.pages.dev`)
2. Update your .env file to set:
   ```
   FRONTEND_URL=https://your-project.pages.dev
   PADDLE_CHECKOUT_SUCCESS_URL=https://your-project.pages.dev/subscription/success
   PADDLE_CHECKOUT_CANCEL_URL=https://your-project.pages.dev/subscription/cancel
   ```

## Setting Up Custom Domain

1. In Cloudflare Pages, go to your project settings
2. Click on "Custom domains"
3. Add your custom domain
4. Update DNS settings according to Cloudflare instructions
5. Update your Paddle dashboard with the custom domain

## Troubleshooting Common Deployment Issues

### Wrangler Configuration Errors

If you see errors related to the wrangler.toml file:

1. **Update to a simplified configuration**:
   ```toml
   # wrangler.toml for Cloudflare Pages deployment
   name = "hellfast-frontend"
   pages_build_output_dir = "build"
   compatibility_flags = ["nodejs_compat"]

   [[routes]]
   pattern = "/*"
   fallback = "index.html"
   ```

2. **Consider removing the wrangler.toml** file entirely for Cloudflare Pages Git deployments and rely on the UI configuration.

### Build Command Errors

If the PowerShell build script fails:

1. **Use the Bash script instead**: 
   - Change the build command to: `bash ./build-cloudflare.sh`

2. **Directly use npm commands**:
   ```
   npm install && npm run build
   ```

### Environment Variable Issues

If your application is not connecting to the API:

1. Check that environment variables are correctly set in Cloudflare Pages dashboard
2. Verify the variables are being properly loaded during the build process
3. You can inspect build logs in the Cloudflare Pages dashboard

### Manual Deployment Fallback

If all else fails, build locally and deploy with Wrangler:

```bash
cd frontend
npm install
npm run build
npx wrangler pages deploy build --project-name hellfast
```

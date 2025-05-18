# Deploying to Vercel

Follow these steps to deploy your frontend on Vercel:

## Step 1: Login or Create a Vercel Account

1. Go to [vercel.com](https://vercel.com/) and sign in or create an account
2. You can use GitHub, GitLab, or Bitbucket authentication for easy integration

## Step 2: Import Your Repository

1. Click on "Add New..." and select "Project"
2. Select your GitHub repository
3. Configure the project:
   - Framework Preset: SvelteKit
   - Root Directory: `frontend`
   - Build Command: `npm install --no-package-lock postcss-nesting && npm run build`
   - Output Directory: `build`

## Step 3: Configure Environment Variables

Add the following environment variables:
- `VITE_API_URL`: Your backend API URL (e.g., http://localhost:8000 for local development)

## Step 4: Deploy

1. Click "Deploy" and wait for the build to complete
2. Vercel will provide a URL for your deployed application

## Step 5: Configure Custom Domain (Optional)

1. Go to your project settings
2. Select "Domains"
3. Add your custom domain
4. Follow the instructions to configure DNS settings

## Step 6: Configure Paddle Integration

1. Add your Vercel domain (both the automatic .vercel.app domain and any custom domains) to your Paddle dashboard
2. Make sure your backend CORS settings include your Vercel domain

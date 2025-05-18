# Vercel Deployment Guide

This guide explains how to deploy the frontend on Vercel while keeping the backend running locally.

## Setup Steps

1. **Sign up for Vercel**
   - Go to [Vercel](https://vercel.com/) and sign up if you haven't already
   - Connect your GitHub account

2. **Create a new project**
   - Click "Add New Project"
   - Import your Git repository
   - Configure the build settings:
     - Framework preset: SvelteKit
     - Root directory: `frontend`
     - Build command: `npm install --no-package-lock && npm run build`
     - Output directory: `build`

3. **Add Environment Variables**
   - Add `VITE_API_URL=http://localhost:8000` for local development
   - For production, you'll update this to your actual backend URL

4. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete

## Local Development

When running locally:
1. Start your backend: `python main.py` from the project root
2. Use the Vercel deployment URL for the frontend

## Testing Paddle Integration

1. Update your Paddle dashboard with your new Vercel domain (e.g., `your-project.vercel.app`)
2. Update your .env file to set:
   ```
   FRONTEND_URL=https://your-project.vercel.app
   PADDLE_CHECKOUT_SUCCESS_URL=https://your-project.vercel.app/subscription/success
   PADDLE_CHECKOUT_CANCEL_URL=https://your-project.vercel.app/subscription/cancel
   ```

## Setting Up Custom Domain

1. In Vercel, go to your project settings
2. Click on "Domains"
3. Add your custom domain
4. Update DNS settings according to Vercel instructions
5. Update your Paddle dashboard with the custom domain

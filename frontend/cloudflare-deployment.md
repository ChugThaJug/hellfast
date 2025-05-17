# Cloudflare Pages Deployment Guide

This guide explains how to deploy the frontend on Cloudflare Pages while keeping the backend running locally.

## Setup Steps

1. **Sign up for Cloudflare Pages**
   - Go to [Cloudflare Pages](https://pages.cloudflare.com/) and sign up if you haven't already
   - Connect your GitHub account

2. **Create a new project**
   - Click "Create a project"
   - Select your GitHub repository
   - Configure the build settings:
     - Framework preset: Svelte
     - Build command: `npm run build`
     - Build output directory: `dist`
     - Root directory: `/frontend` (if your repository has the frontend in a subfolder)

3. **Add Environment Variables**
   - Add `VITE_API_URL=http://localhost:8000` for local development
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

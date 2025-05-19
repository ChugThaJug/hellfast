# Configuring Cloudflare Pages Environment Variables

This guide explains how to set up environment variables for your Hellfast application in Cloudflare Pages.

## Overview

Environment variables allow you to configure your application for different environments (development, production) without changing the code. For Hellfast's frontend, we need to configure several key variables.

## Accessing Cloudflare Pages Settings

1. Log in to your Cloudflare account at [https://dash.cloudflare.com](https://dash.cloudflare.com)
2. Navigate to "Pages" from the sidebar
3. Select your Hellfast project
4. Click on "Settings" and then "Environment variables"

## Required Environment Variables

### Production Environment Variables

These variables will be used when your site is deployed to production:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| VITE_API_URL | https://hellfast-api.onrender.com | Points to your backend API |
| VITE_API_BASE_URL | https://hellfast-api.onrender.com | Same as above |
| VITE_APP_ENV | production | Specifies the environment |

### Development/Preview Environment Variables

These variables will be used for preview deployments (e.g., from pull requests):

| Variable Name | Value | Description |
|---------------|-------|-------------|
| VITE_API_URL | https://hellfast-api-staging.onrender.com | Points to staging API |
| VITE_API_BASE_URL | https://hellfast-api-staging.onrender.com | Same as above |
| VITE_APP_ENV | staging | Specifies the environment |

## Setting Up Environment Variables

1. In the "Environment variables" section, click "Add variable"
2. Enter the variable name (e.g., `VITE_API_URL`)
3. Enter the variable value (e.g., `https://hellfast-api.onrender.com`)
4. Under "Deployment environments", select "Production" or both "Production" and "Preview" as needed
5. Click "Save"
6. Repeat for each variable

## Verifying Configuration

After setting up your environment variables:

1. Trigger a new deployment
2. Once deployed, check your application to ensure it's connecting to the correct API
3. Verify that features like authentication and video processing work correctly

## Updating Environment Variables

If you need to update your environment variables:

1. Navigate to the "Environment variables" section
2. Click "Edit" next to the variable you want to change
3. Update the value
4. Click "Save"
5. Redeploy your application to apply the changes

## Troubleshooting

If your application isn't connecting to the API correctly:

1. Check the browser console for any errors
2. Verify that the environment variables are set correctly
3. Ensure that your API is accessible from the Cloudflare Pages domain
4. Check that CORS is properly configured on your backend

#!/bin/bash

echo "Starting Cloudflare Pages build process..."

# Install dependencies using legacy-peer-deps to avoid conflicts
echo "Installing dependencies..."
npm install --legacy-peer-deps

# Build the project
echo "Building project..."
npm run build

# Ensure the _redirects file is in place for SPA routing
echo "/* /index.html 200" > build/_redirects

echo "Build completed successfully!"
#!/bin/bash

echo "Starting Cloudflare Pages build process..."

# Install dependencies using standard npm install
echo "Installing dependencies..."
npm install

# Build the project
echo "Building project..."
npm run build

# Ensure the _redirects file is in place for SPA routing
echo "/* /index.html 200" > build/_redirects

echo "Build completed successfully!"
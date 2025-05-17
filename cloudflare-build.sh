#!/bin/bash

echo "Starting Cloudflare Pages build process..."

# Go to the frontend directory
cd frontend

# Install dependencies without using package-lock.json
echo "Installing dependencies..."
npm install --no-package-lock

# Build the project
echo "Building project..."
npm run build

# Ensure the build directory exists
if [ -d "build" ]; then
  echo "Build directory exists"
else
  # If using .svelte-kit/output, copy it to build
  if [ -d ".svelte-kit/output/client" ]; then
    echo "Copying from .svelte-kit/output/client to build"
    mkdir -p build
    cp -r .svelte-kit/output/client/* build/
  else
    echo "No build output found"
    exit 1
  fi
fi

# Create SPA redirects
echo "/* /index.html 200" > build/_redirects

echo "Build completed successfully!"

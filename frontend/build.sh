#!/bin/bash

echo "Starting build process..."

# Install dependencies using clean install
npm ci || npm install

# Build the project
npm run build

# Ensure _redirects file is copied to the build directory for SPA routing
echo "/* /index.html 200" > build/_redirects

echo "Build completed successfully"

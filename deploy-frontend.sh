#!/bin/bash

# Navigate to frontend directory
cd frontend

# Clean installation artifacts
rm -rf node_modules
rm -rf .svelte-kit
rm -f package-lock.json

# Install dependencies without creating a package-lock.json file
echo "Installing dependencies..."
npm install --no-package-lock

# Install postcss-nesting explicitly
echo "Installing postcss-nesting..."
npm install postcss-nesting --no-save

# Build the project
echo "Building project..."
npm run build

echo "Build completed successfully"

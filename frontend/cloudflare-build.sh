#!/bin/bash

echo "Starting Cloudflare Pages build process..."

# Ensure we have the right node version
echo "Node version:"
node -v

# Install dependencies using a standard install to update package-lock.json
echo "Installing dependencies..."
npm install

# Create .env file for build
echo "Creating production environment variables..."
cat > .env << EOL
VITE_API_URL=https://hellfast-api.onrender.com
VITE_API_BASE_URL=https://hellfast-api.onrender.com
VITE_APP_ENV=production
EOL

# Build the project
echo "Building project..."
npm run build

# Ensure the _redirects file is in place for SPA routing
echo "/* /index.html 200" > build/_redirects

echo "Build completed successfully!"

#!/bin/bash

echo "Starting Cloudflare Pages build process..."

# Display Node and NPM versions
echo "Node and NPM versions:"
node -v
npm -v

# Create .env file for build with production values
echo "Creating production environment variables..."
cat > .env << EOL
VITE_API_URL=https://hellfast-api.onrender.com
VITE_API_BASE_URL=https://hellfast-api.onrender.com
VITE_APP_ENV=production
EOL

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the project
echo "Building project..."
npm run build

# Ensure the _redirects file is in place for SPA routing
echo "Creating _redirects file for SPA routing..."
echo "/* /index.html 200" > build/_redirects

echo "Build completed successfully!"
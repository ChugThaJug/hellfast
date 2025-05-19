# Cloudflare Pages build script (PowerShell version)
Write-Host "Starting Cloudflare Pages build process..." -ForegroundColor Cyan

# Display Node version
Write-Host "Node version:" -ForegroundColor Cyan
node -v

# Create .env file for build with production values
Write-Host "Creating production environment variables..." -ForegroundColor Cyan
@"
VITE_API_URL=https://hellfast-api.onrender.com
VITE_API_BASE_URL=https://hellfast-api.onrender.com
VITE_APP_ENV=production
"@ | Out-File -FilePath ".env" -Encoding utf8

# Install dependencies normally (no package-lock enforcement for Cloudflare)
Write-Host "Installing dependencies..." -ForegroundColor Cyan
npm install

# Build the project
Write-Host "Building project..." -ForegroundColor Cyan
npm run build:cloudflare || npm run build  # Fallback to regular build if cloudflare-specific build fails

# Ensure the _redirects file is in place for SPA routing
Write-Host "Creating _redirects file for SPA routing..." -ForegroundColor Cyan
"/* /index.html 200" | Out-File -FilePath "build/_redirects" -Encoding utf8

Write-Host "Build completed successfully!" -ForegroundColor Green

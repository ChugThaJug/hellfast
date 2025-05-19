# Fix package.json and package-lock.json synchronization
Write-Host "Fixing package.json and package-lock.json synchronization..." -ForegroundColor Cyan

# Remove package-lock.json if it exists
if (Test-Path -Path "package-lock.json") {
    Remove-Item -Path "package-lock.json" -Force
    Write-Host "Removed existing package-lock.json" -ForegroundColor Yellow
}

# Run a clean install to generate a fresh package-lock.json
Write-Host "Installing dependencies..." -ForegroundColor Cyan
npm install

Write-Host "Package files synchronized!" -ForegroundColor Green

# Clean up existing dependencies
Write-Host "Cleaning up existing node_modules..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue node_modules
Remove-Item -Force -ErrorAction SilentlyContinue package-lock.json

# Update package.json with compatible dependencies
Write-Host "Updating package.json..." -ForegroundColor Cyan
$packageJson = Get-Content -Path "package.json" | ConvertFrom-Json
$packageJson.devDependencies.svelte = "5.0.0-next.27"
$packageJson.dependencies = @{
    "iconify-icon" = "1.0.8"
}
$packageJson | ConvertTo-Json -Depth 100 | Set-Content -Path "package.json"

# Install with legacy peer deps
Write-Host "Installing dependencies with legacy peer deps..." -ForegroundColor Cyan
npm install --legacy-peer-deps

# Install shadcn-svelte for Svelte 5
Write-Host "Installing shadcn-svelte components..." -ForegroundColor Cyan
npx shadcn-svelte@next init --yes

Write-Host "Installation completed!" -ForegroundColor Green
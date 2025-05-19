# PowerShell script to deploy to Cloudflare Pages using Wrangler

# Check if Wrangler is installed
if (-not (Get-Command wrangler -ErrorAction SilentlyContinue)) {
    Write-Host "Wrangler CLI is not installed. Installing it now..." -ForegroundColor Yellow
    npm install -g wrangler
}

# Make sure we're logged in
Write-Host "Ensuring you're logged into Cloudflare..." -ForegroundColor Cyan
wrangler whoami

if ($LASTEXITCODE -ne 0) {
    Write-Host "Please log in to Cloudflare:" -ForegroundColor Yellow
    wrangler login
}

# Deploy to Cloudflare Pages
Write-Host "Deploying to Cloudflare Pages..." -ForegroundColor Cyan

# Ask for project name if not provided
$projectName = Read-Host -Prompt "Enter your Cloudflare Pages project name (default: hellfast)"
if ([string]::IsNullOrWhiteSpace($projectName)) {
    $projectName = "hellfast"
}

# Deploy the build folder
wrangler pages deploy build --project-name $projectName

Write-Host "Deployment complete!" -ForegroundColor Green

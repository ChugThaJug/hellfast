#!/bin/bash
# Script to fix Vercel connection issues and deploy

# Clear Vercel cache
rm -rf ~/.vercel
rm -rf .vercel

# Reinstall Vercel CLI
npm uninstall -g vercel
npm install -g vercel@latest

# Try using a direct login token instead of browser auth
echo "Get your token from https://vercel.com/account/tokens"
read -p "Enter your Vercel token: " TOKEN
vercel login --token $TOKEN

# Deploy with increased timeout
vercel --prod --timeout 120000

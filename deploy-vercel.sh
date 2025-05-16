#!/bin/bash
# Install Vercel CLI
npm install -g vercel

# Log in to Vercel (will open browser for authentication)
vercel login

# Deploy to Vercel
vercel --prod

#!/bin/bash

# First install dependencies with regular npm install
npm install

# Then build the project
npm run build

# Ensure _redirects file is copied to the build directory
cp _redirects build/ 2>/dev/null || :
cp static/_redirects build/ 2>/dev/null || :

echo "Build completed successfully"

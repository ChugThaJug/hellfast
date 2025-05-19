#!/bin/bash

echo "Fixing package.json and package-lock.json synchronization..."

# Remove package-lock.json
rm -f package-lock.json

# Run a clean install to generate a fresh package-lock.json
npm install

echo "Package files synchronized!"

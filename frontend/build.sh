#!/bin/bash

# Create the output directory
mkdir -p dist

# Copy the index.html file to the output directory
cp index.html dist/

# Create a simple CSS file
echo "body { font-family: sans-serif; }" > dist/styles.css

# Create a simple JS file
echo "console.log('Hellfast is running!');" > dist/script.js

echo "Build completed successfully!"

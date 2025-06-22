#!/bin/bash

echo "Starting NetViz Frontend..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the development server
echo "Starting development server on http://localhost:5173"
echo "Make sure the backend is running on http://localhost:3001"
npm run dev 
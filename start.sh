#!/bin/bash

# Quick start script for the Leaf Disease Detection API

set -e

echo "🚀 Starting Leaf Disease Detection API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check if Node.js dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

# Create logs directory
mkdir -p logs

# Start with PM2 in development mode
echo "Starting application with PM2..."
pm2 start ecosystem.config.js --env development

echo "✅ Application started successfully!"
echo ""
echo "📊 View status: pm2 status"
echo "📋 View logs: pm2 logs"
echo "🔍 Monitor: pm2 monit"
echo "🌐 Health check: http://localhost:3000/health"
echo ""
echo "To stop: pm2 stop leaf-disease-api"

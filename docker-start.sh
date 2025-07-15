#!/bin/bash

# SkylightSync Docker Quick Start Script

set -e

echo "🐳 SkylightSync Docker Quick Start"
echo "=================================="
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please run the setup script first:"
    echo "python setup.py"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ docker compose not found!"
    echo "Please install Docker Compose and try again."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo

# Build and start the container
echo "🔨 Building Docker image..."
docker compose build

echo "🚀 Starting SkylightSync..."
docker compose up -d

echo
echo "✅ SkylightSync is now running!"
echo
echo "📋 Useful commands:"
echo "  View logs:     docker compose logs -f"
echo "  Stop service:  docker compose down"
echo "  Restart:       docker compose restart"
echo "  Web UI:        http://localhost:5003"
echo
echo "📁 Photos will be saved to: $(grep PHOTOS_DIRECTORY .env 2>/dev/null | cut -d'=' -f2 || echo "/Users/m1/Pictures/Skylight")"
echo
echo "🔍 To check if it's working:"
echo "  docker compose logs -f" 
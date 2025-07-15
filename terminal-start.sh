#!/bin/bash

# SkylightSync Terminal Quick Start Script

set -e

echo "💻 SkylightSync Terminal Quick Start"
echo "===================================="
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please run the setup script first:"
    echo "python setup.py"
    exit 1
fi

# Check if Python is available
if ! command -v python3 > /dev/null 2>&1; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check if Chrome is available
if ! command -v google-chrome > /dev/null 2>&1 && [ ! -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo "⚠️  Chrome browser not found!"
    echo "Please install Google Chrome for best results."
fi

# Check if ChromeDriver is available
if ! command -v chromedriver > /dev/null 2>&1; then
    echo "⚠️  ChromeDriver not found!"
    echo "Please install ChromeDriver: brew install chromedriver"
fi

echo "✅ Prerequisites check passed"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo
echo "✅ SkylightSync is ready!"
echo
echo "📋 Usage options:"
echo "  Run once:      python skylight_sync.py --once"
echo "  Run continuous: python skylight_sync.py"
echo "  Custom interval: python skylight_sync.py --interval 1800"
echo "  Custom batch:   python skylight_sync.py --batch-size 10"
echo
echo "📁 Photos will be saved to: $(grep PHOTOS_DIRECTORY .env 2>/dev/null | cut -d'=' -f2 || echo "~/Pictures/Skylight")"
echo
echo "🌐 Web UI available at: http://localhost:5003"
echo
echo "🔍 To start the sync:"
echo "  python skylight_sync.py --once" 
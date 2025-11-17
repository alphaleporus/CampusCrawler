#!/bin/bash

# University Merch Bot - Setup Script
# This script will help you set up the project quickly

echo "=================================="
echo "University Merch Bot - Setup"
echo "=================================="
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✅ Python is installed"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

echo "✅ Data directory created"
echo ""

# Run configuration test
echo "🧪 Running configuration test..."
echo ""
python3 test_config.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ Setup complete!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. Update config.py with your Gmail credentials"
    echo "2. Run: python3 test_config.py"
    echo "3. Run: python3 main.py --crawl-limit 5"
    echo ""
else
    echo ""
    echo "=================================="
    echo "⚠️  Setup incomplete"
    echo "=================================="
    echo ""
    echo "Please configure your Gmail credentials in config.py"
    echo "Then run: python3 test_config.py"
    echo ""
fi

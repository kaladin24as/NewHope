#!/bin/bash
# AntiGravity Installation Script

set -e

echo "========================================="
echo "  AntiGravity Installation"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.11"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Python $required_version or higher is required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

echo ""
echo "Installing development dependencies..."
pip install pytest pytest-cov pytest-asyncio httpx black isort flake8 mypy

# Verify installation
echo ""
echo "Verifying installation..."
python verify_providers.py

echo ""
echo "========================================="
echo "  ✓ Installation Complete!"
echo "========================================="
echo ""
echo "Quick Start:"
echo "  1. Activate venv: source .venv/bin/activate"
echo "  2. Run API: make run-api"
echo "  3. Run UI: make run-ui"
echo ""
echo "Or use Docker:"
echo "  docker-compose up"
echo ""

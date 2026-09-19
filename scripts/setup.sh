#!/usr/bin/env bash
# OpenCitizen AI - Automated Setup Script (Bash)
set -euo pipefail

echo "==> Setting up OpenCitizen AI development environment..."

# 1. Backend virtual environment
echo "==> Initializing Python virtual environment in backend/.venv..."
if [ ! -d "backend/.venv" ]; then
    uv venv backend/.venv
fi

# 2. Install backend packages
echo "==> Installing backend dependencies..."
uv pip install -e "backend[dev]" --python backend/.venv

# 3. Frontend packages
echo "==> Installing frontend npm dependencies..."
cd frontend
npm install
cd ..

echo "==> Setup complete! Run ./scripts/test.sh to verify."

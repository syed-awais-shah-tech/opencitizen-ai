#!/usr/bin/env bash
# OpenCitizen AI - Test & Validation Script (Bash)
set -euo pipefail

echo "==> Running OpenCitizen AI Test Suite..."

# 1. Backend Tests
echo -e "\n[1/2] Running Backend Unit & Integration Tests..."
backend/.venv/bin/pytest backend/tests tests/backend -v

# 2. Frontend Validation
echo -e "\n[2/2] Running Frontend Validation (TypeScript / Build Check)..."
cd frontend
npm run build
cd ..

echo -e "\n==> All checks passed successfully!"

#!/usr/bin/env bash
# OpenCitizen AI - Local Development Runner (Bash)
set -euo pipefail

echo "==> Launching OpenCitizen AI Development Services..."

# Trap SIGINT to kill background jobs
trap "kill 0" EXIT

echo "Starting FastAPI Backend on http://localhost:8000..."
(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000) &

echo "Starting Next.js Frontend on http://localhost:3000..."
(cd frontend && npm run dev) &

wait

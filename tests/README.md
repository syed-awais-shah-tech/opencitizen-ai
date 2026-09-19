# OpenCitizen AI - Test Suite

This directory contains cross-service, end-to-end, and backend integration test suites.

## Directory Structure

```
tests/
├── backend/          # Integration tests for FastAPI endpoints and services
│   └── test_health.py
└── e2e/              # (Planned) End-to-end browser and workflow tests
```

## Running Tests

Execute from the workspace root:

```bash
backend\.venv\Scripts\pytest tests/backend -v
```

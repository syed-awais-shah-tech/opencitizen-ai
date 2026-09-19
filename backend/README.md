# OpenCitizen AI - Backend Service

FastAPI backend service powering OpenCitizen AI.

## Overview

The backend service coordinates:
- Evidence-grounded natural language question-answering
- Document ingestion and semantic search (Qdrant)
- Tabular dataset registration and SQL analytics (DuckDB)
- Source citation and calculation trace inspection

## Getting Started

### Local Development

1. Create and activate a Python virtual environment:
   ```bash
   uv venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # macOS / Linux
   ```

2. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. Verify health:
   ```bash
   curl http://localhost:8000/health
   ```

### Running Tests

```bash
pytest
```

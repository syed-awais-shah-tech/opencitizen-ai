# Comprehensive Testing Guide

OpenCitizen AI enforces strict verification invariants across backend services, retrieval pipelines, AI grounding, and frontend interfaces. This guide details how to execute, write, and maintain tests.

---

## 1. Test Architecture Overview

The repository features over 265 automated tests divided into:
1. **Backend Unit & Module Tests** (`backend/tests/`):
   - `test_analytics.py`: DuckDB query compiler, analytical filters, aggregate functions, and table execution.
   - `test_connectors.py`: External data source connectors, provenance tracking, schema extraction, and normalization.
   - `test_database_operations.py`: PostgreSQL metadata persistence, models, relationships, and queries.
   - `test_dataset_ingestion.py`: CSV, XLSX, and JSON tabular parsing, inferred types, and null value analysis.
   - `test_documents.py`: Document registration, metadata persistence, chunk retrieval.
   - `test_errors.py`: Global exception handlers and sanitized JSON error payloads.
   - `test_evaluation_framework.py`: Benchmark evaluation suite (retrieval precision, citation correctness, answer accuracy, latency).
   - `test_geospatial.py`: GeoJSON parsing, coordinate validation, spatial bounding, and GeoJSON export.
   - `test_health.py`: Health check and system readiness endpoints.
   - `test_hybrid_retrieval.py`: BM25 lexical search, Qdrant vector retrieval, and Reciprocal Rank Fusion reranking.
   - `test_ingestion.py`: PDF text extraction, page preservation, and chunking boundaries.
   - `test_ingestion_jobs.py`: Asynchronous background processing queue and job lifecycle transitions.
   - `test_orchestration.py`: Controlled query routing (Qdrant, DuckDB, hybrid, or unsupported).
   - `test_rag_pipeline.py`: Evidence grounding, prompt templates, and citation attribution.
   - `test_security.py`: Multi-vector security tests (magic bytes, path traversal, prompt injection, SQL injection, secret scrubbing).
   - `test_trust_layer.py`: Inspectable trust payloads, citation mapping, and confidence limitations.
   - `test_vector_search.py`: Vector store abstraction, Qdrant in-memory indexing, and top-k search.
   - `test_visualization.py`: Deterministic chart configuration generator (bar, line, pie, table).
2. **Integration Tests** (`tests/`):
   - Multi-service workflows and root API health integration.
3. **Frontend Validation** (`frontend/`):
   - TypeScript compile-time type verification (`tsc --noEmit`).
   - Next.js production build validation (`next build`).

---

## 2. Running Tests Locally

### 2.1 Backend Tests
Run all unit and integration tests using pytest:

```bash
# From workspace root using the backend virtual environment
backend\.venv\Scripts\pytest backend/tests tests -v

# Or on Linux / macOS with virtual environment activated:
pytest backend/tests tests -v
```

#### Running a Specific Test Module:
```bash
pytest backend/tests/test_hybrid_retrieval.py -v
```

#### Running with Detailed Timing:
```bash
pytest backend/tests -v --durations=10
```

### 2.2 Code Quality & Linting
Run Ruff to check linting and formatting across the backend:

```bash
backend\.venv\Scripts\ruff check backend
```

To automatically fix safe lint issues:
```bash
backend\.venv\Scripts\ruff check backend --fix
```

### 2.3 Frontend Tests & Build Validation
Navigate to `frontend/`:

```bash
cd frontend

# Strict TypeScript type check
npm run typecheck

# Production build and static page generation
npm run build
```

---

## 3. Hermetic Testing Invariant

All automated tests are designed to execute **hermetically** without requiring network connectivity, Docker containers, or paid API keys:
- **Database**: Uses SQLite in-memory or temporary SQLite database (`sqlite:///:memory:`).
- **Vector Store**: Uses Qdrant in-memory collection (`QDRANT_IN_MEMORY=true`).
- **AI Provider**: Uses `MockAIProvider` (`LLM_PROVIDER=mock`).
- **Embedding Provider**: Uses `MockEmbeddingProvider` (`EMBEDDING_PROVIDER=mock`).

### Environment Variables for Hermetic Testing
When running tests, these environment variables are set automatically via `backend/tests/conftest.py`:
```python
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["QDRANT_IN_MEMORY"] = "true"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["GEMINI_API_KEY"] = "ci-test-mock-token"
```

---

## 4. Benchmark & Quality Evaluation

OpenCitizen AI includes an automated benchmark evaluation framework to evaluate model quality, retrieval precision, and citation accuracy:

```bash
# Run benchmark evaluation suite
pytest backend/tests/test_evaluation_framework.py -v
```

Evaluation metrics computed:
- **Retrieval Precision & Recall**: Document chunk overlap against ground-truth passages.
- **Citation Precision & Recall**: Source document title attribution in synthesized answers.
- **Answer Correctness & Grounding**: Factual alignment with supplied evidence.
- **Unsupported Claim Detection**: Flagging hallucinated facts not in evidence.
- **Latency (ms)**: End-to-end response time.

See [`docs/evaluation-framework.md`](evaluation-framework.md) for full benchmark documentation.

---

## 5. Adding New Tests

When contributing a new feature or bug fix:
1. Create a corresponding test file in `backend/tests/` (e.g., `test_<feature>.py`).
2. Use `pytest` fixtures from `conftest.py` (`db_session`, `client`, etc.).
3. Write both positive cases and negative/error cases (e.g. invalid inputs, missing fields, security boundaries).
4. Verify that running `pytest backend/tests` passes 100% before committing.

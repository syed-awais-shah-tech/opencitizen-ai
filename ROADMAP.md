# OpenCitizen AI - Project Roadmap

This roadmap tracks the development milestones of OpenCitizen AI. Through rigorous incremental development, Stages 1 through 20 have been completed, verified with automated tests, and committed.

> **Status Legend:**
> - `[x]` **Completed**
> - `[~]` **In Progress**
> - `[ ]` **Planned**

---

## Completed Milestones (v1.0 Core Platform)

### Milestone 1: Core Foundation & API Layer
* [x] **Stage 1 (Repository Foundation):** Initial repository scaffolding, Next.js frontend shell, FastAPI health check, and project documentation.
* [x] **Stage 2 (Frontend Shell):** Modular responsive layout, sidebar navigation, dataset explorer, document viewer, and evidence inspection pages.
* [x] **Stage 3 (FastAPI API Layer):** Clean modular routes, Pydantic schemas, domain error handling, and unit test suite.

### Milestone 2: Persistence, Ingestion & Vector Search
* [x] **Stage 4 (PostgreSQL):** Relational schema definition, SQLAlchemy models, Alembic migrations, and Docker Compose orchestration.
* [x] **Stage 5 (PDF Ingestion):** Page-preserving PDF text extraction, typographical cleaning, semantic chunking, and source traceability metadata.
* [x] **Stage 6 (Qdrant & Embeddings):** Vector search service abstraction, dense embedding provider, Qdrant collection indexing, and top-k search.

### Milestone 3: Grounded Intelligence & Trust Layer
* [x] **Stage 7 (RAG Pipeline):** Grounded question answering using Gemini with strict system instructions, citation extraction, and insufficient-evidence handling.
* [x] **Stage 8 (Trust Layer):** Structured evidence inspection exposing source documents, page numbers, text excerpts, and model information without vanity scores.

### Milestone 4: Quantitative Analytics & Query Orchestration
* [x] **Stage 9 (Structured Dataset Ingestion):** Tabular parsing for CSV, XLSX, and JSON with schema detection, inferred SQL types, and null distributions.
* [x] **Stage 10 (DuckDB Analytics):** In-process OLAP SQL analytical engine executing controlled aggregates (count, sum, avg, min, max, group by, order by).
* [x] **Stage 11 (Query Orchestration):** Intent routing classifying user questions into document retrieval, structured analytics, hybrid, or unsupported.
* [x] **Stage 12 (Data Visualization):** Deterministic chart generation (bar, line, pie, table) derived strictly from actual analytical results.

### Milestone 5: Advanced Retrieval, Quality & Security
* [x] **Stage 13 (Hybrid Retrieval):** Combined dense vector search (Qdrant) and lexical keyword search (BM25) with Reciprocal Rank Fusion (RRF).
* [x] **Stage 14 (AI Evaluation):** Automated benchmark framework measuring retrieval precision, citation accuracy, answer correctness, and latency.
* [x] **Stage 15 (Security Hardening):** Defense-in-depth security protecting against oversized uploads, magic byte mismatches, prompt injection, SQL injection, and secret leakage.

### Milestone 6: Scalability, External Feeds & Geospatial
* [x] **Stage 16 (Background Processing):** Asynchronous background job queue for document processing with status tracking (queued, processing, completed, failed).
* [x] **Stage 17 (External Public Data Sources):** Pluggable connector abstraction (`fetch -> validate -> normalize -> record provenance -> store`) for civic open data portals.
* [x] **Stage 18 (Geospatial Capability):** GeoJSON coordinate validation, spatial bounding, and interactive Leaflet vector map viewer.

### Milestone 7: Continuous Integration & Open-Source Readiness
* [x] **Stage 19 (GitHub CI):** GitHub Actions workflow running Ruff linting, 265+ backend unit/integration tests, TypeScript type checks, and Next.js builds on pull requests.
* [x] **Stage 20 (Open-Source Readiness):** Issue templates, pull request template, comprehensive developer guides (local setup, Docker, testing, extension guides), and architectural documentation.

---

## Future Vision (Post-v1.0 Roadmap)

The following capabilities are planned for upcoming releases:

### Milestone 8: Multi-Tenancy & Collaboration [Planned]
* [ ] Multi-tenant workspace segregation with Role-Based Access Control (RBAC).
* [ ] Collaborative citizen annotations and shared research notebooks.
* [ ] Public workspace sharing with view-only permalinks.

### Milestone 9: Real-Time Streaming & Multimodal Ingestion [Planned]
* [ ] Server-Sent Events (SSE) streaming for real-time answer generation.
* [ ] Optical Character Recognition (OCR) pipeline for scanned historical municipal archives.
* [ ] Tabular data extraction directly from PDF reports.

### Milestone 10: Expanded Civic Connectors & Integrations [Planned]
* [ ] Native Socrata Open Data API (SODA) connector.
* [ ] CKAN API connector with automated dataset catalog sync.
* [ ] Eurostat and US Census Bureau statistical API connectors.

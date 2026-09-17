# OpenCitizen AI - Project Roadmap

This roadmap outlines the planned development phases for OpenCitizen AI. In accordance with our core engineering principles, features are built incrementally in small, tested atomic modules.

> **Status Legend:**
> - `[x]` **Completed**
> - `[~]` **In Progress**
> - `[ ]` **Planned**

---

## Milestone 0: Foundation & Environment (Current)
* [x] Define system architecture and tech stack
* [x] Configure repository guidelines (`.gitignore`, licensing, governance, security policies)
* [x] Establish modular directory structure (`frontend/`, `backend/`, `data-pipeline/`, etc.)
* [ ] Setup Docker Compose development environment (PostgreSQL, Qdrant)
* [ ] Setup backend virtual environment and base dependency management (`uv`, `pyproject.toml`)
* [ ] Setup frontend Next.js project structure with TypeScript

---

## Milestone 1: Data Storage & Persistence [Planned]
* [ ] PostgreSQL schema definition and migrations (documents, datasets, user workspaces)
* [ ] Qdrant vector database client connection and collection initialization
* [ ] Basic document ingestion pipeline (PDF parsing, metadata extraction, text chunking)
* [ ] Basic structured data ingestion pipeline (CSV/Parquet ingestion into DuckDB)
* [ ] Automated integration tests for database persistence

---

## Milestone 2: AI Provider & Evidence Grounding [Planned]
* [ ] AI Provider clean abstraction layer (`AIProvider` interface)
* [ ] Gemini API implementation of `AIProvider` (embeddings and reasoning models)
* [ ] Semantic search pipeline retrieving top-k relevant document chunks with exact page citations
* [ ] Mock AI provider implementation for deterministic unit and CI tests
* [ ] Test suite for retrieval precision and citation extraction

---

## Milestone 3: Analytical Engine & Query Orchestration [Planned]
* [ ] DuckDB analytical query execution engine for structured data
* [ ] Safe SQL query generation from natural language questions
* [ ] Dual-retrieval orchestrator combining textual evidence (Qdrant) and quantitative queries (DuckDB)
* [ ] Calculation provenance tracker capturing exact SQL query, execution time, and raw result set
* [ ] Unit and integration tests for analytical queries

---

## Milestone 4: Frontend UI & Interactive Analytics [Planned]
* [ ] Next.js dashboard shell and responsive layout
* [ ] Document and dataset upload interface with ingestion progress tracking
* [ ] Evidence-grounded chat and question-answering interface
* [ ] Dynamic data visualization components using Recharts
* [ ] Inspectable "Source & Calculation" drawer showing exact citation text and SQL calculations

---

## Milestone 5: Verification, Auditability & Polish [Planned]
* [ ] End-to-end integration test suite
* [ ] Export audit reports (PDF/JSON summaries of findings with full source citations)
* [ ] Performance benchmarking (query latency, embedding generation speed)
* [ ] Production deployment documentation and security hardening

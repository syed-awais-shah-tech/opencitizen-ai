# OpenCitizen AI - System Architecture

OpenCitizen AI is designed as a modular, evidence-grounded civic intelligence platform. Its mission is enabling citizens, analysts, and public-interest researchers to question public policy documents and civic tabular datasets with absolute transparency—allowing users to audit the exact citations, source excerpts, and mathematical calculations behind every answer.

---

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Client Layer [Next.js & TypeScript Frontend]
        Dashboard["Citizen Dashboard (/)"]
        DocPage["Document Viewer (/documents)"]
        DataPage["Dataset Explorer (/datasets)"]
        QueryPage["Evidence Q&A (/query)"]
        EvidenceDrawer["Citation & Trust Inspector (/evidence)"]
        MapViewer["Geospatial Map Viewer (Leaflet)"]
        Charts["Dynamic Visualizations (Recharts)"]
    end

    subgraph API & Security Layer [FastAPI Gateway]
        API["REST Gateway (/api/v1)"]
        SecurityGuard["Security Validator & Sanitizer"]
        Queue["Background Ingestion Queue"]
    end

    subgraph Intelligence & Orchestration Layer
        Orchestrator["Controlled Query Orchestrator"]
        AI_Provider["AI Provider Abstraction (Gemini / Mock)"]
        Embed_Provider["Embedding Provider (Gemini / Mock)"]
        Evaluator["Evaluation Benchmark Suite"]
    end

    subgraph Analytical & Spatial Processing Layer
        DuckDB_Engine["DuckDB Engine (In-Process SQL)"]
        SQL_Validator["SQL Whitelist & Compiler"]
        Geo_Engine["Geospatial Processing & GeoJSON"]
    end

    subgraph Storage & Retrieval Layer
        BM25_Index["BM25 Lexical Inverted Index"]
        Qdrant_Store["Qdrant Vector Database"]
        RRF_Reranker["Reciprocal Rank Fusion Reranker"]
        Postgres["PostgreSQL 16 (App Metadata DB)"]
        Storage["storage/ (PDFs, Datasets, Previews)"]
    end

    Client Layer --> API
    API --> SecurityGuard
    SecurityGuard --> Orchestrator
    SecurityGuard --> Queue

    Orchestrator --> SQL_Validator
    SQL_Validator --> DuckDB_Engine
    DuckDB_Engine --> Geo_Engine

    Orchestrator --> RRF_Reranker
    RRF_Reranker --> BM25_Index
    RRF_Reranker --> Qdrant_Store

    Orchestrator --> AI_Provider
    AI_Provider --> Client Layer

    Queue --> Storage
    Queue --> Embed_Provider
    Queue --> Qdrant_Store
    Queue --> BM25_Index
    Queue --> Postgres

    API --> Postgres
    API --> Storage
```

---

## 2. Core Architectural Invariants

### 2.1 Evidence Grounding Before Generation
Answers are never synthesized purely from LLM parametric memory. Every factual claim must be backed by a verified document passage (via Qdrant + BM25) or a computed analytical result (via DuckDB). If evidence is insufficient, the system explicitly returns `INSUFFICIENT_EVIDENCE_PHRASE`.

### 2.2 Dual-Path Retrieval & Analysis
* **Unstructured Documents (PDFs, Municipal Budgets, Reports):** Chunked, embedded into Qdrant, and indexed into BM25 for hybrid search with exact page-level citations.
* **Structured Data (CSVs, XLSX, JSON, Parquet):** Registered with DuckDB for exact SQL execution (counts, sums, averages, groupings, orderings) to prevent mathematical hallucinations.

### 2.3 Controlled Orchestration (Zero Arbitrary SQL)
A natural language question is never converted into arbitrary, model-generated SQL executed directly against a database. Execution flows through:
`Question -> Intent Classifier -> Validated Query Plan -> Parameterized SQL Compiler -> QueryValidator -> DuckDB Engine`.

### 2.4 Defense-in-Depth Security
All inputs pass through:
- File upload streaming chunk limits (max 25 MB) and magic byte verification.
- Entity identifier regex filtering (`^[a-zA-Z0-9_-]{1,64}$`).
- Prompt injection and delimiter sanitization.
- Automated secret scrubbing before logging or error responses.

---

## 3. Subsystem Breakdown

### 3.1 Client Layer (`frontend/`)
Built with **Next.js 15**, **React**, and **TypeScript**:
- **Modular Components**: `DatasetViewer`, `DocumentViewer`, `GeospatialMapViewer`, `ProvenanceViewer`, `ChartRenderer`.
- **Zero Inline State Duplication**: Communicates with the FastAPI backend via structured API services in `frontend/app/services/`.
- **Responsive Layout**: Sidebar navigation and accessible dashboard views for mobile and desktop screens.

### 3.2 API Gateway & Security Layer (`backend/app/api/`, `backend/app/core/`)
- **FastAPI**: Asynchronous routing with Pydantic v2 schemas for request validation and response serialization.
- **Domain Error Handling**: Centralized exception mapping returning consistent, sanitized JSON payloads without leaking internal paths or stack traces.
- **Security Audit Layer**: Enforces upload limits, filename sanitization, SQL keyword blacklisting, and secret redaction.

### 3.3 Query Orchestration & AI Grounding (`backend/app/orchestration/`, `backend/app/ai/`)
- **Intent Classifier**: Classifies queries into `DOCUMENT_SEARCH`, `DATA_ANALYSIS`, `HYBRID`, or `UNSUPPORTED`.
- **Provider Abstraction (`BaseAIProvider`)**: Shields business logic from vendor SDKs. Includes `GeminiProvider` (production) and `MockAIProvider` (deterministic offline testing).
- **System Prompts (`OPENCITIZEN_SYSTEM_INSTRUCTION`)**: Strictly instructs models to cite evidence and disallow ungrounded claims.

### 3.4 Hybrid Document Retrieval (`backend/app/search/`)
- **Dense Vector Search**: Qdrant vector database (`QdrantVectorStore`) indexing 768-dimensional text embeddings.
- **Lexical Keyword Search**: In-memory BM25 inverted index (`BM25Index`) for exact term matching.
- **Reciprocal Rank Fusion**: Merges candidates using $RRF(d) = \sum \frac{1}{60 + rank(d)}$, ensuring balanced precision across dense and sparse methods.

### 3.5 Analytical Engine & Geospatial Layer (`backend/app/analytics/`, `backend/app/geospatial/`)
- **DuckDB**: In-process columnar OLAP database executing read-only SQL queries over registered tables.
- **Geospatial Module**: Identifies geographic columns, validates GeoJSON geometry objects, computes bounding boxes, and generates standard GeoJSON feature collections for vector mapping.

### 3.6 Background Job Processing (`backend/app/jobs/`)
- Asynchronous document processing queue (`JobQueue`) managing extraction, chunking, embedding, and vector storage without blocking client HTTP requests.

### 3.7 Public Data Connectors (`backend/app/connectors/`)
- Standardized 5-step pipeline: `fetch -> validate -> normalize -> record provenance -> store`.
- Every dataset permanently tracks source URL, publisher name, retrieval date, original format, and SHA-256 content checksum.

---

## 4. Extension & Contributor Guides

To extend or customize specific parts of OpenCitizen AI, refer to our dedicated guides:
- [Adding External Connectors](docs/extending-connectors.md)
- [Adding AI & Embedding Providers](docs/extending-ai-providers.md)
- [Customizing Retrieval Strategies](docs/extending-retrieval-strategies.md)
- [Geospatial Architecture Guide](docs/geospatial-architecture.md)
- [Benchmark Evaluation Guide](docs/evaluation-framework.md)

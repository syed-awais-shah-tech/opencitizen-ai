# OpenCitizen AI - API Specification

**Stage:** Stage 1 (Foundation)  
**Version:** 0.1.0  
**Protocol:** REST / JSON  

---

## Base URLs

* **Local Development Backend:** `http://localhost:8000`
* **API Version 1 Prefix:** `/api/v1`

---

## Core Endpoints

### 1. Root Service Discovery

* **Endpoint:** `GET /`
* **Description:** Returns service identification and documentation discovery URLs.
* **Response (200 OK):**
  ```json
  {
    "message": "Welcome to OpenCitizen AI API",
    "version": "0.1.0",
    "docs_url": "/docs",
    "health_url": "/health"
  }
  ```

---

### 2. Service Health Check

* **Endpoint:** `GET /health` (also aliased at `GET /api/v1/health`)
* **Description:** Returns the operational health status and environment metadata of the backend service.
* **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "service": "OpenCitizen AI API",
    "version": "0.1.0",
    "environment": "development"
  }
  ```

---

## Planned Endpoints (Milestones 1–4)

| Method | Endpoint | Milestone | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Milestone 1 | Upload PDF document for text extraction and vector indexing. |
| `GET` | `/api/v1/documents` | Milestone 1 | List indexed documents and metadata. |
| `POST` | `/api/v1/datasets/upload` | Milestone 1 | Upload CSV/XLSX tabular dataset for DuckDB registration. |
| `GET` | `/api/v1/datasets` | Milestone 1 | List registered datasets and schema details. |
| `POST` | `/api/v1/connectors/ingest` | Stage 17 | Import public external dataset via connector with provenance. |
| `GET` | `/api/v1/geospatial/{dataset_id}/geojson` | Stage 18 | Retrieve RFC 7946 GeoJSON FeatureCollection with spatial bbox filtering. |
| `GET` | `/api/v1/geospatial/{dataset_id}/metadata` | Stage 18 | Retrieve geographic CRS, extent bbox, and spatial column mappings. |
| `POST` | `/api/v1/geospatial/validate` | Stage 18 | Validate geographic coordinates or GeoJSON schema conformity. |
| `POST` | `/api/v1/query` | Milestone 2–3 | Evidence-grounded natural language query orchestrator. |
| `GET` | `/api/v1/trace/{query_id}` | Milestone 3 | Inspect citation excerpts and DuckDB SQL calculation trace. |


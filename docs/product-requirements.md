# OpenCitizen AI - Product Requirements Document (PRD)

**Document Version:** 1.0.0  
**Phase:** Stage 0 (MVP Product Specification)  
**Status:** Approved Specification  
**Target Delivery:** Milestone 0 to Milestone 4  

---

## 1. Executive Summary & Product Vision

**OpenCitizen AI** is an open-source, evidence-grounded intelligence platform designed for citizens, journalists, civic researchers, and policy analysts. Public records, municipal budgets, legislative minutes, and civic datasets are often scattered across dense PDF reports and unindexed spreadsheets. Existing generic LLM chat tools produce hallucinated numbers, provide vague answers, and lack verifiable references.

OpenCitizen AI solves this through a dual-path retrieval and verification architecture:
1. **Unstructured Documents (PDFs):** Ingested, chunked, and indexed with page-level semantic search.
2. **Structured Datasets (CSV/XLSX):** Ingested and executed against an analytical SQL engine (DuckDB) to guarantee mathematical accuracy.
3. **Inspectable Provenance:** Every response provides a transparent inspection panel displaying exact document citations (with page numbers) or the executed SQL query and raw computation table.

---

## 2. Target User Personas

| Persona | Role & Context | Primary Need |
| :--- | :--- | :--- |
| **Civic Researcher / Journalist** | Investigating municipal spending, environmental reports, or public policy decisions. | Fast cross-referencing between policy claims in PDFs and actual expenditures in spreadsheets, backed by airtight citations. |
| **Engaged Citizen / Community Advocate** | Seeking clarity on local government programs, zoning proposals, and neighborhood budget allocations. | Plain-language questions answered accurately with charts and visible proof without needing data science skills. |
| **Policy Analyst / Public Servant** | Drafting briefs, auditing compliance documents, or comparing historical civic datasets. | Repeatable, deterministic queries and audit trails that can be verified and shared with stakeholders. |

---

## 3. MVP Scope & Core Capabilities

The MVP is organized strictly around ten functional capabilities:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        OpenCitizen AI MVP Core                         │
├──────────────────────────────────┬─────────────────────────────────────┤
│      Document Ingestion & RAG    │      Structured Data & Analytics    │
│  1. Upload PDF documents         │  2. Upload CSV/XLSX datasets        │
│  3. Process documents            │  6. Analytical queries via DuckDB   │
│  4. Semantic retrieval (Qdrant)  │  7. Dynamic charts (Recharts)       │
│  5. Grounded Q&A                 │ 10. Transparent calculation trace   │
├──────────────────────────────────┴─────────────────────────────────────┤
│                         Auditability & Provenance                      │
│  8. Source citations with page-level precision                         │
│  9. Inspectable evidence used to produce an answer                     │
└────────────────────────────────────────────────────────────────────────┘
```

### Capability Details & Functional Requirements

#### FR-1: Upload PDF Documents
* **Description:** The system must accept user uploads of digital PDF files via drag-and-drop or file selector.
* **Specifications:**
  * Support single and multi-file uploads.
  * Maximum file size: 50 MB per document for MVP.
  * MIME type validation: `application/pdf`.
  * Document deduplication via cryptographic hash (`SHA-256`).
  * Capture metadata: file name, file size, page count, and upload timestamp.

#### FR-2: Upload CSV/XLSX Datasets
* **Description:** The system must accept user uploads of tabular datasets in CSV and XLSX (Excel) formats.
* **Specifications:**
  * Maximum file size: 100 MB per dataset for MVP.
  * File format validation: comma/semicolon/tab delimited CSV and single/multi-sheet XLSX.
  * Auto-detect header row, column count, row count, and initial data types (string, integer, float, date/timestamp, boolean).
  * Register dataset metadata in PostgreSQL and prepare tables for in-memory or persisted DuckDB queries.

#### FR-3: Process Documents
* **Description:** An automated ingestion pipeline must extract text and structure from PDFs and prepare it for semantic search.
* **Specifications:**
  * Extract text page-by-page, strictly preserving page number mappings (`page_number`).
  * Chunking strategy: Recursive character or semantic sentence splitting (target chunk size: 500–800 tokens, 100-token overlap).
  * Metadata preservation per chunk: `document_id`, `document_title`, `page_number`, `chunk_id`, and `character_offsets`.
  * Status lifecycle: `PENDING` -> `PROCESSING` -> `INDEXED` / `FAILED` with descriptive error logs.

#### FR-4: Perform Semantic Retrieval
* **Description:** The system must vectorize document chunks and execute similarity queries to retrieve the most relevant passages for a user's question.
* **Specifications:**
  * Embedding generation using Gemini API embedding models via the `AIProvider` abstraction layer.
  * Vector storage and similarity indexing in Qdrant.
  * Configurable top-k retrieval (default: top 5 chunks with similarity threshold filtering).
  * Retrieved chunks include original text snippets, similarity score, document ID, and page number.

#### FR-5: Ask Questions About Uploaded Information
* **Description:** Users can ask free-form questions in natural language through a conversational UI.
* **Specifications:**
  * Query routing: determine whether the prompt targets unstructured document text, structured tabular data, or both (hybrid).
  * System prompt enforcement: The model is instructed never to hallucinate or guess; if information is absent from uploaded data, it must explicitly decline to answer.
  * Streaming response delivery to the frontend via WebSockets or Server-Sent Events (SSE).

#### FR-6: Perform Analytical Queries Against Structured Datasets
* **Description:** The system must translate natural language queries targeting tabular data into safe, read-only SQL queries executed by DuckDB.
* **Specifications:**
  * Query translation: Schema-aware LLM prompt converts user intent into valid DuckDB SQL (`SELECT` statements).
  * Safety Sandbox: Strict read-only enforcement. Rejection of any modifying or destructive keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `ATTACH`, `COPY`, `PRAGMA`).
  * Execution against DuckDB: aggregations (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`), grouping, filtering, and sorting.
  * Error recovery: if a query fails execution, the error is fed back to the planner or surfaced gracefully to the user.

#### FR-7: Generate Charts from Actual Analytical Results
* **Description:** When a query yields quantitative, multi-row, or categorical data, the system must generate interactive visualizations rendered dynamically in the UI.
* **Specifications:**
  * Chart types supported in MVP: Bar Chart (categorical comparisons), Line Chart (time-series trends), and Area/Pie Chart (proportions).
  * Chart rendering engine: Recharts (React component library).
  * Visual data integrity: Chart data points must be strictly bound to actual DuckDB query results—never estimated or invented.
  * Chart features: Interactive tooltips, responsive container, labeled axes, and legend.

#### FR-8: Show Source Citations
* **Description:** Every answer grounded in document text must display interactive, in-text citation badges pointing to specific source documents and page numbers.
* **Specifications:**
  * Citation format: In-text clickable pills (e.g., `[City Budget 2024, p. 12]`).
  * Hover preview: Quick tooltip displaying document title and page number.
  * Click behavior: Opens the dedicated Evidence Drawer scrolled to the specific referenced passage.

#### FR-9: Show Evidence Used to Produce an Answer
* **Description:** Users must have complete access to an inspectable "Evidence Drawer" showing the exact text chunks used to generate the answer.
* **Specifications:**
  * Displays source document name, page number, and similarity score.
  * Full text of the retrieved chunk highlighted in context.
  * Indication of chunk relevance and token count.

#### FR-10: Show Calculations When Answer Depends on Data Analysis
* **Description:** Any response that provides numbers or answers computed from structured datasets must expose the complete analytical lineage.
* **Specifications:**
  * Transparent display of the exact DuckDB SQL query generated and executed.
  * Tabular preview of the raw result set returned by DuckDB before LLM synthesis.
  * Query metadata: execution duration (milliseconds), rows scanned, and table references.
  * Step-by-step arithmetic derivation connecting raw table rows to the figures quoted in the response.

---

## 4. Data Architecture & Entities

```
┌─────────────────────────┐           ┌─────────────────────────┐
│        Workspace        │1       *  │        Document         │
│  id, name, created_at   ├───────────►  id, title, file_path,  │
└────────────┬────────────┘           │  file_hash, page_count  │
             │                        └────────────┬────────────┘
             │1                                    │1
             │                                     │*
             │*                       ┌────────────▼────────────┐
┌────────────▼────────────┐           │      DocumentChunk      │
│         Dataset         │           │  id, chunk_index, page, │
│  id, name, file_path,   │           │  text_content, vector_id│
│  row_count, table_name  │           └─────────────────────────┘
└────────────┬────────────┘
             │1
             │*
┌────────────▼────────────┐
│      DatasetColumn      │
│  id, column_name, type  │
└─────────────────────────┘
```

* **Workspace:** Logical container for a user's session, uploaded documents, datasets, and queries.
* **Document:** Metadata record for an uploaded PDF file.
* **DocumentChunk:** Segment of document text associated with a specific page number, embedded in Qdrant.
* **Dataset:** Metadata record for an uploaded CSV/XLSX file, mapped to a DuckDB table.
* **DatasetColumn:** Schema definition of columns and inferred types for structured queries.
* **QuerySession / Message:** Thread of user questions, assistant responses, citation lists, and calculation traces.

---

## 5. Non-Functional Requirements (NFRs)

* **NFR-1 (Evidence Grounding):** Responses must never synthesize unsupported factual claims. If retrieved context has a low similarity score (< threshold) or analytical query returns empty sets, the system must clearly state lack of evidence.
* **NFR-2 (Query Performance):**
  * Document chunk retrieval: < 300 ms for top-5 chunks.
  * Analytical SQL execution: < 500 ms for datasets up to 100,000 rows in DuckDB.
  * Time-to-First-Token (TTFT) for LLM answers: < 1.5 s.
* **NFR-3 (Data Security & Isolation):** All SQL queries generated by LLMs are sanitized and executed strictly in read-only mode.
* **NFR-4 (Explainability & Auditability):** 100% of generated numerical answers and text claims must carry either a source citation or a calculation trace.
* **NFR-5 (Usability):** Clean, responsive Next.js frontend with dark/light theme support, accessible according to WCAG 2.1 AA standards.
* **NFR-6 (Testability):** Complete separation of AI logic behind an `AIProvider` interface enabling deterministic mock testing in CI/CD without live API keys.

---

## 6. Acceptance Criteria

| ID | Capability | Validation Criteria |
| :--- | :--- | :--- |
| **AC-1** | PDF Upload | Valid PDF files are accepted, parsed, and assigned unique document IDs with page counts recorded. |
| **AC-2** | CSV/XLSX Upload | Datasets are parsed, schemas detected, and registered as queryable DuckDB tables. |
| **AC-3** | Ingestion & Chunking | Document chunks retain correct page numbers and are indexed into Qdrant. |
| **AC-4** | Semantic Search | Querying returns top-k chunks with page numbers and relevance scores. |
| **AC-5** | Grounded Q&A | Answering a policy question quotes document context with inline citation pills. |
| **AC-6** | SQL Analytics | Asking "What was the total spending in 2023?" produces a valid `SUM()` SQL query executed in DuckDB. |
| **AC-7** | Recharts Visualization | Analytical breakdown outputs dynamic Bar/Line/Pie charts linked directly to query data. |
| **AC-8** | Source Citations | Clicking a citation pill opens the Evidence Drawer to the cited page. |
| **AC-9** | Evidence Drawer | Evidence drawer displays the exact chunk text, page number, and similarity score. |
| **AC-10** | Calculation Inspector | Calculation inspector shows the exact DuckDB SQL query, execution time, and raw output table. |

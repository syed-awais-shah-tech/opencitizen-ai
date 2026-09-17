# OpenCitizen AI - User Flows & Interaction Workflows

**Document Version:** 1.0.0  
**Phase:** Stage 0 (MVP Product Specification)  
**Status:** Approved Specification  
**Related Documents:** [Product Requirements](product-requirements.md) | [Non-Goals](non-goals.md)  

---

## Overview

This document specifies the primary end-to-end user journeys for the OpenCitizen AI MVP. Each flow is designed to prioritize **evidence grounding, transparency, and auditability**, ensuring users can trace every insight back to an original PDF page or a verifiable SQL calculation.

---

## Flow 1: Uploading & Ingesting Civic Documents (PDF)

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant API as FastAPI Backend
    participant Pipe as Ingestion Pipeline
    participant VecDB as Qdrant Vector DB
    participant DB as PostgreSQL Metadata

    User->>UI: Drag & drop PDF (e.g., "City_Budget_2024.pdf")
    UI->>API: POST /api/v1/documents/upload (multipart/form-data)
    API->>API: Validate file type (PDF), size (<50MB), compute SHA-256
    API->>DB: Record Document (status=PENDING, filename, hash)
    API-->>UI: 202 Accepted (document_id, status=PROCESSING)
    
    API->>Pipe: Trigger background document processing
    Pipe->>Pipe: Extract text page-by-page (preserve page_number)
    Pipe->>Pipe: Chunk text (500-800 tokens, 100-token overlap)
    Pipe->>API: Generate embeddings via AIProvider (Gemini)
    Pipe->>VecDB: Upsert chunks with payload (doc_id, page_no, chunk_text)
    Pipe->>DB: Update Document (status=READY, page_count, chunk_count)
    
    UI->>API: Poll status or receive SSE event (document:ready)
    UI-->>User: Display "City_Budget_2024.pdf (Ready, 84 pages, 210 chunks)"
```

### Steps & Edge Cases
1. **User Action:** The user accesses the Document Library tab and uploads a PDF file (e.g., city budget or policy report).
2. **Validation:** System checks file format and file size.
   * *Edge Case (Invalid File):* If a non-PDF or corrupted file is uploaded, the UI presents an immediate error: *"Invalid file type: Only standard PDF documents are supported in MVP."*
3. **Processing Feedback:** A progress indicator displays current stage (`Uploading` -> `Extracting Pages` -> `Indexing Chunks` -> `Ready`).
4. **Completion:** The document card appears in the workspace with metadata: title, page count, and chunk count.

---

## Flow 2: Uploading & Registering Tabular Datasets (CSV / XLSX)

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant API as FastAPI Backend
    participant Engine as DuckDB Analytical Engine
    participant DB as PostgreSQL Metadata

    User->>UI: Select CSV or XLSX (e.g., "dept_expenses_2023.csv")
    UI->>API: POST /api/v1/datasets/upload
    API->>API: Validate format, detect encoding and delimiter
    API->>Engine: Ingest dataset & infer schema (columns, types, row count)
    API->>DB: Store Dataset metadata (table_name, columns, row_count)
    API-->>UI: 201 Created (dataset_id, schema preview, row_count)
    UI-->>User: Display Schema Preview (Columns, Data Types, First 5 rows)
```

### Steps & Edge Cases
1. **User Action:** The user uploads a tabular dataset (CSV or XLSX) containing civic data (e.g., department expenditures, vendor contracts, or census tables).
2. **Schema Ingestion:** DuckDB parses the file, assigns column types (INTEGER, DOUBLE, VARCHAR, DATE), and creates an in-memory/persisted table.
3. **User Inspection:** UI displays a schema preview modal showing detected columns, inferred types, and a preview of the first 5 rows.
4. **User Confirmation:** The user confirms the dataset, enabling it for natural language analytical queries.
   * *Edge Case (Malformed Dataset):* If a CSV has inconsistent delimiters or unparseable rows, the system rejects it with line-number error details.

---

## Flow 3: Document Question-Answering with Page Citations & Evidence Drawer

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant API as FastAPI Gateway
    participant Router as Query Orchestrator
    participant VecDB as Qdrant Vector DB
    participant AI as AI Provider (Gemini)

    User->>UI: Asks: "What are the key priorities outlined in the 2024 Transportation Plan?"
    UI->>API: POST /api/v1/query (workspace_id, prompt)
    API->>Router: Route query -> Document Q&A mode
    Router->>AI: Generate query embedding
    Router->>VecDB: Search top-5 chunks (doc_id filter, cosine threshold)
    VecDB-->>Router: Return 5 chunks (text, page_number, similarity_score)
    Router->>AI: Synthesize answer with strict grounding prompt + chunks
    AI-->>Router: Response text with citation tags [Doc: City_Plan, Page: 14]
    Router-->>UI: Stream response to client
    UI-->>User: Render answer with clickable citation pills: [City Plan, p. 14]
    
    User->>UI: Clicks citation pill "[City Plan, p. 14]"
    UI->>UI: Slide out Evidence Drawer
    UI-->>User: Display exact excerpt, page 14, relevance score (0.88), document title
```

### Steps & Edge Cases
1. **User Action:** User enters a natural language query in the chat input.
2. **Retrieval:** Semantic search identifies the top relevant document chunks with page numbers.
3. **Grounded Generation:** The LLM receives the chunks as system context. It is strictly constrained to only state facts present in the text and must attribute claims to specific pages.
4. **Citation Interaction:** Citations are rendered as interactive pills. Clicking a pill opens the **Evidence Drawer**, allowing the user to audit the exact text passage that generated the sentence.
   * *Edge Case (No Supporting Evidence):* If no chunks exceed the similarity threshold, the model answers: *"No relevant information was found in the uploaded documents to answer this question."*

---

## Flow 4: Quantitative Question-Answering & Calculation Inspector

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant Router as Query Orchestrator
    participant AI as AI Provider (Gemini)
    participant DuckDB as DuckDB Analytical Engine

    User->>UI: Asks: "What was the total expenditure for Parks & Rec in 2023?"
    UI->>Router: POST /api/v1/query
    Router->>Router: Classify intent -> Structured Data Analytics
    Router->>AI: Prompt with dataset schema to generate read-only SQL
    AI-->>Router: SELECT SUM(amount) FROM expenses WHERE dept = 'Parks & Rec' AND year = 2023
    Router->>Router: Validate SQL safety sandbox (SELECT only, no DDL/DML)
    Router->>DuckDB: Execute query
    DuckDB-->>Router: Result: [{"total_amount": 4250000.00}], execution_time: 24ms
    Router->>AI: Format result into conversational answer with lineage
    Router-->>UI: Return answer + calculation_trace payload
    UI-->>User: "The total expenditure for Parks & Rec in 2023 was $4,250,000. [Inspect Calculation]"
    
    User->>UI: Clicks "[Inspect Calculation]"
    UI->>UI: Slide out Calculation Drawer
    UI-->>User: Show SQL query, execution time (24ms), raw table output, and derivation
```

### Steps & Edge Cases
1. **User Action:** User asks a computational or aggregation question against structured datasets.
2. **SQL Generation:** The AI Provider produces a sanitized DuckDB SQL query based on the active table schema.
3. **Execution & Trace:** DuckDB runs the query directly against the tabular data. The system records:
   * The exact SQL statement.
   * Execution time in milliseconds.
   * The raw tabular result set.
4. **Transparent Inspection:** The user clicks the **"Inspect Calculation"** button to view the SQL query and raw result table, verifying that the number was not invented by the language model.
   * *Edge Case (Invalid Query / Unsafe SQL):* If the generated SQL contains disallowed commands (`DROP`, `UPDATE`, `INSERT`), the query is blocked by the safety sandbox and an error is logged.

---

## Flow 5: Analytical Chart Generation & Dynamic Visualization

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant API as FastAPI Backend
    participant Engine as DuckDB Analytical Engine
    participant Chart as Recharts Renderer (Frontend)

    User->>UI: Asks: "Show me a chart of municipal spending by category for 2023."
    UI->>API: POST /api/v1/query
    API->>API: Generate SQL: SELECT category, SUM(amount) AS total FROM expenses GROUP BY category ORDER BY total DESC
    API->>Engine: Execute SQL
    Engine-->>API: Tabular rows: [{category: 'Public Safety', total: 12000000}, ...]
    API-->>UI: Response payload with chart_type="bar", data=[...], x_key="category", y_key="total"
    UI->>Chart: Mount Recharts <ResponsiveContainer><BarChart ... /></ResponsiveContainer>
    UI-->>User: Interactive Bar Chart with tooltips, legend, and "View Source SQL" button
```

### Steps & Edge Cases
1. **User Action:** The user asks for a visual summary, comparison, or trend across data columns.
2. **Query & Shape Detection:** The analytical engine executes the query and identifies the appropriate chart format:
   * **Bar Chart:** Categorical comparisons (e.g., department budgets, project spending).
   * **Line Chart:** Sequential / time-series data (e.g., monthly spending, annual trends).
   * **Pie / Donut Chart:** Proportions of a whole (limited to <= 7 categories).
3. **Interactive Rendering:** The frontend renders a dynamic Recharts component inside the chat stream.
4. **Data Verification:** Hovering over bars or lines displays exact numerical tooltips. Users can toggle series visibility or click "View Data Table" to inspect the exact rows powering the visual.

---

## Flow 6: Hybrid Query (Cross-Modal Document & Dataset Verification)

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant Router as Dual-Retrieval Orchestrator
    participant VecDB as Qdrant Vector DB
    participant Engine as DuckDB Analytical Engine
    participant AI as AI Provider (Gemini)

    User->>UI: "Did 2023 road maintenance spending comply with the cap in the 2023 Policy Brief?"
    UI->>Router: POST /api/v1/query
    Router->>Router: Detect Hybrid Intent (requires Policy Document + Expense Dataset)
    par Document Retrieval
        Router->>VecDB: Retrieve chunks for "road maintenance spending cap"
        VecDB-->>Router: Text: "Road maintenance cap is $1.5M" (Page 8)
    and Structured Analytics
        Router->>Engine: Run SQL: SELECT SUM(amount) FROM expenses WHERE item = 'Road Maintenance'
        Engine-->>Router: Result: $1.82M
    end
    Router->>AI: Synthesize response with both evidence chunks and computed SQL result
    Router-->>UI: Return unified response with citation pill [Policy Brief, p. 8] and [Inspect SQL]
    UI-->>User: "No. The 2023 Policy Brief established a cap of $1.5M [Policy Brief, p. 8], but actual expenditures totaled $1,820,000 [Inspect SQL], exceeding the limit by $320,000."
```

### Steps & Edge Cases
1. **User Action:** User asks a complex question connecting a policy statement in a PDF to real numbers in a spreadsheet.
2. **Dual Retrieval:** The orchestrator dispatches parallel queries:
   * Semantic search in Qdrant locates the policy rule and page number.
   * Analytical SQL in DuckDB computes the actual spending.
3. **Unified Synthesis:** The AI model combines the two grounded outputs into a clear comparative summary.
4. **Dual Provenance:** The response contains both an interactive document citation pill and a calculation inspection button.

---

## Flow 7: Handling Ambiguous Queries & Low Evidence

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Researcher
    participant UI as Next.js Frontend
    participant Router as Query Orchestrator
    participant VecDB as Qdrant Vector DB

    User->>UI: "What is the projected budget for the year 2035?"
    UI->>Router: POST /api/v1/query
    Router->>VecDB: Search chunks for "2035 projected budget"
    VecDB-->>Router: Top similarity score = 0.32 (below threshold 0.65)
    Router-->>UI: Return low-confidence decline message
    UI-->>User: "I could not find any evidence regarding a 2035 projected budget in the uploaded documents. The documents only cover fiscal years 2022 through 2025. Please upload the relevant forward-looking forecast or refine your question."
```

### Steps & Edge Cases
1. **User Action:** User asks a question not covered by the current documents or datasets.
2. **Threshold Verification:** The similarity search returns results below the acceptable confidence threshold.
3. **Transparent Decline:** Rather than inventing an answer or speculating, the system politely and clearly declines, stating the boundaries of the available documents and suggesting next steps.

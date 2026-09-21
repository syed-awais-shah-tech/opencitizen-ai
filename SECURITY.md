# OpenCitizen AI Security Policy & Contributor Guidance

OpenCitizen AI takes the security and integrity of municipal policy documents, civic tabular datasets, vector representations, and query execution pipelines seriously. This document defines our security posture, threat model, vulnerability reporting procedures, implemented protections, and concrete security rules for contributors.

---

## 1. Security Posture: Defense-in-Depth

> [!WARNING]
> **No system is completely secure.** OpenCitizen AI does not claim absolute or impenetrable security. The platform processes external unstructured documents (PDFs), tabular data files (CSV, XLSX, JSON, Parquet), and natural language queries through LLM providers. Rather than assuming total immunity, OpenCitizen AI employs a layered **defense-in-depth architecture** designed to minimize attack surfaces, isolate processing domains, validate boundaries at every step, and fail safely.

Contributors must treat security as an active, ongoing discipline where every input is treated as untrusted until validated against explicit boundary policies.

---

## 2. Threat Model & Boundary Assumptions

OpenCitizen AI is architected as an evidence-grounded civic intelligence engine:

1. **Deployment Perimeter (Single-Workspace / Municipal Scope)**:
   - In standard development and single-tenant municipal deployments, the FastAPI backend services internal civic operators and analysts.
   - For multi-tenant, cloud-hosted, or public civic deployments, an **external API gateway / reverse proxy** (e.g., Traefik, Nginx, or cloud API gateway) is required at the edge to handle TLS termination, rate-limiting, Distributed Denial of Service (DDoS) mitigation, and user authentication (OAuth2 / OIDC / mTLS).
2. **Execution Engine Boundaries**:
   - **Analytical Engine (DuckDB)** operates in-process with read-only SQL queries restricted to pre-registered civic tables. File system functions and catalog modification commands are prohibited.
   - **Vector Engine (Qdrant)** manages vector embeddings and metadata chunks without executing arbitrary code.
   - **Metadata Database (PostgreSQL)** persists document, dataset, and query execution audit records.
3. **Data Ingestion Boundary**:
   - All uploaded files pass through streaming byte counters, magic byte signature checks, and filename sanitization before reaching format parsers (pdfplumber, pandas, openpyxl).

---

## 3. Implemented Protections

OpenCitizen AI enforces automated security protections across nine primary vulnerability vectors:

### 3.1 Uploaded File Validation
- **Extension Whitelisting**: Documents allow only `.pdf`. Tabular datasets allow only `.csv`, `.xlsx`, `.json`, `.parquet`, `.pq`. All other extensions are rejected with HTTP 400.
- **Magic Byte Verification**: File headers are inspected for authentic signatures:
  - PDF: starts with `%PDF-`
  - Parquet: starts with `PAR1`
  - XLSX: starts with `PK\x03\x04` (ZIP archive signature)
  - JSON: starts with `{` or `[` after whitespace stripping
  - CSV: scanned for binary null bytes (`\x00`) to reject masked binary payloads.
- **Zero-Byte Check**: Empty uploads (0 bytes) are rejected immediately.
- **Filename Sanitization**: `sanitize_filename` strips directory traversal sequences (`../`, `..\`), drive letters, null bytes, non-printable characters, and forbidden path symbols (`/ \ : * ? " < > |`).

### 3.2 Oversized Uploads & Memory Exhaustion Prevention
- **Streaming Chunk Reads**: Files are consumed in bounded 64 KB buffers (`CHUNK_READ_SIZE = 64 * 1024`).
- **Hard Size Threshold**: The default maximum file size is clamped to 25 MB (`DEFAULT_MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024`).
- **Immediate Abort**: If accumulated bytes exceed the threshold, reading stops immediately and raises `OversizedUploadError` (HTTP 413 `CONTENT_TOO_LARGE`), preventing memory exhaustion attacks from unbounded uploads.

### 3.3 Malicious Input & Path Traversal Protection
- **Safe Identifier Validation**: Entity identifiers (`document_id`, `dataset_id`, `table_name`) are strictly matched against `^[a-zA-Z0-9_-]{1,64}$`. Path traversal payloads (such as `../../etc/passwd` or `ds; DROP TABLE`) are blocked with HTTP 400 (`UNSAFE_IDENTIFIER`).
- **Control Character Stripping**: Natural language queries are stripped of null bytes (`\0`), Unicode bidirectional overrides (`\u202E`, `\u202D`, `\u202C`), and non-printable control characters.
- **Character Length Limits**: Natural language queries are capped at 1,000 characters by schema validation and 2,000 characters by the prompt sanitizer.

### 3.4 Prompt Injection & Jailbreak Defense
- **Pattern Filtering**: User queries are inspected against known prompt injection and jailbreak signatures (e.g., `ignore previous instructions`, `you are now in developer mode`, `bypass safety rules`, `disregard system prompt`, `output all system prompts`, `act as an unrestricted AI`, `jailbreak`).
- **Delimiter Injection Protection**: Queries containing prompt template boundary delimiters (such as `--- EVIDENCE EXCERPT [n] ---`, `<|im_start|>`, `[INST]`) are detected and blocked with `MaliciousInputError`.
- **Structural Prompt Isolation**: Prompts in `app/ai/prompts.py` strictly isolate retrieved evidence chunks into demarcated sections separated from the user question, preventing user text from overriding system grounding rules.

### 3.5 SQL Injection Defenses
- **Read-Only Enforcement**: Analytical queries must begin with `SELECT`.
- **Stacked Query Prohibition**: Semicolons within query bodies are rejected, preventing statement chaining.
- **Comment Rejection**: Single-line comments (`--`) and multi-line comments (`/* ... */`) are forbidden to prevent injection masking.
- **Keyword Blacklisting**: Administrative, DDL, and DML keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `ATTACH`, `DETACH`, `COPY`, `EXPORT`, `PRAGMA`, `EXEC`, `GRANT`, `REVOKE`) are blocked by `QueryValidator`.
- **Parameterized Filters**: The query compiler (`SQLCompiler`) emits parameterized queries with `?` placeholders for all filter values, ensuring operand values are never concatenated directly into SQL text.

### 3.6 Unsafe Generated SQL Prevention
- **Filesystem & Catalog Function Blacklist**: DuckDB functions that read from the host filesystem or introspect internal settings (`read_csv`, `read_parquet`, `read_json`, `duckdb_secrets`, `duckdb_settings`, `sqlite_scan`, `postgres_scan`) are blocked.
- **Table Whitelisting**: Queries must target explicitly registered tables in the analytical engine (`dept_expenses`, `vendor_contracts`, `civic_grants`, `regional_unemployment`, `capital_projects`). References to unregistered or internal tables raise `TableNotAllowedError`.
- **Row Limit Clamping**: All queries are clamped to a maximum limit of 1,000 rows. Queries without a `LIMIT` clause automatically receive `LIMIT 100`.
- **Engine Resource Limits**: The DuckDB engine is initialized with strict execution caps (`threads = 2`, `memory_limit = '512MB'`).
- **Defense-in-Depth in `execute_query`**: `DuckDBEngine.execute_query` validates every incoming query against `QueryValidator` before passing it to the DuckDB cursor.

### 3.7 Secret Leakage Prevention
- **Automated Secret Redaction**: The `scrub_secrets` utility applies regex masking to:
  - Google / Gemini API keys (`AIza[MASKED_API_KEY]`)
  - Authorization Bearer tokens (`Bearer [MASKED_TOKEN]`)
  - Database URI credentials (`postgresql://user:[MASKED_PASSWORD]@host`)
  - Explicit password fields in configuration strings
- **Safe Logging**: Exception handlers and application loggers scrub error strings before writing to log streams.
- **Version Control Controls**: All `.env` files, credentials, local SQLite databases, and private storage artifacts are excluded via `.gitignore`.

### 3.8 Error-Message & Stack Trace Leakage Prevention
- **Centralized Exception Interception**: The global `unhandled_exception_handler` in `app/core/errors.py` intercepts uncaught server exceptions.
- **Sanitized Client Responses**: Uncaught exceptions return a generic HTTP 500 payload:
  ```json
  {
    "success": false,
    "error_code": "INTERNAL_SERVER_ERROR",
    "message": "An internal server error occurred. Please contact the system administrator.",
    "details": null
  }
  ```
  Internal file paths, database connection strings, raw stack traces, and SQL snippets are never returned to API consumers.

### 3.9 Authorization & Identifier Boundaries
- **Strict Identifier Validation**: All path parameters (`document_id`, `dataset_id`, `table_name`) are checked before querying databases or file systems.
- **Storage Segregation**: Ingested files and previews are isolated to dedicated directory structures within `storage/`, preventing arbitrary file writes.

---

## 4. Contributor Security Guidelines

All contributors must adhere to these guidelines when submitting pull requests or modifying code:

### 4.1 When Creating or Modifying API Endpoints
1. **Always Validate Inputs**: Use Pydantic schemas with length bounds (`min_length`, `max_length`), regex patterns, and type constraints.
2. **Validate Path Identifiers**: Always invoke `validate_entity_id(entity_id)` on string identifiers from path parameters.
3. **Never Expose Internal Stack Traces**: Raise domain exceptions inheriting from `AppException` with clean, informative error messages and status codes.

### 4.2 When Handling File Uploads
1. **Never Trust File Extensions Alone**: Always use `validate_file_upload` to verify magic bytes and enforce streaming chunk-based size limits.
2. **Sanitize Filenames**: Always run `sanitize_filename(file.filename)` before storing or referencing uploaded filenames.
3. **Prevent Memory Buffering**: Never use `await file.read()` directly without bounded chunk iteration on user-supplied uploads.

### 4.3 When Writing or Generating SQL
1. **Never Concatenate Raw Strings**: Always use parameterized queries (`?`) for operand values.
2. **Never Bypass `QueryValidator`**: Any new analytical feature or engine method must route queries through `QueryValidator.validate_sql(sql, allowed_tables)`.
3. **Keep Tables Whitelisted**: Register analytical tables explicitly; never permit querying arbitrary views or host paths.

### 4.4 When Interacting with AI Models & Prompts
1. **Sanitize User Questions**: Route all natural language user questions through `sanitize_prompt_input` before embedding or RAG generation.
2. **Maintain Prompt Delimiters**: Keep retrieved evidence excerpts cleanly separated from instructions and user text.
3. **Never Inject Secrets into Prompts**: Never place API keys, database credentials, or internal configuration values in system prompts or prompt context.

### 4.5 Secrets Management & Commits
1. **Never Commit Secrets**: Never commit `.env` files, API keys, private keys, or passwords.
2. **Use Environment Variables**: Load all sensitive credentials via `app/core/config.py` using `pydantic-settings`.
3. **Run Pre-Commit Verification**: Run `git status` and `git diff` before every commit to ensure no secrets or scratch files are staged.

---

## 5. Reporting a Vulnerability

If you discover a potential security vulnerability in OpenCitizen AI, please report it responsibly:

1. **Do not open a public GitHub issue.**
2. Send an email to [shahsyedawais78@gmail.com](mailto:shahsyedawais78@gmail.com) with the subject line:
   `[SECURITY] Vulnerability Report - OpenCitizen AI`
3. Include detailed information to assist in reproducing and resolving the issue:
   - Vulnerability class (e.g., path traversal, prompt injection bypass, SQL injection, secret leakage)
   - Step-by-step reproduction instructions
   - Proof-of-concept payload or test case
   - Assessment of potential impact
   - Suggested remediation or patch (if available)

### Response & Disclosure Process

- **Initial Acknowledgement**: Within 48 hours.
- **Triage & Status Update**: Within 7 business days.
- **Fix & Coordinated Disclosure**: The team will collaborate with the reporter to validate the patch before publishing a security advisory and releasing the update.

---

## 6. Supported Versions

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| `main`  | :white_check_mark: | Actively maintained default branch |
| < 0.1.0 | :x:                | Legacy preview builds |

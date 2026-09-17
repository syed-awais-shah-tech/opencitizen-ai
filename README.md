# OpenCitizen AI

An evidence-grounded, open-source AI platform enabling citizens, researchers, and organizations to upload public/development documents and structured datasets, ask questions, perform verifiable data analysis, generate charts, and inspect the exact sources and calculations behind every answer.

---

> ### ⚠️ Project Status: Foundation & Scaffolding (Active Development)
> OpenCitizen AI is in its initial setup phase. Application code and service modules are being built incrementally in atomic, tested steps. See [ROADMAP.md](ROADMAP.md) for current progress and planned milestones.

---

## Core Principles

1. **Evidence-Grounded Answers:** Hallucinations are mitigated by requiring factual answers to be grounded in retrieved document text or computed datasets.
2. **Transparent Calculations:** Factual mathematical claims are computed directly through an analytical database (DuckDB) rather than generated via LLM arithmetic.
3. **Inspectable Provenance:** Every response provides an inspectable drawer displaying the source document, page number, citation text, or the exact SQL query run.
4. **Open & Modular Architecture:** Built entirely on open-source technologies with clean vendor abstractions.

---

## Planned Capabilities

* [ ] **Public Document Q&A:** Semantic search and question answering across PDFs, municipal budgets, and reports with page-level citations.
* [ ] **Quantitative Data Analysis:** Natural language questioning over tabular civic datasets (CSV, Parquet) converted into safe DuckDB SQL queries.
* [ ] **Interactive Visualizations:** Automated charts and data breakdowns rendered dynamically using Recharts.
* [ ] **Source & Calculation Inspector:** A dedicated inspection panel to audit how any answer or chart was derived.
* [ ] **Self-Hostable Infrastructure:** Standardized multi-container deployment via Docker Compose.

---

## Technology Stack

* **Frontend:** [Next.js](https://nextjs.org/) (React), [TypeScript](https://www.typescriptlang.org/), [Recharts](https://recharts.org/)
* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python), [Pandas](https://pandas.pydata.org/)
* **Analytical Engine:** [DuckDB](https://duckdb.org/)
* **Vector Database:** [Qdrant](https://qdrant.tech/)
* **Application Database:** [PostgreSQL](https://www.postgresql.org/)
* **AI Provider:** [Gemini API](https://ai.google.dev/) via clean abstraction layer
* **Orchestration:** [Docker Compose](https://docs.docker.com/compose/)

---

## Repository Structure

```
opencitizen-ai/
├── frontend/          # Next.js web application (planned)
├── backend/           # FastAPI application and API routes (planned)
├── data-pipeline/     # Ingestion, cleaning, and embedding scripts (planned)
├── docs/              # System documentation and guides
├── tests/             # Cross-service and integration tests
├── scripts/           # Development and database maintenance scripts
├── ARCHITECTURE.md    # System architecture and design specifications
├── ROADMAP.md         # Planned milestones and development progress
├── CONTRIBUTING.md   # Guidelines for contributing and commit conventions
├── CODE_OF_CONDUCT.md# Community standards
├── SECURITY.md        # Security policies and vulnerability reporting
└── LICENSE            # MIT License
```

---

## Getting Started (Prerequisites)

Ensure you have the following tools installed locally:
* **Git** (>= 2.40)
* **GitHub CLI** (`gh`)
* **Node.js** (>= 20 LTS) & **npm**
* **Python** (>= 3.11) & **uv**
* **Docker Desktop** (with Docker Compose)

Detailed setup guides for individual services will be published as each atomic component is introduced.

---

## Contributing

We welcome contributions! Please review our [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting pull requests.

OpenCitizen AI strictly enforces:
* Incremental, reviewable atomic modules
* Strict adherence to [Conventional Commits](https://www.conventionalcommits.org/)
* Comprehensive test coverage for each module before merge
* Zero secrets in commit history

---

## License

This project is licensed under the [MIT License](LICENSE).

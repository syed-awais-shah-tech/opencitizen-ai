# Local Development Setup Guide

This guide walks you through setting up a complete OpenCitizen AI development environment on your local machine without requiring external cloud accounts.

---

## 1. System Prerequisites

Ensure you have the following prerequisites installed:

| Tool | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11+ | 3.11 or 3.12 | Core backend environment |
| **Node.js** | 20 LTS | 20.x or 22.x LTS | Next.js frontend runtime |
| **npm** | 10+ | 10.x | Node package manager |
| **Git** | 2.40+ | Latest | Version control |
| **Docker** | 24+ | Latest Desktop | Optional for local PostgreSQL & Qdrant |

---

## 2. Repository Cloning & Environment Setup

Clone the repository and inspect the root structure:

```bash
git clone https://github.com/syed-awais-shah-tech/opencitizen-ai.git
cd opencitizen-ai
```

Copy the example environment file:
```bash
# On Linux / macOS
cp .env.example .env

# On Windows (PowerShell)
Copy-Item .env.example .env
```

### Environment Configuration (`.env`)
By default, OpenCitizen AI runs with hermetic offline defaults so you can develop without external API keys:
- `DATABASE_URL`: `postgresql://opencitizen:opencitizen_dev_password@localhost:5432/opencitizen_app` (or SQLite fallback `sqlite:///./storage/app.db`)
- `QDRANT_HOST`: `localhost`
- `QDRANT_PORT`: `6333`
- `QDRANT_IN_MEMORY`: `false` (set to `true` to run an embedded in-memory vector store without Docker)
- `LLM_PROVIDER`: `mock` (or `gemini` if you supply a `GEMINI_API_KEY`)
- `EMBEDDING_PROVIDER`: `mock` (or `gemini` with `GEMINI_API_KEY`)

---

## 3. Backend Setup (FastAPI & Python)

The backend code is contained in `backend/`.

### 3.1 Create and Activate Virtual Environment
```bash
# On Linux / macOS
python3 -m venv backend/.venv
source backend/.venv/bin/activate

# On Windows (PowerShell)
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
```

### 3.2 Install Dependencies
Install dependencies in editable mode along with dev/test packages:
```bash
pip install --upgrade pip
pip install -e "./backend[dev]"
```

### 3.3 Initialize Database Migrations
If running local PostgreSQL:
```bash
cd backend
alembic upgrade head
cd ..
```
*Note: If PostgreSQL is not running, the application and tests automatically fall back to SQLite or in-memory execution.*

### 3.4 Start the FastAPI Server
```bash
# From workspace root
uvicorn backend.app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## 4. Frontend Setup (Next.js & TypeScript)

The frontend code is contained in `frontend/`.

### 4.1 Install Node Dependencies
```bash
cd frontend
npm ci
```

### 4.2 Start Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

The frontend includes pages for:
- `/`: Interactive Dashboard and Activity Overview
- `/datasets`: Tabular CSV/XLSX/JSON Ingestion, Schema Preview, and DuckDB Analysis
- `/documents`: PDF Ingestion, Text Extraction, and Chunk Inspector
- `/query`: Natural Language Q&A with Evidence Citations and Dynamic Visualizations
- `/evidence`: Citation & Provenance Inspection Drawer

---

## 5. Automated Setup Scripts

For rapid bootstrapping, you can use the automated setup scripts in `scripts/`:

### PowerShell (Windows)
```powershell
.\scripts\setup.ps1
```

### Bash (Linux / macOS)
```bash
chmod +x ./scripts/setup.sh
./scripts/setup.sh
```

---

## 6. Next Steps
- Review [Docker Setup Guide](docker-setup.md) to run PostgreSQL and Qdrant in containers.
- Review [Testing Guide](testing.md) to run unit and integration tests.
- Review [Contributing Guidelines](../CONTRIBUTING.md) before submitting code.

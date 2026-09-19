# OpenCitizen AI - Getting Started & Developer Guide

**Stage:** Stage 1 (Foundation)  
**Last Updated:** September 2026  

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
* **Node.js** (>= 20 LTS or Node 24) & **npm** (>= 10)
* **Python** (>= 3.11) & **uv** (>= 0.5)
* **Git** (>= 2.40)
* **Docker Desktop** (planned for Milestone 1 / Stage 2 container orchestration)

---

## 2. Quick Setup

We provide automated setup scripts in `scripts/`:

### Windows (PowerShell)
```powershell
.\scripts\setup.ps1
```

### Linux / macOS (Bash)
```bash
./scripts/setup.sh
```

---

## 3. Manual Component Setup

### Backend (FastAPI + Python)

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create a virtual environment using `uv`:
   ```bash
   uv venv .venv
   ```

3. Activate the virtual environment:
   * **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\activate
     ```
   * **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

4. Install dependencies in editable mode:
   ```bash
   uv pip install -e ".[dev]"
   ```

5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. Verify the health check endpoint:
   * `http://localhost:8000/health`
   * `http://localhost:8000/docs` (Swagger UI)

### Frontend (Next.js + TypeScript)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Running Automated Tests

### Backend Tests
```bash
# From workspace root
backend\.venv\Scripts\pytest backend/tests

# Or with virtualenv activated
pytest backend/tests tests/backend
```

### Frontend Validation & Build
```bash
cd frontend
npm run build
```

---

## 5. Development Scripts Directory

| Script | Purpose |
| :--- | :--- |
| `scripts/setup.ps1` / `scripts/setup.sh` | One-shot setup of virtualenv, backend dependencies, and npm packages. |
| `scripts/test.ps1` / `scripts/test.sh` | Runs backend pytest suite and frontend validation. |
| `scripts/dev.ps1` / `scripts/dev.sh` | Starts development servers for frontend and backend. |

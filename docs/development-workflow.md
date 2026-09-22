# Development Workflow & Continuous Integration Guide

**OpenCitizen AI — Stage 19 Architecture & Workflow Document**

---

## 1. Overview & Core Engineering Principles

OpenCitizen AI operates under strict engineering, safety, and evidence-grounding invariants. All development follows an incremental, test-driven, and verifiable approach:

1. **Incremental & Atomic**: Features and bug fixes are developed in small, reviewable increments. Monolithic pull requests are avoided.
2. **Conventional Commits**: Every commit follows the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) format (`type(scope): imperative description`).
3. **Automated Verification**: Every pull request must pass all frontend checks, backend unit tests, linting, and integration tests before merging.
4. **Zero-Secret Invariant**: API keys, credentials, tokens, and production secrets must never be placed in source code, committed to Git, or exposed in CI workflow logs.
5. **Strict Failure Boundaries**: CI workflows fail immediately upon test failures, type mismatches, or lint violations.

---

## 2. Local Development Environment

### 2.1 Prerequisites
- **Git** (>= 2.40)
- **Python** (>= 3.11)
- **Node.js** (>= 20 LTS) & **npm** (>= 10)
- **Docker & Docker Compose** (optional, for containerized local services)

### 2.2 Backend Setup & Verification
Create and activate a virtual environment, then install dependencies with dev extras:

```bash
# From workspace root
python -m venv backend/.venv

# Activate virtual environment (Windows PowerShell)
.\backend\.venv\Scripts\Activate.ps1
# Or on Linux/macOS
source backend/.venv/bin/activate

# Install backend package with test/dev dependencies
pip install --upgrade pip
pip install -e "./backend[dev]"
```

#### Running Backend Checks Locally:
```bash
# 1. Run Ruff Linter
ruff check backend

# 2. Run Backend Unit & Module Test Suite (264+ tests)
pytest backend/tests -v

# 3. Run Root Integration Tests
pytest tests -v
```

### 2.3 Frontend Setup & Verification
Install frontend dependencies using `npm ci`:

```bash
# Navigate to frontend directory
cd frontend
npm ci

# 1. Run TypeScript Typecheck (strict type verification)
npm run typecheck

# 2. Run Production Build Validation (linting + static page optimization)
npm run build

# 3. Run Local Development Server
npm run dev
```

---

## 3. Continuous Integration Pipeline (GitHub Actions)

OpenCitizen AI employs a GitHub Actions workflow defined in `.github/workflows/ci.yml`. The pipeline runs automatically on:
- All **pull requests** targeting the `main` branch.
- All **pushes** directly to the `main` branch.

### 3.1 Concurrency & Security Controls
- **Auto-Cancellation**: In-flight CI runs for older commits on the same branch are cancelled automatically (`cancel-in-progress: true`).
- **Read-Only Permissions**: Workflows run with restricted `contents: read` permissions.
- **Zero-Secret Logging**: No secrets or credentials are passed to or printed by CI logs. Tests execute hermetically in-memory (`QDRANT_IN_MEMORY=true`, `DATABASE_URL=sqlite:///:memory:`).

### 3.2 Job Architecture

```
                          ┌────────────────────────┐
                          │  GitHub Pull Request   │
                          └───────────┬────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
      ┌──────────────────────────────┐  ┌──────────────────────────────┐
      │       backend-checks         │  │       frontend-checks        │
      ├──────────────────────────────┤  ├──────────────────────────────┤
      │ 1. Checkout repository       │  │ 1. Checkout repository       │
      │ 2. Set up Python 3.11        │  │ 2. Set up Node.js 20 LTS     │
      │ 3. pip install -e .[dev]     │  │ 3. npm ci --prefix frontend  │
      │ 4. ruff check backend        │  │ 4. npm run typecheck         │
      │ 5. pytest backend/tests      │  │ 5. npm run build             │
      │ 6. pytest tests              │  │                              │
      └──────────────────────────────┘  └──────────────────────────────┘
```

#### Job 1: `backend-checks`
1. **Environment Initialization**: Configures Ubuntu latest with Python 3.11 and pip caching based on `backend/pyproject.toml`.
2. **Dependency Installation**: Upgrades pip and installs `opencv-backend` with dev dependencies (`pytest`, `pytest-asyncio`, `httpx`, `ruff`).
3. **Linting Check**: Executes `ruff check backend`, catching syntax anomalies, undefined symbols, and style violations.
4. **Backend Unit & Module Tests**: Executes `pytest backend/tests -v`, validating all analytics, connectors, documents, ingestion, orchestration, RAG, trust, and geospatial components.
5. **Integration Tests**: Executes `pytest tests -v`, validating multi-service and root integration endpoints.

#### Job 2: `frontend-checks`
1. **Environment Initialization**: Configures Ubuntu latest with Node.js 20 LTS and npm caching based on `frontend/package-lock.json`.
2. **Clean Dependency Installation**: Executes `npm ci` for deterministic reproducible builds.
3. **TypeScript Typecheck**: Executes `npm run typecheck` (`tsc --noEmit`), enforcing compile-time type safety across all React components, hooks, and types.
4. **Next.js Production Build**: Executes `npm run build`, validating JSX compilation, route layouts, static generation, and CSS bundles.

---

## 4. Pull Request Guidelines

Before submitting a pull request:

1. **Keep Branches Focused**: Create a branch off `main` with a conventional name (e.g. `feat/geospatial-capability`, `fix/connector-timeout`).
2. **Run Local Validation**:
   ```bash
   ruff check backend
   pytest backend/tests
   npm run typecheck --prefix frontend
   npm run build --prefix frontend
   ```
3. **Inspect Diff**: Ensure no temporary artifacts, `.env` files, or unintended files are staged (`git status`, `git diff`).
4. **Conventional Commit Message**:
   ```
   type(scope): concise imperative description
   ```
5. **Verify GitHub Actions**: Ensure all checks turn green in the GitHub PR interface. Any failure blocks merging until addressed.

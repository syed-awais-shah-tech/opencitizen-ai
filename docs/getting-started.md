# OpenCitizen AI - Getting Started & Developer Guide

Welcome to OpenCitizen AI! This guide provides a fast onboarding path for developers and researchers looking to explore, run, and contribute to the platform.

---

## 1. Quick Navigation

Depending on what you want to do, jump directly to the relevant guide:

- **New Developer Setup:** [Local Development Setup Guide](local-setup.md)
- **Container Infrastructure:** [Docker & Docker Compose Setup Guide](docker-setup.md)
- **Development & CI Pipeline:** [Development Workflow & CI Guide](development-workflow.md)
- **Testing & Quality Assurance:** [Comprehensive Testing Guide](testing.md)
- **Adding External Data Feeds:** [Extending Connectors Guide](extending-connectors.md)
- **Adding Custom LLMs or Embeddings:** [Extending AI Providers Guide](extending-ai-providers.md)
- **Customizing Retrieval & Rerankers:** [Extending Retrieval Strategies Guide](extending-retrieval-strategies.md)
- **System Architecture Deep-Dive:** [System Architecture Document](../ARCHITECTURE.md)
- **Contributing & Pull Requests:** [Contributing Guidelines](../CONTRIBUTING.md)

---

## 2. 5-Minute Quickstart (Hermetic Local Execution)

OpenCitizen AI is designed to run offline without external API keys or cloud accounts out of the box.

### 2.1 Clone & Configure
```bash
git clone https://github.com/syed-awais-shah-tech/opencitizen-ai.git
cd opencitizen-ai
cp .env.example .env
```

### 2.2 Run Backend (FastAPI)
```bash
# Set up Python virtual environment
python -m venv backend/.venv
source backend/.venv/bin/activate   # Windows: .\backend\.venv\Scripts\Activate.ps1

# Install package with dev dependencies
pip install -e "./backend[dev]"

# Start API server
uvicorn backend.app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 2.3 Run Frontend (Next.js)
In a separate terminal:
```bash
cd frontend
npm ci
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## 3. Running Verification Locally

Before submitting code, always run the full test suite:

```bash
# Backend linting
ruff check backend

# Backend unit & integration tests (265+ tests)
pytest backend/tests tests -v

# Frontend typecheck & build
npm run typecheck --prefix frontend
npm run build --prefix frontend
```

All 265+ tests run hermetically in-memory and execute in under 30 seconds.

---

## 4. Need Help?

- Check the [Project Roadmap](../ROADMAP.md) for milestone progress and upcoming capabilities.
- Open an issue using one of our [GitHub Issue Templates](../.github/ISSUE_TEMPLATE/).
- Report security issues privately following our [Security Policy](../SECURITY.md).

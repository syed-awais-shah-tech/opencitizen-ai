# Contributing to OpenCitizen AI

Thank you for your interest in contributing to OpenCitizen AI! We are building an evidence-grounded AI platform for analyzing public documents and structured datasets with verifiable calculations and source attribution.

Please review this guide before submitting contributions.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all project spaces.

---

## Core Development Philosophy

1. **Incremental & Atomic:** We build iteratively in small, reviewable steps. We avoid massive, monolithic pull requests.
2. **Quality & Verification:** Every completed atomic module must include tests (unit, integration, or linting) before being merged.
3. **Evidence & Truthfulness:** We do not claim features are implemented when they are still planned. Documentation must reflect actual project state.
4. **Zero Secrets:** Never commit secrets, credentials, API keys, or `.env` files.

---

## Conventional Commits

We strictly follow the [Conventional Commits](https://www.conventionalcommits.org/) specification (v1.0.0).

Commit messages must take the form:
```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

### Allowed Types:
* `feat`: A new user-facing or platform feature
* `fix`: A bug fix
* `docs`: Documentation updates or additions
* `style`: Formatting, missing semicolons, etc. (no code change)
* `refactor`: Refactoring production code without changing behavior
* `test`: Adding or correcting tests
* `chore`: Maintenance tasks, dependency updates, repo scaffolding

### Example:
```bash
feat(backend): implement duckdb query execution service
test(api): add tests for document upload endpoint
chore(repo): initialize project structure
```

---

## Getting Started

### Prerequisites
* **Git** (>= 2.40)
* **GitHub CLI** (`gh`)
* **Node.js** (>= 20 LTS) & **npm**
* **Python** (>= 3.11) & **uv** (recommended for fast package management)
* **Docker** & **Docker Compose** (for multi-service orchestration)

### Development Workflow

1. **Fork or Branch:**
   Create a descriptive feature branch from `main`:
   ```bash
   git checkout -b feat/evidence-grounding
   ```

2. **Make Changes Incrementally:**
   Keep changes focused on a single atomic responsibility.

3. **Verify & Test:**
   Run relevant tests and linters for the modified component:
   * Frontend: `npm test` / `npm run lint`
   * Backend: `pytest` / `ruff check`

4. **Review Git Diff:**
   Ensure no stray files, debug logs, or credentials are staged:
   ```bash
   git status
   git diff
   ```

5. **Commit & Push:**
   Stage only relevant files and write a clear conventional commit message:
   ```bash
   git add <specific-files>
   git commit -m "feat(module): add atomic capability"
   git push origin feat/evidence-grounding
   ```

6. **Submit a Pull Request:**
   Open a PR against `main` detailing the changes made, tests executed, and design rationale.

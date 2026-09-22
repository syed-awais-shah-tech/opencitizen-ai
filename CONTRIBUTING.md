# Contributing to OpenCitizen AI

Thank you for your interest in contributing to OpenCitizen AI! We are building an evidence-grounded, verifiable AI platform for public documents and civic tabular datasets.

Please review this guide before submitting issues or pull requests.

---

## Code of Conduct

All contributors, maintainers, and community members are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md) in all project spaces.

---

## Core Engineering Invariants

1. **Evidence Grounding Before Generation:** Answers must be backed strictly by retrieved document passages or computed dataset records. Factual claims without evidence are prohibited.
2. **Deterministic Calculations:** Mathematical claims are computed directly in DuckDB—never guessed by the LLM.
3. **Inspectable Provenance:** Every response retains document IDs, page numbers, text excerpts, or the exact SQL query run.
4. **Incremental & Atomic Work:** Features, bug fixes, and documentation updates are developed in small, reviewable increments.
5. **Full Test Verification:** Every module must include unit and integration tests with 100% passing status prior to merge.
6. **Zero Secrets:** Never commit `.env` files, API keys, passwords, tokens, or credentials.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Check existing issues to see if the bug has already been reported.
- If not, open an issue using the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- Include minimal reproduction steps, expected vs. actual behavior, and error tracebacks (scrubbed of any sensitive data).

### 2. Suggesting Features & Civic Data Sources
- Check the [Project Roadmap](ROADMAP.md) to see if the feature is already planned.
- Open an issue using the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- Focus on civic research use cases, grounding requirements, and clean architectural abstractions.

### 3. Finding Beginner-Friendly Issues
- Look for issues labeled [`good first issue`](.github/ISSUE_TEMPLATE/good_first_issue.md) or [`help wanted`](.github/ISSUE_TEMPLATE/help_wanted.md).
- These tasks are self-contained and ideal for familiarizing yourself with the codebase.

### 4. Extending Subsystems
We provide comprehensive architectural guides for extending key subsystems:
- **Connectors**: See [Extending Connectors Guide](docs/extending-connectors.md) to add public open data portals (CKAN, Socrata, Eurostat, Census).
- **AI Providers**: See [Extending AI Providers Guide](docs/extending-ai-providers.md) to integrate local LLMs (Ollama, vLLM) or alternative APIs (Claude, OpenAI).
- **Retrieval Strategies**: See [Extending Retrieval Strategies Guide](docs/extending-retrieval-strategies.md) for custom vector stores, BM25 tuning, or rerankers.
- **Geospatial**: See [Geospatial Architecture Guide](docs/geospatial-architecture.md) for GeoJSON and mapping extensions.

---

## Development Environment Setup

Please follow our detailed setup guides:
- **Local Development**: [Local Setup Guide](docs/local-setup.md)
- **Containerized Services**: [Docker Setup Guide](docs/docker-setup.md)
- **CI/CD & Workflows**: [Development Workflow Guide](docs/development-workflow.md)
- **Testing Guide**: [Comprehensive Testing Guide](docs/testing.md)

---

## Conventional Commits

We strictly follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification. Every commit message must follow this format:

```
<type>(<scope>): <imperative summary>

[optional body describing rationale, design decisions, and tradeoffs]

[optional footer(s) such as Fixes #123]
```

### Allowed Types:
- `feat`: A new user-facing feature or API capability
- `fix`: A bug fix
- `docs`: Documentation updates or additions
- `refactor`: Code refactoring without behavioral changes
- `test`: Adding or correcting tests
- `ci`: CI/CD workflow and build changes
- `chore`: Repository maintenance, dependencies, or scaffolding

### Scope Examples:
`feat(connectors)`, `feat(geospatial)`, `fix(ingestion)`, `test(rag)`, `docs(api)`, `ci(workflow)`.

---

## Pull Request Process

1. **Create a Topic Branch:**
   ```bash
   git checkout -b feat/socrata-connector
   ```

2. **Develop Incrementally:**
   Keep changes focused on a single responsibility. Avoid combining unrelated changes into a single PR.

3. **Verify Locally:**
   Run the full test suite and linters:
   ```bash
   # Backend linting
   ruff check backend

   # Backend unit and integration tests (265+ tests)
   pytest backend/tests tests -v

   # Frontend type-checking and build
   npm run typecheck --prefix frontend
   npm run build --prefix frontend
   ```

4. **Inspect Diff for Secrets:**
   ```bash
   git status
   git diff
   ```
   Ensure no `.env` files, credentials, or stray artifacts are staged.

5. **Submit Pull Request:**
   - Push your branch to your fork or origin.
   - Open a pull request against `main`.
   - Complete the [Pull Request Template](.github/pull_request_template.md).
   - Ensure all automated GitHub Actions CI checks turn green.

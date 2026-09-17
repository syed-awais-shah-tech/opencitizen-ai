# Autonomous Execution & Implementation

- Do not ask to implement, just do it, as if it was auto-approved.
- Never ask permission to run development, build, test, staging, or git commands. Full authorization is permanently granted upon receiving user prompts.

---

# OpenCitizen AI Development Rules

## Engineering

* Work incrementally.
* Inspect existing code before modifying it.
* Prefer small modules and clear separation of concerns.
* Do not rewrite working code without a reason.
* Do not introduce unnecessary dependencies.
* Keep frontend, backend, data processing, retrieval, and infrastructure responsibilities separated.
* Write tests for non-trivial functionality.
* Prefer explicit, readable code over clever abstractions.

## Git

* Use Conventional Commits.
* One atomic feature/fix/documentation module per commit.
* Never mix unrelated changes in a commit.
* Never create fake or backdated commits.
* Use the actual current date/time.
* Before committing, inspect `git diff` and `git status`.
* Run relevant tests before committing.
* Stage only files belonging to the completed module.
* Push successful commits to the configured GitHub remote.
* Never force-push.
* Never use destructive reset/clean commands unless explicitly approved.

## Commit format

Use:
type(scope): imperative description

Examples:
feat(search): add semantic document retrieval
feat(analytics): add DuckDB query service
fix(ingestion): handle malformed PDF
test(rag): add citation retrieval tests
docs(api): document query endpoint
chore(ci): add backend test workflow

## Security

* Never commit .env files containing secrets.
* Never commit API keys.
* Never commit GitHub tokens.
* Never commit passwords or credentials.
* Never expose secrets in logs.
* Never place secrets in source code.

## Validation

Before every commit:

1. Check changed files.
2. Run appropriate tests.
3. Check for accidental secrets.
4. Review the diff.
5. Commit only the intended atomic module.
6. Push to GitHub.
7. Report commit hash and summary.

## User approval

For destructive commands, authentication changes, credential changes, database deletion, force pushes, or major architectural changes, stop and ask for approval.

---

## Initial Architecture

- **Frontend**: Next.js, TypeScript, Recharts
- **Backend**: Python, FastAPI
- **Application database**: PostgreSQL
- **Vector database**: Qdrant
- **Analytical engine**: DuckDB
- **AI**: Gemini API through a clean provider abstraction
- **Data processing**: Pandas where appropriate
- **Infrastructure**: Docker Compose
- **Testing**: frontend tests, backend tests, integration tests as the project grows

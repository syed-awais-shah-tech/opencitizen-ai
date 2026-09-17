# Implement

- Do not ask to implement, just do it, as if it was auto-approved.

---

# OpenCitizen AI - Project Rules & Guidelines

## Core Development Rules
1. Work incrementally. Never build the entire application at once.
2. Before changing files, inspect the current repository and explain the proposed change.
3. Do not rewrite working code unnecessarily.
4. Do not introduce technologies that are not part of the agreed architecture without explaining why.
5. Prefer small, reviewable modules.
6. Every completed atomic module must be tested before committing.
7. After an atomic module is complete and tests pass:
   - inspect git diff
   - stage only the files belonging to that module
   - create one Conventional Commit
   - push the commit to the configured GitHub remote
8. Do not make fake, backdated, or misleading commit dates. Commit using the actual current date/time.
9. Never commit secrets, API keys, passwords, tokens, .env files containing secrets, or credentials.
10. Never run destructive git commands such as reset --hard, clean -fd, force push, or deleting branches unless explicitly approved.
11. Before every commit, show:
    - files changed
    - tests run
    - commit message
    - files that will be included in the commit
12. Never combine unrelated features into one commit.

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

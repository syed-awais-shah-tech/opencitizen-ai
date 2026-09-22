## Description
Briefly describe what changes this pull request introduces and the motivation behind them.

Fixes #(issue number)

## Type of Change
- [ ] `feat`: New user-facing feature or API capability
- [ ] `fix`: Bug fix
- [ ] `docs`: Documentation updates or additions
- [ ] `refactor`: Code refactoring without behavioral changes
- [ ] `test`: New or updated tests
- [ ] `ci`: CI/CD workflow updates
- [ ] `chore`: Repository maintenance, dependencies, or scaffolding

## Key Changes
- Itemized list of changes made
- Architectural decisions or non-obvious rationale

## Verification & Testing
Describe the tests you ran to verify your changes:
- [ ] Backend unit & module tests: `pytest backend/tests`
- [ ] Integration tests: `pytest tests`
- [ ] Ruff linter check: `ruff check backend`
- [ ] Frontend type check: `npm run typecheck --prefix frontend`
- [ ] Frontend production build: `npm run build --prefix frontend`
- [ ] Tested manually (e.g. browser UI, Swagger docs at `/docs`)

## Checklist
- [ ] My code adheres to the project's coding and style guidelines.
- [ ] I have self-reviewed my code and checked `git diff`.
- [ ] I have added/updated tests that prove my fix is effective or feature works.
- [ ] I have updated relevant documentation in `docs/` or `README.md`.
- [ ] No secrets, credentials, API keys, or private tokens are introduced or committed.
- [ ] Conventional Commit format is used (`type(scope): imperative description`).
- [ ] All CI checks pass cleanly.

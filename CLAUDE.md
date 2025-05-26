# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands
- Run all tests: `make test`
- Run single test: `docker compose run --rm test pytest tests/test_file.py::TestClass::test_function`
- Lint code: `make ruff`
- Type check: `make mypy`
- Run all checks: `make all`

## Code Style Guidelines
- **Formatting**: Black with 100 char line length
- **Imports**: Use isort (stdlib → third-party → first-party → local)
- **Types**: Use strict typing with mypy, Protocol for interfaces
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Extend from NewsAssistantError base class with message, error_code, and details
- **Architecture**: Service-oriented with dependency injection
- **Tests**: pytest with fixtures for DB and API client

## Git Workflow
- **Issue Work**: Always create a new branch before starting work on any GitHub issue
- **Branch Naming**: Use format `feature/issue-{number}-{brief-description}` or `fix/issue-{number}-{brief-description}`

## Repository Structure
Modular organization with domain-specific modules (ai, articles, content, speech, etc.)
FastAPI for web APIs, SQLAlchemy for database, Pydantic for validation
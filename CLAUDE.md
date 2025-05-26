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
- **Pull Requests**: Always use MCP GitHub tools (mcp__github__create_pull_request) to create pull requests, not gh CLI

## GitHub Operations
- **Always use MCP tools**: All GitHub operations (PRs, issues, reviews, etc.) should be performed using MCP GitHub tools (mcp__github__*)
- **Available operations**:
  - Creating/updating pull requests: `mcp__github__create_pull_request`, `mcp__github__update_pull_request`
  - Managing issues: `mcp__github__create_issue`, `mcp__github__update_issue`, `mcp__github__add_issue_comment`
  - Code reviews: `mcp__github__create_pending_pull_request_review`, `mcp__github__submit_pending_pull_request_review`
  - Repository operations: `mcp__github__create_branch`, `mcp__github__push_files`
- **Never use gh CLI**: Do not use `gh` command for GitHub operations

## Repository Structure
Modular organization with domain-specific modules (ai, articles, content, speech, etc.)
FastAPI for web APIs, SQLAlchemy for database, Pydantic for validation
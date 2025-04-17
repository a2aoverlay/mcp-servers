# Agent Git MCP Server - Developer Guidelines

## Commands
- Install: `pip install -e "src/agent_git[dev]"` or use `uv`
- Test: `cd src/agent_git && python -m pytest`
- Run single test: `cd src/agent_git && python -m pytest tests/test_server.py::test_git_commit_valid_message -v`
- Lint: `cd src/agent_git && ruff check .`
- Type check: `cd src/agent_git && pyright`

## Code Style
- Follow PEP 8 conventions for Python code formatting
- Use explicit type hints for all functions and class attributes
- Use Pydantic models for data validation and schema definition
- Exception handling: Use specific exceptions with descriptive error messages
- Imports: Group imports by standard library, third-party, and local modules
- Model naming: Use clear, descriptive names for Pydantic models (e.g., GitStatus)
- Tool naming: Use Enum classes for tool names (follow GitTools pattern)
- Always include docstrings for test fixtures and complex functions

## Git Conventions
- All commit messages must begin with "[agent]" prefix
- GPG signing is required for all commits (-S flag)
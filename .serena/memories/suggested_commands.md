# Suggested Commands for Prosemark Development

## Development Workflow Commands
- `uv sync --all-groups` - Install all dependencies including dev and test groups
- `uv add <package>` - Add runtime dependency
- `uv add --group dev <package>` - Add development dependency
- `uv add --group test <package>` - Add test dependency

## Code Quality Commands (run after changes)
1. `uv run ruff format` - Format code
2. `uv run ruff check` - Run linter
3. `uv run mypy` - Type checking
4. `uv run pytest` - Run tests
5. `uv run pytest --cov` - Run tests with coverage

## Testing Commands
- `uv run pytest tests/` - Run all tests
- `uv run pytest tests/test_app_*.py` - Run application layer tests
- `uv run pytest -k "test_name"` - Run specific test
- `uv run pytest --random-order` - Run tests in random order

## Project Management
- `pmk` - Main CLI entry point (when installed)
- `git` - Version control operations

## System Commands (Darwin/macOS)
- `ls`, `cd`, `pwd` - Directory navigation
- `grep`, `find` - Text/file search
- `cat`, `head`, `tail` - File viewing

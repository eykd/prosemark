# Conventions for the prosemark project

## When asked to create new conventions

When asked to create a new convention (`CONVENTIONS.md`), add a second-level
heading section to this document, `CONVENTIONS.md`.

- Name the new convention heading with a short, descriptive title.
- Use the first line of the section to elaborate on the "When..." of the heading.
- Use bullet points to organize further details for the convention.
- Use full imperative sentences.
- Keep new conventions short and to the point.
- Use short examples for complex conventions.

## Python code style and quality

When writing or editing Python code (`*.py`), follow these quality standards:

- Use PEP8 style with CamelCase for class names and snake_case for variables/functions.
- Include type annotations for all functions, methods, and complex structures.
- Add Google Style docstrings to all packages, modules, functions, classes, and methods.
- Run code quality tools:
  - Format: `uv run ruff format`
  - Lint: `uv run ruff --fix check`
  - Type check: `uv run mypy`

## Hexagonal Architecture

When designing application components (`*.py`), use hexagonal architecture to separate business logic from external concerns:

- Place core business logic at the center, free from direct I/O dependencies.
- Define interfaces (ports) for all external interactions.
- Implement concrete adapters for external systems.
- Inject dependencies through constructor parameters or factory functions.
- When testing, use test doubles (fakes, stubs, mocks) for external dependencies.
- Test adapters separately with integration tests.

## Testing

When writing Python code (`*.py`), follow these testing practices:

- Write tests first for each change using pytest.
- Organize tests in a dedicated `tests/` folder by module.
- Use descriptive names for test functions and methods.
- Group related tests in test classes.
- Use fixtures for complex setup.
- Aim for 100% test coverage for code under `src/`.
- Move common fixtures to `tests/conftest.py`.

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
- Favor a functional style for core business logic.
- Define interfaces (ports) for all external interactions.
- Implement concrete adapters for external systems.
- Inject dependencies through constructor parameters or factory functions.
- When testing, use test doubles (fakes, stubs, mocks) for external dependencies.
- Test adapters separately with integration tests.

## Testing

When writing Python code (`*.py`), follow these testing practices:

- Write tests first for each change using pytest.
- Organize tests in a dedicated `tests/` folder in the project root.
- Name test files by package and module, omitting the root `prosemark` package name.
- Use descriptive names for test functions and methods.
- Group related tests in test classes.
- Use fixtures for complex setup.
- Aim for 100% test coverage for code under `src/`.
- When writing tests, move common fixtures to `tests/conftest.py`.

## Variable naming

When naming variables in Python code, follow these naming practices:

- Use concise but descriptive variable names that clearly indicate purpose.
- Avoid single-character variable names except in the simplest comprehensions and generator expressions.
- Follow snake_case for all variable names.
- Choose names that reveal intent and make code self-documenting.
- Use plural forms for collections (lists, sets, dictionaries) and singular forms for individual items.
- Prefix boolean variables with verbs like `is_`, `has_`, or `should_`.

## Exception style

When raising exceptions in Python code, follow these practices:

- Do not raise generic exceptions like `Exception` or `RuntimeError`.
- Use a specific exception defined in `src/prosemark/exceptions.py`.
- Define a new specific exception in `src/prosemark/exceptions.py` if none exists for your situation.
- Do not define `__init__` methods on custom exceptions.
- When raising exceptions with a string message, do not use variable substitution in the error message.
- Add extra context as further arguments to the exception instead of embedding variables in the message.
- Example:
  ```python
  # Bad
  raise ValueError(f"Node with ID {node_id} not found")
  
  # Good
  raise NodeNotFoundError("Node not found", node_id)
  ```

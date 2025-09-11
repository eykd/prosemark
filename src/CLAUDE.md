# Source Code Conventions for prosemark/src

## Package structure

When organizing code within `src/prosemark/`:

- Follow hexagonal architecture with clear separation of concerns.
- Place core business logic in `domain/` - pure functions and domain models.
- Define port interfaces (protocols/ABCs) in `ports/`.
- Implement external adapters in `adapters/`.
- Keep application orchestration logic in `application/`.
- Place custom exceptions in `exceptions.py` at the package root.

## Domain layer

When implementing business logic in `domain/`:

- Write pure functions without I/O or external dependencies.
- Use immutable data structures where possible (dataclasses with `frozen=True`).
- Return values rather than mutating state.
- Express business rules through domain models and value objects.
- Avoid framework-specific code or external library dependencies.

## Port interfaces

When defining ports in `ports/`:

- Use Python protocols or abstract base classes to define contracts.
- Keep interfaces focused on single responsibilities.
- Name ports by their business capability, not technical implementation.
- Example: `StoragePort` not `FileSystemInterface`.
- Include comprehensive docstrings describing the contract.

## Adapter implementations

When implementing adapters in `adapters/`:

- Create concrete implementations of port interfaces.
- Handle all external I/O and third-party integrations.
- Include both production adapters and in-memory fakes for testing.
- Name adapters by their implementation strategy.
- Example: `YAMLFileStorage`, `InMemoryStorage` for `StoragePort`.

## Dependency injection

When wiring dependencies:

- Inject dependencies through constructor parameters.
- Use factory functions or builder patterns for complex initialization.
- Never import concrete adapters directly in domain or application code.
- Pass port interfaces as type hints, not concrete implementations.
- Example:
  ```python
  def create_grammar_service(storage: StoragePort) -> GrammarService:
      return GrammarService(storage=storage)
  ```

## Module imports

When organizing imports:

- Group imports in order: standard library, third-party, local application.
- Use absolute imports from the package root: `from prosemark.domain import models`.
- Place type-checking-only imports in `TYPE_CHECKING` blocks with `# pragma: no cover`.
- Avoid circular imports by keeping dependencies unidirectional.

## Type annotations

When adding type hints:

- Annotate all function parameters and return types.
- Use generic types from `typing` for collections.
- Define custom type aliases for complex types at module level.
- Use `Protocol` for structural subtyping over inheritance.
- Example:
  ```python
  from typing import Protocol, Iterable

  GrammarRules = dict[str, list[str]]

  class Parser(Protocol):
      def parse(self, text: str) -> GrammarRules: ...
  ```

## Error handling

When handling errors:

- Define specific exceptions in `exceptions.py`.
- Raise exceptions with context using `raise ... from`.
- Let exceptions bubble up to application boundaries.
- Handle recovery logic in adapters, not domain code.
- Never catch generic `Exception` without re-raising.

## Code documentation

When documenting code:

- Add Google-style docstrings to all public modules, classes, and functions.
- Include type information in docstrings only when it adds clarity beyond type hints.
- Document the "why" not the "what" in inline comments.
- Keep docstrings concise but complete.
- Example:
  ```python
  def parse_grammar(content: str) -> Grammar:
      """Parse grammar rules from text content.

      Args:
          content: Raw grammar text in prosemark format.

      Returns:
          Parsed grammar object with validated rules.

      Raises:
          GrammarParseError: If content has invalid syntax.
      """
  ```

## Code quality standards

When writing any Python code:

- Follow PEP 8 with 120-character line length.
- Use descriptive variable names that reveal intent.
- Prefer composition over inheritance.
- Keep functions small and focused on single responsibilities.
- Extract complex expressions into well-named variables.
- After every change, run:
  1. `uv run ruff format`
  2. `uv run ruff check --fix --unsafe-fixes`
  3. `uv run mypy src/`
  4. `./scripts/runtests.sh`
- Failing linters, type-checking, or tests are NEVER ACCEPTABLE.
  - Engage the @python-linter-fixer sub-agent to address any linting problems.
  - Engage the @python-mypy-error-fixer sub-agent to address any typing problems.
- You MUST stop everything and fix failing checks. NO EXCEPTIONS.

## Test coverage pragmas

When writing Python code with untestable defensive programming constructs:

* Use `# pragma: no cover` for lines that cannot be practically tested.
* Use `# pragma: no branch` for branch conditions that cannot be practically tested.
* Apply pragmas to defensive re-raises, impossible conditions, and safety checks.

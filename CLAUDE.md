# Conventions for the prosemark project

The Linear project URL for this project is https://linear.app/solo-workbox/project/prosemark-1dcb08dfed59 and the project name is `Prosemark`.

## When asked to create new conventions

When asked to create a new convention (`CLAUDE.md`), add a second-level
heading section to this document, `CLAUDE.md`.

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
- After every change:
  1. Format: `uv run ruff format`
  2. Engage the @python-linter-fixer sub-agent to address any linting problems
  3. Engage the @mypy-error-fixer sub-agent to address any typing problems.

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

* Use Test-Driven Development (TDD):
  * Write one small test first for each change using pytest.
  * Run the new tests and ensure that they fail.
  * Implement just enough to make the test pass.
  * Iterate between test and implementation until the implementation matches the spec.
* Organize tests in a dedicated `tests/` folder in the project root.
* Name test files by package and module, omitting the root `prosemark` package name.
  * Example: `tests/test_domain_models.py` tests `src/prosemark/domain/models.py`
* Use descriptive names for test functions and methods.
* Group related tests in test classes.
* Use fixtures for complex setup.
* Aim for 100% test coverage for all code under `src/`.
* When writing tests, move common fixtures to `tests/conftest.py`.
* Run tests with `./scripts/runtests.sh` (which accepts normal `pytest` arguments and flags).
  * Example: `./scripts/runtests.sh tests/test_config_loader.py`

## Test organization with classes

When organizing tests in pytest, group related tests using `TestX` classes:

* Use `TestX` classes to group tests for the same module, function, or behavior.
* Name test classes with descriptive titles like `TestGrammarParser` or `TestFileStorage`.
* Do not inherit from `unittest.TestCase` since pytest handles plain classes.
* Place setup and teardown logic in `setup_method` and `teardown_method`.
* Example:
  ```python
  class TestGrammarParser:
      @pytest.fixture
      def parser(self) -> GrammarParser:
          return GrammarParser()

      def test_parses_simple_grammar(self, parser: GrammarParser) -> None:
          result = parser.parse("Begin: hello")
          assert result["Begin"] == ["hello"]
  ```

## Unit testing with pytest

When writing unit tests for Python libraries, follow these pytest best practices:

* Test public APIs and behaviors, not implementation details.
* Focus on testing function contracts: inputs, outputs, and side effects.
* Use pytest's built-in `assert` statements rather than unittest-style assertions.
* Structure tests with arrange-act-assert pattern for clarity.
* Test edge cases: empty inputs, None values, boundary conditions, and error states.
* Use parametrized tests for testing multiple similar cases:
  ```python
  @pytest.mark.parametrize("input_val,expected", [(1, 2), (3, 4)])
  def test_increment(input_val, expected):
      assert increment(input_val) == expected
  ```
* Mock external dependencies using `pytest-mock` or `unittest.mock`.
* Test exception handling explicitly with `pytest.raises()`:
  ```python
  def test_raises_value_error():
      with pytest.raises(ValueError, match="invalid input"):
          parse_config("bad_input")
  ```
* Use fixtures for test data and setup, preferring function-scoped fixtures.
* Test one behavior per test function to maintain clarity and isolation.
* Avoid testing private methods directly; test through public interfaces.
* Do not test third-party library functionality; focus on your code's usage of it.

## Test failure resolution

When tests fail during development, always fix them immediately:

* Stop all development work until failing tests are addressed.
* Identify the root cause of test failures before making changes.
* Fix the underlying issue rather than updating tests to match broken behavior.
* Ensure all tests pass before continuing with new development.
* Run the full test suite after fixes to prevent regression.
* Update mocks, test data, or test logic only when the intended behavior has genuinely changed.
* NEVER ignore or skip failing tests.

FAILING TESTS ARE NEVER ACCEPTABLE.

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
- When raising a new exception from within an exception handler, always `raise NewError from old_exception`:
  Define a new specific exception in `src/prosemark/exceptions.py` if none exists for your situation.
- Do not define `__init__` methods on custom exceptions.
- When raising exceptions with a string message, do not use variable substitution in the error message.
- Add extra context as further arguments to the exception instead of embedding variables in the message.
- Example:
  ```python
  # Bad
  try:
      ...
  except Exception:
      raise ValueError(f"Node with ID {node_id} not found")

  # Good
  try:
      ...
  except ValueError as exc:
      raise NodeNotFoundError("Node not found", node_id) from exc
  ```

## TYPE_CHECKING blocks

When using TYPE_CHECKING for import statements in Python code, follow these practices:

- Always add `# pragma: no cover` to the TYPE_CHECKING block to exclude it from coverage reports.
- Place all imports that are only needed for type checking inside this block.
- Example:
  ```python
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:  # pragma: no cover
      from some_module import SomeType
  ```

## Test coverage pragmas

When writing Python code with untestable defensive programming constructs:

* Use `# pragma: no cover` for lines that cannot be practically tested.
* Use `# pragma: no branch` for branch conditions that cannot be practically tested.
* Apply pragmas to defensive re-raises, impossible conditions, and safety checks.
* Examples:

  ```python
  except DeploymentError:
      raise  # pragma: no cover - defensive re-raise

  if some_impossible_condition:  # pragma: no branch
      raise RuntimeError("This should never happen")

  except Exception as exc:
      if isinstance(exc, SpecificError):  # pragma: no branch
          raise  # pragma: no cover
  ```

## Dependency management

When working with uv for dependency management:

* Always use `uv sync --all-groups` to install dependencies including dev and test groups.
* Use `uv add` to add new runtime dependencies.
* Use `uv add --group dev` or `uv add --group test` for development dependencies.

## Git commit style

When committing changes to the repository, use conventional commit format:

* Use the format: `<type>(<scope>): <description>`
* Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
* Keep the first line under 50 characters
* Use present tense imperative mood ("add feature" not "added feature")
* Examples:
  * `feat(cli): add new grammar validation command`
  * `fix(storage): handle missing YAML files gracefully`
  * `docs: update installation instructions`
  * `test(grammars): add tests for include functionality`

- The code formatter and linter will run via hook every time you write or edit a file. For instance, this will cause unused imports to disappear.

# Test Conventions for prosemark/tests

## Test folder structure

When creating test files in the `tests/` folder:

- Keep the folder structure completely flat - no subdirectories.
- Place all test files directly in `tests/`.
- Group related tests using test classes rather than folder hierarchy.

## Test file naming

When naming test files:

- Name test files by package and module path, omitting the root `prosemark` package name.
- Use underscores to separate package hierarchy levels.
- Example: `tests/test_domain_models.py` tests `src/prosemark/domain/models.py`
- Example: `tests/test_adapters_file_storage.py` tests `src/prosemark/adapters/file_storage.py`

## Test doubles and fakes

When implementing test doubles for protocols and abstract base classes:

- Never implement mocks directly in test files.
- Create in-memory fakes as concrete implementations in the appropriate location within `src/prosemark/`.
- Place fakes alongside their protocols/ABCs or in a dedicated `fakes` module within the same package.
- Use dependency injection to substitute fakes during testing.
- Example: For `StoragePort` protocol in `src/prosemark/ports/storage.py`, implement `InMemoryStorage` in `src/prosemark/adapters/in_memory.py`.

## Test organization

When organizing tests within a file:

- Use `TestX` classes to group related tests (e.g., `TestGrammarParser`).
- Place shared fixtures in `tests/conftest.py`.
- Follow the arrange-act-assert pattern for test structure.
- Test one behavior per test function.

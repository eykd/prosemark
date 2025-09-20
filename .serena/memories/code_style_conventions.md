# Code Style and Conventions

## Python Style (from CLAUDE.md)
- Follow PEP8 with CamelCase for classes, snake_case for variables/functions
- Include type annotations for all functions, methods, and complex structures
- Add Google Style docstrings to all packages, modules, functions, classes, and methods
- Use hexagonal architecture with dependency injection
- Favor functional style for core business logic
- Define interfaces (ports) for all external interactions

## Exception Handling
- Use specific exceptions from `src/prosemark/exceptions.py`
- No custom `__init__` methods on exceptions
- Use `raise NewError from old_exception` pattern
- Pass extra context as arguments, not in message strings

## Testing Practices
- Use Test-Driven Development (TDD)
- Organize tests in `tests/` folder
- Name test files by package/module: `test_domain_models.py`
- Use `TestX` classes to group related tests
- Use pytest fixtures for setup
- Aim for 100% test coverage

## TYPE_CHECKING blocks
- Always add `# pragma: no cover` to TYPE_CHECKING blocks
- Place type-only imports inside these blocks

## Variable Naming
- Use descriptive names that reveal intent
- Follow snake_case for variables
- Use plural forms for collections
- Prefix booleans with `is_`, `has_`, `should_`

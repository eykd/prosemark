# Task Completion Workflow

## After Every Code Change (from CLAUDE.md)
1. Format: `uv run ruff format`
2. Engage @python-linter-fixer sub-agent to address linting problems
3. Engage @python-mypy-error-fixer sub-agent to address typing problems
4. Engage @python-test-runner sub-agent to ensure all tests pass
5. Repeat until all issues are addressed
6. Once code quality is verified, engage @conventional-committer sub-agent to commit changes
7. If working on Linear issue and commit completes the task, mark the issue as done

## Quality Gates
- NEVER bypass verification when committing to git
- Always run linters and type checker after making changes
- MUST fix all linter and type-checking errors before committing
- FAILING TESTS ARE NEVER ACCEPTABLE - fix immediately

## Git Commit Style
- Use conventional commit format: `<type>(<scope>): <description>`
- Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Keep first line under 50 characters
- Use present tense imperative mood

## Test-Driven Development
- Write tests FIRST for each change
- Run new tests and ensure they fail
- Implement just enough to make tests pass
- Iterate between test and implementation

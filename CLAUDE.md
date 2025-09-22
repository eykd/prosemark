## Quality checks when making python changes

When making changes to python files, you MUST ensure the highest quality:

1. Use @agent-python-mypy-error-fixer to address all typing errors
2. Then engage @agent-python-linter-fixer to address any linting errors.
3. Continue with 1 & 2 until linting and typing both pass. Watch out for them undoing each other's work.
4. Once that's done, use @agent-python-test-runner to run and fix any broken tests.
5. When you think everything is fixed, run typing, linting, and tests one more time.
6. All quality checks MUST pass. If anything doesn't pass, you MUST engage that agent again to fix it.

---
description: Ensure the quality of a python project by running quality-assurance processes.
---

1. Use @agent-python-mypy-error-fixer to address all typing errors
2. Then engage @agent-python-linter-fixer to address any linting errors.
3. Continue with 1 & 2 until linting and typing both pass. Watch out for them undoing each other's work.
4. Once that's done, use @agent-python-test-runner to run and fix any broken tests.
5. When you think everything is fixed, run typing, linting, and tests one more time. All tests MUST pass. If anything doesn't pass, you MUST engage that agent again to fix it.
5. Once all linting, typing, and tests pass, commit all changes with @agent-conventional-committer.md

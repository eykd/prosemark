<!--
Sync Impact Report:
- Version change: None → v1.0.0 (initial creation)
- Modified principles: N/A (initial creation)
- Added sections: All sections (complete constitution)
- Removed sections: N/A
- Templates requiring updates: ✅ Updated plan-template.md version reference
- Follow-up TODOs: None
-->

# Prosemark Constitution

## Core Principles

### I. Hexagonal Architecture
Core business logic MUST be separated from external concerns through ports and adapters. Business logic functions MUST be pure where possible with side effects isolated behind port interfaces. All external systems (file I/O, CLI, editors) MUST interact through adapter implementations only. This ensures testability and future extensibility to GUI or web interfaces without domain changes.

### II. Test-First Development (NON-NEGOTIABLE)
Test-Driven Development is mandatory for all code changes. Tests MUST be written first, confirmed to fail, then implementation proceeds until tests pass. No code changes are acceptable without prior test coverage. Failing tests MUST be fixed immediately before any other development work. This ensures reliability and prevents regression in the writing tool's core functionality.

### III. Plain Text Storage
All project data MUST be stored in plain text formats using Markdown + YAML frontmatter. Files MUST remain Obsidian-compatible for interoperability. Identity uses UUIDv7 for stability across sessions. Binder structure allows free-form prose outside managed blocks for user flexibility while maintaining programmatic access.

### IV. Code Quality Standards
All Python code MUST pass ruff formatting, linting, and mypy type checking before commit. Type annotations are required for all functions and methods. Google Style docstrings MUST be provided for all public APIs. 100% test coverage is required for all source code under `src/`. Quality gates prevent degradation of the codebase.

### V. CLI-First Interface
Every feature MUST be accessible through simple CLI commands that map directly to use cases. Commands follow text in/out protocol: stdin/args → stdout, errors → stderr. Support both JSON and human-readable output formats. CLI provides the canonical interface with other interfaces (future GUI/web) built as adapters.

## Development Workflow

All development MUST follow the established quality pipeline: format code → fix linting → resolve typing → run tests → commit changes. Sub-agents (@python-linter-fixer, @python-mypy-error-fixer, @python-test-runner, @conventional-committer) automate quality enforcement. Linear issue tracking integrates with commits for project management. Changes bypass verification only in genuine emergencies with immediate remediation required.

## File Organization

Project structure follows hexagonal architecture with clear separation: `src/prosemark/domain/` (core logic), `src/prosemark/app/` (use cases), `src/prosemark/ports/` (interfaces), `src/prosemark/adapters/` (implementations), `src/prosemark/cli/` (command interface). Tests organized in `tests/` with unit, contract, and integration subdirectories. All test files named by module path omitting root package name.

## Governance

This constitution supersedes all other development practices and conventions. All pull requests and code reviews MUST verify compliance with constitutional principles. Any complexity or architectural deviation MUST be explicitly justified in design documents. Amendment requires documentation of rationale, approval process, and migration plan for existing code. Use `CLAUDE.md` for runtime development guidance and detailed conventions.

**Version**: 1.0.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20

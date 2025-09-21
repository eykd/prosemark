<!--
Sync Impact Report:
- Version change: v1.0.0 → v1.1.0 (material enhancement to quality principles)
- Modified principles: Code Quality Standards (Principle IV) - strengthened with 100% requirements
- Added sections: Enhanced Development Workflow with non-negotiable quality gates
- Removed sections: None
- Templates requiring updates: ✅ plan-template.md version reference already current
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

### IV. Code Quality Standards (NON-NEGOTIABLE)
All Python code MUST achieve 100% compliance before any commit or task completion. Type checking MUST pass 100% via mypy with strict configuration. Linting MUST pass 100% via ruff with all enabled rules. All tests MUST pass 100% with no exceptions, skipped tests, or disabled validations. Type annotations are required for all functions and methods. Google Style docstrings MUST be provided for all public APIs. 100% test coverage is required for all source code under `src/`. These quality gates are absolute - no compromises, workarounds, or bypasses are permitted under any circumstances. Quality enforcement is automated through specialized agents and tooling to ensure consistent application.

### V. CLI-First Interface
Every feature MUST be accessible through simple CLI commands that map directly to use cases. Commands follow text in/out protocol: stdin/args → stdout, errors → stderr. Support both JSON and human-readable output formats. CLI provides the canonical interface with other interfaces (future GUI/web) built as adapters.

## Development Workflow

All development MUST follow the established quality pipeline with zero tolerance for quality failures: format code → fix linting → resolve typing → run tests → commit changes. The quality pipeline is enforced through specialized sub-agents (@python-linter-fixer, @python-mypy-error-fixer, @python-test-runner, @conventional-committer) that automatically ensure 100% compliance. No code or task may be marked complete until all quality checks pass completely. Linear issue tracking integrates with commits for project management. Emergency bypasses of quality gates are prohibited - if code cannot pass quality checks, it cannot be committed or deployed. Failed quality checks MUST be resolved immediately before any other work continues.

## File Organization

Project structure follows hexagonal architecture with clear separation: `src/prosemark/domain/` (core logic), `src/prosemark/app/` (use cases), `src/prosemark/ports/` (interfaces), `src/prosemark/adapters/` (implementations), `src/prosemark/cli/` (command interface). Tests organized in `tests/` with unit, contract, and integration subdirectories. All test files named by module path omitting root package name.

## Governance

This constitution supersedes all other development practices and conventions. All pull requests and code reviews MUST verify compliance with constitutional principles. Any complexity or architectural deviation MUST be explicitly justified in design documents. Amendment requires documentation of rationale, approval process, and migration plan for existing code. Use `CLAUDE.md` for runtime development guidance and detailed conventions.

**Version**: 1.1.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-21

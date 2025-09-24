# Tasks: Write-Only Freewriting Interface

**Input**: Design documents from `/specs/003-write-only-freewriting/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (as per plan.md structure)
- Hexagonal architecture: `src/prosemark/domain/`, `src/prosemark/ports/`, `src/prosemark/adapters/`

## Phase 3.1: Setup
- [x] T001 Create freewriting module structure in src/prosemark/freewriting/ with domain/, ports/, adapters/ subdirectories
- [x] T002 Add Textual dependency to pyproject.toml requirements
- [x] T003 [P] Configure mypy and ruff for freewriting module with 100% compliance requirements

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Ports)
- [x] T004 [P] Contract test for FreewriteServicePort in tests/contract/test_freewrite_service_port.py
- [x] T005 [P] Contract test for TUIAdapterPort in tests/contract/test_tui_adapter_port.py
- [x] T006 [P] Contract test for CLIAdapterPort in tests/contract/test_cli_adapter_port.py
- [x] T007 [P] Contract test for NodeServicePort in tests/contract/test_node_service_port.py
- [x] T008 [P] Contract test for FileSystemPort in tests/contract/test_file_system_port.py

### Integration Tests (User Scenarios)
- [x] T009 [P] Integration test for daily freewrite file creation in tests/integration/test_daily_freewrite.py
- [x] T010 [P] Integration test for node targeting in tests/integration/test_node_freewrite.py
- [x] T011 [P] Integration test for session with title in tests/integration/test_titled_session.py
- [x] T012 [P] Integration test for session with goals in tests/integration/test_goal_session.py
- [x] T013 [P] Integration test for error handling scenarios in tests/integration/test_error_handling.py
- [x] T014 [P] Integration test for multiple sessions same day in tests/integration/test_multiple_sessions.py

## Phase 3.3: Domain Models (ONLY after tests are failing)
- [x] T015 [P] FreewriteSession domain model in src/prosemark/freewriting/domain/models.py
- [x] T016 [P] SessionConfig domain model in src/prosemark/freewriting/domain/models.py
- [x] T017 [P] Domain exceptions hierarchy in src/prosemark/freewriting/domain/exceptions.py

## Phase 3.4: Port Interfaces (Domain Layer)
- [x] T018 [P] FreewriteServicePort interface in src/prosemark/freewriting/ports/freewrite_service.py
- [x] T019 [P] TUIAdapterPort interface in src/prosemark/freewriting/ports/tui_adapter.py
- [x] T020 [P] CLIAdapterPort interface in src/prosemark/freewriting/ports/cli_adapter.py
- [x] T021 [P] NodeServicePort interface in src/prosemark/freewriting/ports/node_service.py
- [x] T022 [P] FileSystemPort interface in src/prosemark/freewriting/ports/file_system.py

## Phase 3.5: Adapter Implementations
- [ ] T023 [P] FileSystem adapter implementation in src/prosemark/freewriting/adapters/file_system_adapter.py
- [ ] T024 [P] Node service adapter implementation in src/prosemark/freewriting/adapters/node_service_adapter.py
- [ ] T025 Freewrite service implementation in src/prosemark/freewriting/adapters/freewrite_service_adapter.py
- [ ] T026 Textual TUI adapter implementation in src/prosemark/freewriting/adapters/tui_adapter.py
- [ ] T027 Typer CLI adapter implementation in src/prosemark/freewriting/adapters/cli_adapter.py

## Phase 3.6: CLI Integration
- [ ] T028 Add "write" command to main CLI in src/prosemark/cli/commands/write.py
- [ ] T029 Wire dependency injection for freewriting adapters in src/prosemark/freewriting/container.py
- [ ] T030 CLI command registration in main prosemark entry point

## Phase 3.7: Polish & Validation
- [ ] T031 [P] Unit tests for domain models validation in tests/unit/test_freewrite_models.py
- [ ] T032 [P] Unit tests for filename generation logic in tests/unit/test_filename_utils.py
- [ ] T033 [P] Unit tests for word count calculation in tests/unit/test_word_count.py
- [ ] T034 Performance tests for TUI responsiveness in tests/performance/test_tui_performance.py
- [ ] T035 Run quickstart.md scenarios manually and verify all pass
- [ ] T036 [P] Add docstrings for all public APIs following Google style
- [ ] T037 Remove any TODO comments and verify no dead code exists

## Dependencies

### Sequential Dependencies
- Setup (T001-T003) → All other phases
- Contract tests (T004-T008) → All implementation phases
- Integration tests (T009-T014) → All implementation phases
- Domain models (T015-T017) → Port interfaces (T018-T022)
- Port interfaces (T018-T022) → Adapter implementations (T023-T027)
- Adapters (T023-T027) → CLI integration (T028-T030)
- CLI integration (T028-T030) → Polish (T031-T037)

### Within-Phase Dependencies
- T015, T016 → T017 (models before exceptions)
- T023, T024 → T025 (file/node adapters before service)
- T025 → T026, T027 (service before UI adapters)
- T028 → T029 → T030 (command → wiring → registration)

## Parallel Execution Examples

### Contract Tests (can run together)
```bash
Task: "Contract test for FreewriteServicePort in tests/contract/test_freewrite_service_port.py"
Task: "Contract test for TUIAdapterPort in tests/contract/test_tui_adapter_port.py"
Task: "Contract test for CLIAdapterPort in tests/contract/test_cli_adapter_port.py"
Task: "Contract test for NodeServicePort in tests/contract/test_node_service_port.py"
Task: "Contract test for FileSystemPort in tests/contract/test_file_system_port.py"
```

### Integration Tests (can run together)
```bash
Task: "Integration test for daily freewrite file creation in tests/integration/test_daily_freewrite.py"
Task: "Integration test for node targeting in tests/integration/test_node_freewrite.py"
Task: "Integration test for session with title in tests/integration/test_titled_session.py"
Task: "Integration test for session with goals in tests/integration/test_goal_session.py"
Task: "Integration test for error handling scenarios in tests/integration/test_error_handling.py"
Task: "Integration test for multiple sessions same day in tests/integration/test_multiple_sessions.py"
```

### Port Interfaces (can run together)
```bash
Task: "FreewriteServicePort interface in src/prosemark/freewriting/ports/freewrite_service.py"
Task: "TUIAdapterPort interface in src/prosemark/freewriting/ports/tui_adapter.py"
Task: "CLIAdapterPort interface in src/prosemark/freewriting/ports/cli_adapter.py"
Task: "NodeServicePort interface in src/prosemark/freewriting/ports/node_service.py"
Task: "FileSystemPort interface in src/prosemark/freewriting/ports/file_system.py"
```

### Independent Adapters (can run together)
```bash
Task: "FileSystem adapter implementation in src/prosemark/freewriting/adapters/file_system_adapter.py"
Task: "Node service adapter implementation in src/prosemark/freewriting/adapters/node_service_adapter.py"
```

### Unit Tests (can run together)
```bash
Task: "Unit tests for domain models validation in tests/unit/test_freewrite_models.py"
Task: "Unit tests for filename generation logic in tests/unit/test_filename_utils.py"
Task: "Unit tests for word count calculation in tests/unit/test_word_count.py"
Task: "Add docstrings for all public APIs following Google style"
```

## Constitutional Compliance Requirements

### Quality Gates (Applied to Every Task)
- **100% mypy compliance**: No type errors allowed
- **100% ruff compliance**: No linting violations allowed
- **100% test coverage**: All source code under src/ must have tests
- **TDD enforcement**: Tests must be written first and must fail before implementation

### Specialized Quality Agents
- **python-mypy-error-fixer**: Automatically run after each implementation task
- **python-linter-fixer**: Automatically run after each code change
- **python-test-runner**: Automatically run to ensure tests pass
- **conventional-committer**: Automatically create proper commit messages

### Architecture Compliance
- **Hexagonal architecture**: Domain logic isolated behind port interfaces
- **Plain text storage**: All data in Markdown files with YAML frontmatter
- **CLI-first interface**: Typer commands provide canonical interface
- **Test-first development**: All functionality covered by failing tests first

## Notes
- [P] tasks = different files, no dependencies within the parallelizable set
- Verify tests fail before implementing (critical for TDD compliance)
- Each task completion triggers automatic quality gate validation
- Commit after each task with conventional commit format
- No task can be marked complete until 100% quality compliance achieved
- Constitutional agents will automatically enforce compliance

## Manual Validation Checklist
After task completion, verify:
- [ ] All quickstart.md scenarios pass manually
- [ ] TUI displays correctly with 80/20 layout
- [ ] ENTER key appends content and clears input
- [ ] Daily files created with correct YYYY-MM-DD-HHmm.md naming
- [ ] Node files created/appended correctly with binder updates
- [ ] Word count and timer display updates in real-time
- [ ] Error messages appear in TUI without crashes
- [ ] All constitutional requirements verified (hexagonal arch, TDD, quality gates)

# Tasks: Materialize All Command Option

**Input**: Design documents from `/workspace/specs/002-materialize-all-the/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11, Typer framework, pytest testing
2. Load design documents:
   → data-model.md: 4 entities → 4 model tasks
   → contracts/: 2 files → multiple contract test tasks
   → research.md: Technical decisions → setup approach
3. Generate tasks by category:
   → Setup: Project configuration and quality gates
   → Tests: Contract tests (CLI and use case), integration tests
   → Core: Domain models, use case, CLI adapter
   → Integration: Placeholder discovery, error handling
   → Polish: Performance tests, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests? ✓
   → All entities have models? ✓
   → All quickstart scenarios covered? ✓
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/prosemark/` (existing PMK structure)
- **Tests**: `tests/` at repository root
- Domain: `src/prosemark/domain/`
- Application: `src/prosemark/app/`
- CLI: `src/prosemark/cli/`

## Phase 3.1: Setup
- [X] T001 Configure quality gates for new feature (mypy, ruff, pytest requirements)
- [X] T002 [P] Set up test fixtures for binder with placeholders in tests/fixtures/
- [X] T003 [P] Create test helper for batch materialization assertions in tests/helpers/

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [X] T004 [P] CLI contract test for --all flag validation in tests/contract/test_cli_materialize_all.py
- [X] T005 [P] CLI contract test for batch success response in tests/contract/test_cli_materialize_batch.py
- [X] T006 [P] CLI contract test for partial failure handling in tests/contract/test_cli_materialize_partial.py
- [X] T007 [P] CLI contract test for empty binder scenario in tests/contract/test_cli_materialize_empty.py
- [X] T008 [P] Use case contract test for MaterializeAllPlaceholders in tests/contract/test_use_case_materialize_all.py

### Integration Tests (from quickstart scenarios)
- [X] T009 [P] Integration test: basic bulk materialization (5 placeholders) in tests/integration/test_materialize_all_basic.py
- [X] T010 [P] Integration test: empty binder handling in tests/integration/test_materialize_all_empty.py
- [X] T011 [P] Integration test: partial failure resilience in tests/integration/test_materialize_all_partial.py
- [X] T012 [P] Integration test: command validation (mutual exclusion) in tests/integration/test_materialize_all_validation.py
- [X] T013 [P] Integration test: performance with 100+ placeholders in tests/integration/test_materialize_all_performance.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Domain Models
- [X] T014 [P] Create BatchMaterializeResult value object in src/prosemark/domain/batch_materialize_result.py
- [X] T015 [P] Create MaterializeResult value object in src/prosemark/domain/materialize_result.py
- [X] T016 [P] Create MaterializeFailure value object in src/prosemark/domain/materialize_failure.py
- [X] T017 [P] Create PlaceholderSummary value object in src/prosemark/domain/placeholder_summary.py

### Use Case Layer
- [X] T018 Create MaterializeAllPlaceholders use case in src/prosemark/app/materialize_all_placeholders.py
- [X] T019 Implement placeholder discovery logic (leverage AuditBinder patterns)
- [X] T020 Add batch materialization loop with error collection
- [X] T021 Implement progress reporting callback mechanism

### CLI Adapter
- [X] T022 Extend materialize command with --all flag in src/prosemark/cli/main.py
- [X] T023 Add mutual exclusion validation (title vs --all)
- [X] T024 Implement batch progress reporting to stdout
- [X] T025 Add comprehensive error handling and exit codes

## Phase 3.4: Integration

### Service Integration
- [X] T026 Wire MaterializeAllPlaceholders use case into dependency injection
- [X] T027 Connect to existing MaterializeNode use case for individual processing
- [X] T028 Integrate with BinderRepoFs for binder operations
- [X] T029 Connect to IdGeneratorUuid7 for node ID generation

### Error Handling
- [X] T030 Implement filesystem error recovery strategy
- [X] T031 Add binder integrity validation before batch operations
- [X] T032 Create detailed error reporting for partial failures

## Phase 3.5: Polish

### Additional Tests
- [ ] T033 [P] Unit tests for BatchMaterializeResult validation in tests/unit/test_batch_materialize_result.py
- [ ] T034 [P] Unit tests for placeholder discovery logic in tests/unit/test_placeholder_discovery.py
- [ ] T035 [P] Unit tests for error aggregation in tests/unit/test_error_aggregation.py

### Performance & Quality
- [ ] T036 Performance optimization for large binders (>500 placeholders)
- [ ] T037 Run quality gates: mypy, ruff, pytest with 100% compliance
- [ ] T038 [P] Update CLAUDE.md with new command usage examples

### Documentation
- [ ] T039 [P] Create user documentation for --all flag in docs/cli-reference.md
- [ ] T040 Run quickstart.md scenarios for final validation

## Dependencies
- Setup (T001-T003) can run immediately
- All tests (T004-T013) must complete before implementation
- Domain models (T014-T017) can run in parallel after tests
- Use case (T018-T021) requires domain models
- CLI adapter (T022-T025) requires use case
- Integration (T026-T032) requires CLI adapter
- Polish tasks (T033-T040) require all implementation complete

## Parallel Execution Examples

### Launch all contract tests together (Phase 3.2):
```
Task: "CLI contract test for --all flag validation in tests/contract/test_cli_materialize_all.py"
Task: "CLI contract test for batch success response in tests/contract/test_cli_materialize_batch.py"
Task: "CLI contract test for partial failure handling in tests/contract/test_cli_materialize_partial.py"
Task: "CLI contract test for empty binder scenario in tests/contract/test_cli_materialize_empty.py"
Task: "Use case contract test for MaterializeAllPlaceholders in tests/contract/test_use_case_materialize_all.py"
```

### Launch all integration tests together (Phase 3.2):
```
Task: "Integration test: basic bulk materialization in tests/integration/test_materialize_all_basic.py"
Task: "Integration test: empty binder handling in tests/integration/test_materialize_all_empty.py"
Task: "Integration test: partial failure resilience in tests/integration/test_materialize_all_partial.py"
Task: "Integration test: command validation in tests/integration/test_materialize_all_validation.py"
Task: "Integration test: performance with 100+ placeholders in tests/integration/test_materialize_all_performance.py"
```

### Launch all domain models together (Phase 3.3):
```
Task: "Create BatchMaterializeResult value object in src/prosemark/domain/batch_materialize_result.py"
Task: "Create MaterializeResult value object in src/prosemark/domain/materialize_result.py"
Task: "Create MaterializeFailure value object in src/prosemark/domain/materialize_failure.py"
Task: "Create PlaceholderSummary value object in src/prosemark/domain/placeholder_summary.py"
```

## Notes
- [P] tasks = different files, no dependencies
- CRITICAL: Verify all tests fail before implementing
- Run quality gates after each phase
- Commit after each task with conventional commit messages
- Avoid: vague tasks, same file conflicts, skipping tests

## Quality Gates per Phase
- **Phase 3.2**: All 10 tests written and confirmed failing
- **Phase 3.3**: Domain models and use case with 100% test coverage
- **Phase 3.4**: Integration complete, all contract tests passing
- **Phase 3.5**: 100% mypy, ruff, pytest compliance achieved

## Validation Checklist
*GATE: Checked before execution*

- [x] All contracts have corresponding tests (5 CLI, 1 use case)
- [x] All entities have model tasks (4 value objects)
- [x] All tests come before implementation (T004-T013 before T014+)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Quickstart scenarios covered (5 test scenarios → 5 integration tests)
- [x] Constitutional compliance verified (TDD, quality gates, hexagonal architecture)

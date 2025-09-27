# Tasks: Compile Binder Subtree

**Input**: Design documents from `/specs/004-compile-binder-subtree/`
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
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow hexagonal architecture in plan.md

## Phase 3.1: Setup
- [x] T001 Create compile module directories per implementation plan structure
- [x] T002 [P] Create __init__.py files for all new modules
- [x] T003 [P] Copy contract definitions to ports directory from specs

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [x] T004 [P] Write failing contract test for CompileServicePort in tests/contract/ports/compile/test_service_port.py
  - Test compile_subtree with valid request
  - Test error handling for non-existent node
  - Test include_empty option behavior

### Integration Tests
- [x] T005 [P] Write failing integration test for CLI compile command in tests/integration/cli/test_compile_command.py
  - Test Scenario 1: Simple hierarchy compilation
  - Test Scenario 2: Deep nesting compilation
  - Test Scenario 3: Empty nodes skipped
  - Test Scenario 4: Node not found error

### Unit Tests for Domain Logic
- [x] T006 [P] Write failing unit test for CompileService in tests/unit/domain/compile/test_service.py
  - Test depth-first traversal algorithm
  - Test content concatenation with double newlines
  - Test statistics calculation (node_count, skipped_empty)
  - Test streaming for large subtrees

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Domain Models
- [ ] T007 [P] Implement CompileRequest and CompileResult models in src/prosemark/domain/compile/models.py
  - CompileRequest with node_id and include_empty fields
  - CompileResult with content, node_count, total_nodes, skipped_empty
  - Validation rules per data-model.md

### Port Definitions
- [ ] T008 [P] Create CompileServicePort interface in src/prosemark/ports/compile/service.py
  - Abstract base class with compile_subtree method
  - NodeNotFoundError and CompileError exceptions
  - Type hints and docstrings

### Domain Service
- [ ] T009 Implement CompileService in src/prosemark/domain/compile/service.py
  - Depth-first pre-order traversal algorithm
  - Content aggregation with double newline separation
  - Skip empty nodes by default
  - Calculate statistics during traversal
  - Use generators for memory efficiency

### Use Cases
- [ ] T010 Implement CompileSubtreeUseCase in src/prosemark/app/compile/use_cases.py
  - Orchestrate domain service with repository ports
  - Validate node existence before compilation
  - Handle exceptions and return appropriate errors

### Adapter Implementation
- [ ] T011 Create CompileServiceAdapter implementing CompileServicePort
  - Delegate to CompileSubtreeUseCase
  - Use existing NodeRepo and BinderRepo ports
  - Map domain exceptions to port exceptions

### CLI Command
- [ ] T012 Implement compile CLI command in src/prosemark/cli/commands/compile.py
  - Add @app.command() decorator for Typer
  - Accept node_id as argument
  - Output plain text to stdout
  - Handle errors gracefully with proper exit codes

## Phase 3.4: Integration

### Wire Dependencies
- [ ] T013 Register CompileServiceAdapter in dependency injection container
- [ ] T014 Import and register compile command in main CLI app
- [ ] T015 Ensure compile service uses existing file system adapters

### Error Handling
- [ ] T016 Add proper error messages for user-facing exceptions
- [ ] T017 Add debug logging for traversal operations
- [ ] T018 Validate UUIDv7 format before processing

## Phase 3.5: Polish

### Quality Enforcement
- [ ] T019 [P] Run ruff and fix all linting issues in compile module
- [ ] T020 [P] Run mypy and fix all type checking issues in compile module
- [ ] T021 [P] Achieve 100% test coverage for compile module

### Performance Testing
- [ ] T022 Create performance test for 1000 node compilation
- [ ] T023 Optimize if not meeting <1 second target

### Documentation
- [ ] T024 [P] Add docstrings to all public methods in compile module
- [ ] T025 [P] Update CLI help text with compile command documentation
- [ ] T026 [P] Add compile command to main README.md

### Final Validation
- [ ] T027 Run all quickstart scenarios manually
- [ ] T028 Run full test suite with 100% pass rate
- [ ] T029 Commit changes with conventional commit message

## Dependencies
- Setup (T001-T003) must complete first
- Tests (T004-T006) before any implementation
- Domain models (T007) before service (T009)
- Port definition (T008) before adapter (T011)
- Service (T009) and use case (T010) before adapter (T011)
- Adapter (T011) before CLI command (T012)
- All implementation before integration (T013-T018)
- All integration before polish (T019-T029)

## Parallel Execution Examples

### Phase 3.2 - All tests in parallel:
```bash
# Launch T004-T006 together (different test files):
Task: "Write failing contract test for CompileServicePort in tests/contract/ports/compile/test_service_port.py"
Task: "Write failing integration test for CLI compile command in tests/integration/cli/test_compile_command.py"
Task: "Write failing unit test for CompileService in tests/unit/domain/compile/test_service.py"
```

### Phase 3.3 - Independent implementations:
```bash
# Launch T007-T008 together (different module files):
Task: "Implement CompileRequest and CompileResult models in src/prosemark/domain/compile/models.py"
Task: "Create CompileServicePort interface in src/prosemark/ports/compile/service.py"
```

### Phase 3.5 - Quality checks in parallel:
```bash
# Launch T019-T021 together (independent quality tools):
Task: "Run ruff and fix all linting issues in compile module"
Task: "Run mypy and fix all type checking issues in compile module"
Task: "Achieve 100% test coverage for compile module"
```

## Notes
- Follow TDD strictly: tests must fail before implementation
- Use existing NodeRepo and BinderRepo - do not recreate
- Maintain hexagonal architecture boundaries
- Each task modifies distinct files to enable parallelism
- Commit after each phase for easy rollback

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T004)
- [x] All entities have model tasks (T007)
- [x] All tests come before implementation (T004-T006 before T007-T012)
- [x] Parallel tasks truly independent (verified file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

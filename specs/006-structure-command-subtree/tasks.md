# Tasks: Structure Command Subtree Display

**Input**: Design documents from `/specs/006-structure-command-subtree/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.13, Typer CLI, existing ShowStructure use case
2. Load optional design documents:
   → data-model.md: NodeId entity (existing)
   → contracts/cli-interface.md: CLI command signature
   → quickstart.md: 5 test scenarios
3. Generate tasks by category:
   → Tests: Unit and integration tests (TDD first)
   → Core: Add node_id argument to Typer CLI
   → Polish: Quality gates (mypy, ruff, pytest)
4. Apply task rules:
   → Tests can run in parallel [P] (different files)
   → Implementation is single file change (sequential)
   → Quality gates run after implementation
5. Number tasks sequentially (T001, T002...)
6. Validate task completeness:
   → All test scenarios covered
   → CLI integration complete
   → Quality gates pass 100%
7. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/prosemark/`, `tests/` at repository root
- All paths shown are absolute from repository root

## Phase 3.1: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.2
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Unit Tests
- [x] T001 [P] Write unit test for structure command with valid node_id in tests/unit/cli/test_structure.py
- [x] T002 [P] Write unit test for structure command with invalid UUID format in tests/unit/cli/test_structure.py
- [x] T003 [P] Write unit test for structure command with non-existent node_id in tests/unit/cli/test_structure.py
- [x] T004 [P] Write unit test for structure command with leaf node (no children) in tests/unit/cli/test_structure.py

### Integration Tests
- [x] T005 [P] Write integration test for full tree display (backward compatibility) in tests/integration/cli/test_structure_integration.py
- [x] T006 [P] Write integration test for subtree display with valid node_id in tests/integration/cli/test_structure_integration.py
- [x] T007 [P] Write integration test for JSON format output with node_id in tests/integration/cli/test_structure_integration.py
- [x] T008 [P] Write integration test for error handling (invalid/missing nodes) in tests/integration/cli/test_structure_integration.py

### Contract Tests
- [x] T009 [P] Write contract test for CLI interface with node_id parameter in tests/contract/cli/test_structure_contract.py

## Phase 3.2: Core Implementation (ONLY after tests are failing)
**NOTE: Minimal change required - ShowStructure.execute() already supports node_id**

- [x] T010 Add node_id argument to structure command in src/prosemark/cli/main.py (Annotated[str | None, typer.Argument()])
- [x] T011 Parse and validate node_id using NodeId class if provided in src/prosemark/cli/main.py
- [x] T012 Pass node_id parameter to ShowStructure.execute() in src/prosemark/cli/main.py
- [x] T013 Update docstring for structure command to mention NODE_ID parameter in src/prosemark/cli/main.py

## Phase 3.3: Quality Gates
**CRITICAL: Must achieve 100% compliance per constitution**

- [ ] T014 Run pytest and ensure all tests pass with 100% coverage
- [ ] T015 Run mypy src/ and fix any type checking issues (must be 100% clean)
- [ ] T016 Run ruff check src/ and fix any linting issues (must be 100% clean)
- [ ] T017 Run ruff format src/ to ensure consistent formatting

## Phase 3.4: Validation
- [ ] T018 Test all scenarios from quickstart.md manually with real binder file
- [ ] T019 Verify backward compatibility - existing scripts still work
- [ ] T020 Update CLI help text if needed to show NODE_ID argument

## Dependencies
- Tests (T001-T009) must ALL be written and failing before implementation (T010-T013)
- T010-T013 are sequential (same file: src/prosemark/cli/main.py)
- T014-T017 can only run after implementation is complete
- T018-T020 are final validation steps

## Parallel Execution Examples

### Phase 3.1: Launch all tests together
```bash
# All test files are independent, can write in parallel:
@Task: "Write unit tests for structure command in tests/unit/cli/test_structure.py"
@Task: "Write integration tests in tests/integration/cli/test_structure_integration.py"
@Task: "Write contract test in tests/contract/cli/test_structure_contract.py"
```

### Phase 3.2: Sequential implementation
```bash
# Single file change, must be sequential:
# First add argument, then validate, then pass to execute(), then update docs
```

### Phase 3.3: Quality gates
```bash
# Run sequentially to fix issues incrementally:
# pytest → mypy → ruff check → ruff format
```

## Notes
- Feature is 90% implemented - domain/app layers already support node_id
- Only need to wire up Typer CLI argument to existing use case
- Follow TDD strictly: tests must fail before implementation
- Maintain backward compatibility (optional argument)
- Use existing NodeId value object for validation
- Use existing error handling patterns (NodeNotFoundError, NodeIdentityError)

## Validation Checklist
*GATE: Checked before marking tasks complete*

- [x] All test scenarios from quickstart.md covered
- [x] Tests come before implementation (TDD)
- [x] Parallel tasks are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] tasks modify same file
- [x] Implementation leverages existing ShowStructure.execute(node_id)
- [x] Quality gates ensure 100% compliance

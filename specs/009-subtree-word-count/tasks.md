# Tasks: Subtree Word Count

**Input**: Design documents from `/workspace/specs/009-subtree-word-count/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Loaded - Python 3.13, hexagonal architecture, TDD workflow
2. Load design documents:
   → ✅ data-model.md: WordCountRequest, WordCountResult, WordCounterPort
   → ✅ contracts/: wordcount_port.py with 40+ test scenarios
   → ✅ research.md: Regex-based algorithm, reuse compile infrastructure
   → ✅ quickstart.md: 10 integration test scenarios
3. Generate tasks by category:
   → Setup, Tests (TDD), Core (models, services, adapters), CLI, Polish
4. Apply task rules:
   → Different files = [P] for parallel execution
   → Tests before implementation (strict TDD)
5. Number tasks sequentially (T001-T025)
6. ✅ Validation complete: All contracts tested, all entities modeled, TDD order enforced
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute from `/workspace/`

## Path Conventions
Single project (hexagonal architecture):
- **Domain**: `src/prosemark/domain/wordcount/`
- **Ports**: `src/prosemark/ports/wordcount/`
- **Adapters**: `src/prosemark/adapters/wordcount/`
- **Use Cases**: `src/prosemark/app/wordcount/`
- **CLI**: `src/prosemark/cli/`
- **Tests**: `tests/{unit,contract,integration}/wordcount/`

---

## Phase 3.1: Setup & Directory Structure

### T001: Create wordcount module directories
**Status**: ✅ Completed
**Files**:
- Create `src/prosemark/domain/wordcount/__init__.py`
- Create `src/prosemark/ports/wordcount/__init__.py`
- Create `src/prosemark/adapters/wordcount/__init__.py`
- Create `src/prosemark/app/wordcount/__init__.py`
- Create `tests/unit/wordcount/`
- Create `tests/contract/wordcount/`
- Create `tests/integration/wordcount/`

**Acceptance**: All directories exist with empty `__init__.py` files where needed

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL**: These tests MUST be written first and MUST FAIL before ANY implementation.

### T002 [P]: Contract test for WordCounterPort
**Status**: ✅ Completed
**File**: `tests/contract/wordcount/test_wordcount_port.py`
**Description**: Write contract tests for WordCounterPort using CONTRACT_SCENARIOS from `contracts/wordcount_port.py`. Test all 40+ scenarios including:
- Basic scenarios (hello world, empty string, single word)
- Contractions (don't, it's, won't)
- Hyphens (well-known, state-of-the-art)
- Numbers (123, 3.14, multiple numbers)
- URLs (https://example.com)
- Emails (user@example.com)
- Whitespace normalization
- Punctuation handling
- Em-dashes and en-dashes
- Edge cases (punctuation only, multi-dot numbers)

**Test Strategy**: Parametrize test using CONTRACT_SCENARIOS list. Test must fail (no implementation yet).

**Acceptance**: Test file exists, imports CONTRACT_SCENARIOS, all scenarios parametrized, tests FAIL

---

### T003 [P]: Unit test for WordCountRequest model
**Status**: ✅ Completed
**File**: `tests/unit/wordcount/test_models_request.py`
**Description**: Write unit tests for WordCountRequest model:
- Test creation with NodeId
- Test creation with None (all roots)
- Test include_empty parameter (True/False)
- Test immutability (frozen dataclass)
- Test type validation

**Acceptance**: Test file exists, covers all model attributes, tests FAIL

---

### T004 [P]: Unit test for WordCountResult model
**Status**: ✅ Completed
**File**: `tests/unit/wordcount/test_models_result.py`
**Description**: Write unit tests for WordCountResult model:
- Test creation with count and content
- Test non-negative count validation
- Test immutability (frozen dataclass)
- Test various content types (empty, large)

**Acceptance**: Test file exists, covers all model attributes, tests FAIL

---

### T005 [P]: Unit test for WordCountService
**Status**: ✅ Completed
**File**: `tests/unit/wordcount/test_service.py`
**Description**: Write unit tests for WordCountService:
- Test dependency injection (mock WordCounterPort)
- Test count_text() delegates to counter
- Test result construction (count + content)
- Test with various text inputs

**Acceptance**: Test file exists, uses mock counter, tests FAIL

---

### T006 [P]: Unit test for StandardWordCounter adapter
**Status**: ✅ Completed
**File**: `tests/unit/wordcount/test_counter_standard.py`
**Description**: Write unit tests for StandardWordCounter implementation:
- Test regex patterns for each word type
- Test URL/email preservation
- Test contraction handling
- Test hyphen handling
- Test number handling
- Test whitespace normalization
- Test edge cases (empty, whitespace-only, unicode)

**Acceptance**: Test file exists, comprehensive regex pattern tests, tests FAIL

---

### T007 [P]: Unit test for WordCountUseCase
**Status**: ✅ Completed
**File**: `tests/unit/wordcount/test_use_case.py`
**Description**: Write unit tests for WordCountUseCase:
- Test dependency injection (mock CompileSubtreeUseCase, mock WordCountService)
- Test count_words() with node_id
- Test count_words() without node_id (all roots)
- Test compile request construction
- Test error propagation from compile layer
- Test result construction

**Acceptance**: Test file exists, uses mocks, tests FAIL

---

### T008 [P]: Integration test - basic word count (scenario 1)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_basic.py`
**Description**: Integration test for quickstart scenario 1 (basic single node):
- Create test project with node containing "Hello world"
- Run `pmk wc <node-id>`
- Assert output is `2`
- Assert exit code 0
- Assert no stderr output

**Acceptance**: Test file exists, creates test data, runs CLI command, tests FAIL

---

### T009 [P]: Integration test - subtree word count (scenario 2)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_subtree.py`
**Description**: Integration test for quickstart scenario 2 (parent + children):
- Create parent node with "Chapter introduction" (2 words)
- Create child A with "First scene content" (3 words)
- Create child B with "Second scene content" (3 words)
- Run `pmk wc <parent-id>`
- Assert output is `8`

**Acceptance**: Test file exists, creates node hierarchy, tests FAIL

---

### T010 [P]: Integration test - all root nodes (scenario 3)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_all_roots.py`
**Description**: Integration test for quickstart scenario 3 (no argument):
- Create multiple root nodes with known word counts
- Run `pmk wc` (no node ID)
- Assert output sums all root nodes

**Acceptance**: Test file exists, creates multiple roots, tests FAIL

---

### T011 [P]: Integration test - contractions and hyphens (scenario 4)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_grammar.py`
**Description**: Integration test for quickstart scenario 4 (US English rules):
- Create node with "I don't think it's a well-known fact."
- Run `pmk wc <node-id>`
- Assert output is `7` (don't=1, it's=1, well-known=1)

**Acceptance**: Test file exists, verifies contraction/hyphen handling, tests FAIL

---

### T012 [P]: Integration test - numbers, URLs, emails (scenario 5)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_special_tokens.py`
**Description**: Integration test for quickstart scenario 5 (special tokens):
- Create node with "There are 123 items at https://example.com or email user@example.com"
- Run `pmk wc <node-id>`
- Assert output is `9`

**Acceptance**: Test file exists, verifies special token handling, tests FAIL

---

### T013 [P]: Integration test - empty node (scenario 6)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_empty.py`
**Description**: Integration test for quickstart scenario 6 (empty content):
- Create empty node (no content)
- Run `pmk wc <node-id>`
- Assert output is `0`
- Assert exit code 0 (success, not error)

**Acceptance**: Test file exists, handles empty content, tests FAIL

---

### T014 [P]: Integration test - invalid node ID (scenario 7)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_not_found.py`
**Description**: Integration test for quickstart scenario 7 (non-existent node):
- Run `pmk wc "01JXXXXXXXXXXXXXXXXXXXXX"` (valid format, doesn't exist)
- Assert stdout is `0`
- Assert stderr contains "Error: Node not found"
- Assert exit code 1

**Acceptance**: Test file exists, captures stdout/stderr separately, tests FAIL

---

### T015 [P]: Integration test - invalid UUID format (scenario 8)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_invalid_format.py`
**Description**: Integration test for quickstart scenario 8 (invalid format):
- Run `pmk wc "not-a-uuid"`
- Assert stdout is `0`
- Assert stderr contains "Error: Invalid node ID format"
- Assert exit code 1

**Acceptance**: Test file exists, validates error handling, tests FAIL

---

### T016 [P]: Integration test - whitespace normalization (scenario 10)
**Status**: ✅ Completed
**File**: `tests/integration/wordcount/test_wc_whitespace.py`
**Description**: Integration test for quickstart scenario 10 (whitespace):
- Create node with "word  \n\n  word" (literal multiple spaces and newlines)
- Run `pmk wc <node-id>`
- Assert output is `2`

**Acceptance**: Test file exists, tests whitespace handling, tests FAIL

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### T017 [P]: Implement WordCountRequest and WordCountResult models
**Status**: ✅ Completed
**File**: `src/prosemark/domain/wordcount/models.py`
**Description**: Implement domain models per data-model.md:
- WordCountRequest: frozen dataclass with node_id (NodeId | None), include_empty (bool)
- WordCountResult: frozen dataclass with count (int), content (str)
- Add Google-style docstrings
- Add type hints
- Import from prosemark.domain.models (NodeId)

**Dependencies**: None (pure data structures)
**Acceptance**: Tests T003, T004 PASS, mypy passes, ruff passes

---

### T018: Implement WordCounterPort protocol
**Status**: ✅ Completed
**File**: `src/prosemark/ports/wordcount/counter.py`
**Description**: Implement port interface per contracts/wordcount_port.py:
- Define WordCounterPort Protocol with count_words(text: str) -> int
- Add comprehensive docstring with rules (contractions, hyphens, URLs, emails, numbers)
- Add examples in docstring
- Import typing.Protocol

**Dependencies**: None (protocol definition)
**Acceptance**: File exists, protocol defined, mypy passes

---

### T019: Implement StandardWordCounter adapter
**Status**: ✅ Completed
**File**: `src/prosemark/adapters/wordcount/counter_standard.py`
**Description**: Implement regex-based word counter per research.md algorithm:
- Implement count_words() method
- Regex patterns for:
  - URL preservation: `https?://[^\s]+`
  - Email preservation: `[^\s@]+@[^\s@]+`
  - Whitespace split: `\s+`
  - Token filtering (remove punctuation, keep hyphens/apostrophes in words)
- Handle contractions (keep apostrophes)
- Handle hyphens in compounds
- Handle numbers (including decimals)
- Return non-negative int

**Dependencies**: T018 (port interface)
**Acceptance**: Tests T002, T006 PASS (all contract scenarios), mypy passes, ruff passes

---

### T020: Implement WordCountService
**Status**: ✅ Completed
**File**: `src/prosemark/domain/wordcount/service.py`
**Description**: Implement domain service per data-model.md:
- __init__(counter: WordCounterPort) - dependency injection
- count_text(text: str) -> WordCountResult
- Delegate counting to self._counter.count_words()
- Construct WordCountResult with count and content
- Add docstrings

**Dependencies**: T017 (models), T018 (port)
**Acceptance**: Tests T005 PASS, pure domain logic (no I/O), mypy passes, ruff passes

---

### T021: Implement WordCountUseCase
**Status**: ✅ Completed
**File**: `src/prosemark/app/wordcount/use_cases.py`
**Description**: Implement use case orchestration per plan.md:
- __init__(compile_use_case: CompileSubtreeUseCase, word_count_service: WordCountService)
- count_words(request: WordCountRequest) -> WordCountResult
- Create CompileRequest from WordCountRequest
- Call compile_use_case.compile_subtree()
- Call word_count_service.count_text() with compiled content
- Handle errors (propagate NodeNotFoundError, CompileNodeNotFoundError)
- Add docstrings

**Dependencies**: T017 (models), T020 (service), existing CompileSubtreeUseCase
**Acceptance**: Tests T007 PASS, orchestrates dependencies correctly, mypy passes

---

### T022: Implement CLI wc command
**Status**: ✅ Completed
**File**: `src/prosemark/cli/wc.py`
**Description**: Implement CLI command per plan.md and compile.py pattern:
- wc_command(node_id: str | None, path: Path | None) function
- Wire dependencies: ClockSystem, EditorLauncherSystem, NodeRepoFs, BinderRepoFs
- Create CompileSubtreeUseCase, WordCountService, StandardWordCounter
- Create WordCountUseCase
- Construct WordCountRequest
- Handle optional node_id (None for all roots, validate format if provided)
- Execute use case
- Output count to stdout (plain number, no labels): `typer.echo(result.count)`
- Error handling:
  - Invalid node ID format → stderr "Error: Invalid node ID format: {id}", stdout "0", exit 1
  - Node not found → stderr "Error: Node not found: {id}", stdout "0", exit 1
  - Compilation failure → stderr "Error: Compilation failed: {e}", stdout "0", exit 1
- Add docstring matching compile command style

**Dependencies**: T019 (adapter), T020 (service), T021 (use case)
**Acceptance**: Tests T008-T016 PASS, command works end-to-end, error handling correct

---

### T023: Register wc command in CLI main
**Status**: ✅ Completed
**File**: `src/prosemark/cli/main.py`
**Description**: Register wc_command in main CLI app:
- Import wc_command from prosemark.cli.wc
- Add command registration (follow pattern from compile command)
- Verify command appears in `pmk --help`

**Dependencies**: T022 (CLI command exists)
**Acceptance**: `pmk wc --help` works, command is discoverable

---

## Phase 3.4: Polish & Quality

### T024 [P]: Run python-linter-fixer agent
**Status**: ✅ Completed
**Description**: Fix all ruff linting violations in wordcount modules:
- Run ruff on all new files
- Fix formatting issues
- Fix import order
- Fix docstring issues
- Verify 100% ruff compliance

**Command**: Launch python-linter-fixer agent for wordcount modules
**Acceptance**: `uv run ruff check src/prosemark/*/wordcount/ tests/*/wordcount/` passes 100%

---

### T025 [P]: Run python-mypy-error-fixer agent
**Status**: ✅ Completed
**Description**: Fix all mypy type checking errors in wordcount modules:
- Run mypy strict mode on all new files
- Fix type annotation issues
- Fix protocol compliance
- Verify 100% mypy compliance

**Command**: Launch python-mypy-error-fixer agent for wordcount modules
**Acceptance**: `uv run mypy src/prosemark/*/wordcount/` passes 100% strict

---

### T026 [P]: Verify 100% test coverage
**Status**: ✅ Completed
**Description**: Ensure 100% code coverage for wordcount modules:
- Run pytest with coverage for wordcount modules
- Identify any uncovered lines
- Add tests or mark lines with `# pragma: no cover` if untestable
- Verify coverage report shows 100%

**Command**: `uv run pytest --cov=src/prosemark/domain/wordcount --cov=src/prosemark/ports/wordcount --cov=src/prosemark/adapters/wordcount --cov=src/prosemark/app/wordcount --cov=src/prosemark/cli/wc --cov-report=term-missing`
**Acceptance**: Coverage report shows 100% for all wordcount modules

---

### T027: Run python-test-runner agent
**Status**: ✅ Completed
**Description**: Run all tests and fix any failures:
- Run full test suite
- Fix any failing tests
- Ensure all wordcount tests pass
- Verify no regressions in existing tests

**Command**: Launch python-test-runner agent for wordcount tests
**Acceptance**: All tests pass, no failures, no skipped tests

---

### T028 [P]: Manual quickstart validation
**Status**: ✅ Completed
**Description**: Execute quickstart.md manually to validate user experience:
- Follow all 10 test scenarios manually
- Verify outputs match expectations
- Check error messages are clear
- Confirm scriptable integration works
- Document any discrepancies

**Reference**: `/workspace/specs/009-subtree-word-count/quickstart.md`
**Acceptance**: All quickstart scenarios pass manually, user experience is smooth

---

## Dependencies Graph

```
Setup:
  T001 (directories)

Tests (TDD - must fail before implementation):
  T002 [P] ─┐
  T003 [P] ─┤
  T004 [P] ─┤
  T005 [P] ─┤  All independent (different files)
  T006 [P] ─┤
  T007 [P] ─┤
  T008 [P] ─┤
  T009 [P] ─┤
  T010 [P] ─┤
  T011 [P] ─┤
  T012 [P] ─┤
  T013 [P] ─┤
  T014 [P] ─┤
  T015 [P] ─┤
  T016 [P] ─┘

Implementation (only after tests fail):
  T017 [P] ─┬─→ T020 ─→ T021 ─→ T022 ─→ T023
  T018 ─────┴─→ T019 ─┘

Polish (after implementation):
  T024 [P] ─┐
  T025 [P] ─┤  All independent quality checks
  T026 [P] ─┘
  T027 (runs all tests)
  T028 [P] (manual validation)
```

**Critical Path**: T001 → Tests (T002-T016) → T017,T018 → T019,T020 → T021 → T022 → T023 → Quality (T024-T028)

---

## Parallel Execution Examples

### Example 1: Run all contract/unit tests in parallel (Phase 3.2)
```python
# After T001 completes, launch all test tasks together:
tasks = [
    "Contract test WordCounterPort in tests/contract/wordcount/test_wordcount_port.py",
    "Unit test WordCountRequest in tests/unit/wordcount/test_models_request.py",
    "Unit test WordCountResult in tests/unit/wordcount/test_models_result.py",
    "Unit test WordCountService in tests/unit/wordcount/test_service.py",
    "Unit test StandardWordCounter in tests/unit/wordcount/test_counter_standard.py",
    "Unit test WordCountUseCase in tests/unit/wordcount/test_use_case.py",
]
# Execute concurrently - different files, no dependencies
```

### Example 2: Run all integration tests in parallel
```python
# After T001, launch all integration tests together:
integration_tests = [
    "Integration test basic word count (scenario 1)",
    "Integration test subtree word count (scenario 2)",
    "Integration test all root nodes (scenario 3)",
    "Integration test contractions/hyphens (scenario 4)",
    "Integration test special tokens (scenario 5)",
    "Integration test empty node (scenario 6)",
    "Integration test invalid node ID (scenario 7)",
    "Integration test invalid UUID format (scenario 8)",
    "Integration test whitespace normalization (scenario 10)",
]
# Execute concurrently - different test files
```

### Example 3: Run quality gates in parallel (Phase 3.4)
```python
# After T023 completes, run quality checks together:
quality_tasks = [
    "Run python-linter-fixer agent for wordcount modules",
    "Run python-mypy-error-fixer agent for wordcount modules",
    "Verify 100% test coverage for wordcount modules",
    "Manual quickstart validation",
]
# Execute concurrently - independent quality checks
```

---

## Task Execution Notes

### TDD Discipline
- **MUST** write tests first (T002-T016)
- **MUST** verify tests fail before implementation
- **MUST** run tests after each implementation task
- **NEVER** skip tests or disable failing tests

### Quality Gates (Constitutional Requirements)
- **100% mypy compliance** - strict mode, no errors
- **100% ruff compliance** - all rules enabled
- **100% test coverage** - no uncovered lines (except pragmas)
- **All tests passing** - no failures, no skipped tests

### Error Handling Pattern (from compile.py)
```python
try:
    # Execute operation
    result = use_case.count_words(request)
    typer.echo(result.count)  # Plain number to stdout
except NodeNotFoundError:
    typer.echo(f"Error: Node not found: {node_id}", err=True)
    typer.echo("0")  # 0 to stdout for scriptability
    raise typer.Exit(1)
except Exception as e:
    typer.echo(f"Error: Compilation failed: {e}", err=True)
    typer.echo("0")
    raise typer.Exit(1)
```

### File Naming Conventions
- **Models**: `models.py` (multiple models in one file)
- **Services**: `service.py` (one service per file)
- **Ports**: `counter.py` (port interface)
- **Adapters**: `counter_standard.py` (implementation name)
- **Use Cases**: `use_cases.py` (can have multiple use cases)
- **CLI**: `wc.py` (command name)
- **Tests**: `test_<module>.py` or `test_<scenario>.py`

---

## Validation Checklist

- [x] All contracts have corresponding tests (T002 covers wordcount_port.py)
- [x] All entities have model tasks (T017 creates WordCountRequest, WordCountResult)
- [x] All tests come before implementation (T002-T016 before T017-T023)
- [x] Parallel tasks are truly independent (verified: different files, no shared state)
- [x] Each task specifies exact file path (all file paths included)
- [x] No task modifies same file as another [P] task (verified: all [P] tasks use different files)
- [x] TDD order enforced (tests → implementation → quality)
- [x] Quality gates included (T024-T027)
- [x] Integration tests cover all quickstart scenarios (T008-T016)

---

## Success Criteria

Feature is complete when:
- ✅ All 28 tasks completed
- ✅ All tests passing (unit, contract, integration)
- ✅ 100% mypy compliance (strict mode)
- ✅ 100% ruff compliance
- ✅ 100% test coverage
- ✅ `pmk wc` command works as specified
- ✅ All quickstart scenarios pass manually
- ✅ Error handling matches compile command patterns
- ✅ Output is plain number to stdout (scriptable)

---

**Next Step**: Execute tasks in order, starting with T001 (directory creation).

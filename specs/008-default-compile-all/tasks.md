# Tasks: Optional Node ID for Compile Command

**Feature**: 008-default-compile-all
**Branch**: `008-default-compile-all`
**Input**: Design documents from `/workspace/specs/008-default-compile-all/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Flow (main)
```
1. Load plan.md from feature directory ✅
   → Tech stack: Python 3.13, typer, hexagonal architecture
   → Structure: Single project (src/, tests/)
2. Load design documents ✅
   → data-model.md: CompileRequest entity modified
   → contracts/: 2 contracts defined (CLI, Binder)
   → quickstart.md: 7 validation scenarios
3. Generate tasks by category ✅
   → Setup: Environment verification
   → Tests: 2 contract tests, 4 integration tests
   → Core: Domain model, use case, CLI modifications
   → Verification: Quality gates
4. Apply task rules ✅
   → Contract tests marked [P] (different files)
   → Integration tests marked [P] (different files)
   → Implementation tasks sequential (dependencies)
5. Number tasks sequentially (T001-T016) ✅
6. Dependencies identified and documented ✅
7. Parallel execution examples provided ✅
8. Validation complete ✅
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All paths are absolute from `/workspace/`

## Path Conventions
- **Project Type**: Single Python CLI project
- **Source**: `/workspace/src/prosemark/`
- **Tests**: `/workspace/tests/`
- **Specs**: `/workspace/specs/008-default-compile-all/`

---

## Phase 3.1: Setup & Verification

### T001: Verify Environment and Dependencies ✅
**File**: N/A (environment check)
**Description**: Verify Python 3.13, pytest, mypy, ruff are installed and working. Confirm existing compile functionality passes all tests.
**Commands**:
```bash
python --version  # Should be 3.13+
pytest tests/integration/compile/ -v  # Existing tests should pass
mypy src/prosemark/domain/compile/ --strict
ruff check src/prosemark/domain/compile/
```
**Success Criteria**: All existing compile tests pass, type checking clean, linting clean

---

## Phase 3.2: Contract Tests (TDD) ✅ COMPLETE

**CRITICAL**: These tests MUST be written first and MUST FAIL before ANY implementation begins.

### T002 [P]: Contract Test - CompileRequest Optional Node ID ✅
**File**: `/workspace/tests/contract/compile/test_compile_request_optional_node_id.py`
**Description**: Write contract tests verifying CompileRequest accepts both NodeId and None for node_id field.
**Test Cases**:
```python
def test_compile_request_accepts_node_id():
    """CompileRequest accepts NodeId for node_id."""
    node_id = NodeId.generate()
    request = CompileRequest(node_id=node_id, include_empty=False)
    assert request.node_id == node_id

def test_compile_request_accepts_none():
    """CompileRequest accepts None for node_id."""
    request = CompileRequest(node_id=None, include_empty=False)
    assert request.node_id is None

def test_compile_request_is_frozen():
    """CompileRequest is immutable."""
    request = CompileRequest(node_id=None, include_empty=False)
    with pytest.raises(FrozenInstanceError):
        request.node_id = NodeId.generate()
```
**Success Criteria**: Tests written, tests FAIL (CompileRequest.node_id not optional yet)

---

### T003 [P]: Contract Test - Binder Roots Iteration ✅
**File**: `/workspace/tests/contract/compile/test_binder_roots_iteration.py`
**Description**: Write contract tests verifying Binder.roots iteration and materialized node filtering.
**Test Cases**:
```python
def test_binder_roots_returns_list():
    """Binder.roots returns list of BinderItems."""
    binder = Binder(roots=[])
    assert isinstance(binder.roots, list)

def test_empty_binder_filter_returns_empty():
    """Filtering empty binder returns empty list."""
    binder = Binder(roots=[])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == []

def test_all_placeholders_filter_returns_empty():
    """Filtering all-placeholder binder returns empty list."""
    binder = Binder(roots=[
        BinderItem(display_title="P1", node_id=None),
        BinderItem(display_title="P2", node_id=None),
    ])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == []

def test_filter_preserves_order():
    """Filtering maintains binder order for materialized nodes."""
    id1, id2 = NodeId.generate(), NodeId.generate()
    binder = Binder(roots=[
        BinderItem(display_title="P", node_id=None),
        BinderItem(display_title="M1", node_id=id1),
        BinderItem(display_title="P2", node_id=None),
        BinderItem(display_title="M2", node_id=id2),
    ])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == [id1, id2]
```
**Success Criteria**: Tests written, tests PASS (no domain changes needed, existing Binder already works)

---

## Phase 3.3: Integration Tests (TDD) ✅ COMPLETE

**CRITICAL**: Write these integration tests before implementing use case changes.

### T004 [P]: Integration Test - Compile All Roots ✅
**File**: `/workspace/tests/integration/compile/test_compile_all_roots.py`
**Description**: Write integration test for compiling all materialized root nodes without providing node_id.
**Test Scenario** (from quickstart.md Scenario 1):
```python
def test_compile_all_roots_with_three_roots(tmp_path):
    """Compile all roots when no node_id provided."""
    # Setup: Create project with 3 root nodes
    create_test_binder(tmp_path, roots=["root1", "root2", "root3"])
    create_test_node(tmp_path / "root1.md", content="Chapter 1 content")
    create_test_node(tmp_path / "root2.md", content="Chapter 2 content")
    create_test_node(tmp_path / "root3.md", content="Chapter 3 content")

    # Execute: Compile without node_id
    runner = CliRunner()
    result = runner.invoke(cli, ["compile", "--path", str(tmp_path)])

    # Verify: All roots compiled, double newline separators
    assert result.exit_code == 0
    assert "Chapter 1 content" in result.output
    assert "Chapter 2 content" in result.output
    assert "Chapter 3 content" in result.output
    # Verify ordering: root1 before root2 before root3
    pos1 = result.output.find("Chapter 1")
    pos2 = result.output.find("Chapter 2")
    pos3 = result.output.find("Chapter 3")
    assert pos1 < pos2 < pos3
```
**Success Criteria**: Test written, test FAILS (multi-root compilation not implemented yet) ✅

---

### T005 [P]: Integration Test - Empty Binder Handling ✅
**File**: `/workspace/tests/integration/compile/test_compile_empty_binder.py`
**Description**: Write integration test for empty binder (no materialized roots).
**Test Scenario** (from quickstart.md Scenario 2):
```python
def test_compile_empty_binder_silent_success(tmp_path):
    """Empty binder produces empty output with exit code 0."""
    # Setup: Create binder with no roots
    create_test_binder(tmp_path, roots=[])

    # Execute: Compile without node_id
    runner = CliRunner()
    result = runner.invoke(cli, ["compile", "--path", str(tmp_path)])

    # Verify: Empty output, exit 0, no error
    assert result.exit_code == 0
    assert result.output.strip() == ""
    assert not result.stderr or result.stderr.strip() == ""

def test_compile_all_placeholder_roots(tmp_path):
    """All-placeholder binder produces empty output with exit code 0."""
    # Setup: Binder with placeholders only (no node files)
    create_test_binder(tmp_path, roots=["Placeholder 1", "Placeholder 2"])
    # Don't create .md files - placeholders have no node_id

    # Execute
    runner = CliRunner()
    result = runner.invoke(cli, ["compile", "--path", str(tmp_path)])

    # Verify: Empty output, exit 0
    assert result.exit_code == 0
    assert result.output.strip() == ""
```
**Success Criteria**: Test written, test FAILS (empty binder handling not implemented yet) ✅

---

### T006 [P]: Integration Test - Placeholder Filtering ✅
**File**: `/workspace/tests/integration/compile/test_compile_with_placeholders.py`
**Description**: Write integration test verifying placeholders are filtered out.
**Test Scenario** (from quickstart.md Scenario 3):
```python
def test_compile_filters_placeholder_roots(tmp_path):
    """Only materialized roots compiled, placeholders skipped."""
    # Setup: Mix of placeholders and materialized nodes
    create_test_binder(tmp_path, roots=[
        "Placeholder 1",  # No node file
        "actual1",        # Has node file
        "Placeholder 2",  # No node file
        "actual2",        # Has node file
    ])
    create_test_node(tmp_path / "actual1.md", content="Actual 1 content")
    create_test_node(tmp_path / "actual2.md", content="Actual 2 content")

    # Execute
    runner = CliRunner()
    result = runner.invoke(cli, ["compile", "--path", str(tmp_path)])

    # Verify: Only actual nodes compiled
    assert result.exit_code == 0
    assert "Actual 1 content" in result.output
    assert "Actual 2 content" in result.output
    assert "Placeholder" not in result.output
```
**Success Criteria**: Test written, test FAILS (placeholder filtering not implemented yet) ✅

---

### T007 [P]: Integration Test - Single Node Behavior Preserved ✅
**File**: `/workspace/tests/integration/compile/test_compile_single_root_preserved.py`
**Description**: Write integration test verifying backward compatibility when node_id is provided.
**Test Scenario** (from quickstart.md Scenario 4):
```python
def test_compile_specific_node_only(tmp_path):
    """Providing node_id compiles only that node (existing behavior)."""
    # Setup: Binder with 2 roots
    create_test_binder(tmp_path, roots=["root1", "root2"])
    create_test_node(tmp_path / "root1.md", content="Root 1 content", node_id="root1")
    create_test_node(tmp_path / "root2.md", content="Root 2 content", node_id="root2")

    # Execute: Compile specific node
    runner = CliRunner()
    result = runner.invoke(cli, ["compile", "root1", "--path", str(tmp_path)])

    # Verify: Only root1 compiled
    assert result.exit_code == 0
    assert "Root 1 content" in result.output
    assert "Root 2 content" not in result.output

def test_compile_with_include_empty_flag(tmp_path):
    """--include-empty flag works consistently for all roots."""
    # Setup: Roots with empty content
    create_test_binder(tmp_path, roots=["empty1", "full1"])
    create_test_node(tmp_path / "empty1.md", content="", node_id="empty1")
    create_test_node(tmp_path / "full1.md", content="Full content", node_id="full1")

    # Execute without flag
    result = runner.invoke(cli, ["compile", "--path", str(tmp_path)])
    assert "Full content" in result.output
    # Empty node excluded by default

    # Execute with flag
    result = runner.invoke(cli, ["compile", "--include-empty", "--path", str(tmp_path)])
    assert "Full content" in result.output
    # Empty node included with flag
```
**Success Criteria**: Test written, test FAILS (multi-root logic not implemented yet) ✅

---

## Phase 3.4: Domain Model Changes (Make Contract Tests Pass) ✅ COMPLETE

### T008: Modify CompileRequest to Accept Optional Node ID ✅
**File**: `/workspace/src/prosemark/domain/compile/models.py`
**Description**: Change CompileRequest.node_id type from `NodeId` to `NodeId | None`.
**Changes**:
```python
@dataclass(frozen=True)
class CompileRequest:
    """Request to compile a node subtree or all root nodes.

    Args:
        node_id: NodeId to compile. If None, compile all materialized root nodes.
        include_empty: Whether to include nodes with empty content in compilation.
    """
    node_id: NodeId | None  # Changed from NodeId to NodeId | None
    include_empty: bool = False
```
**Success Criteria**:
- Type change applied ✅
- Docstring updated ✅
- Contract tests in T002 now PASS ✅
- mypy strict type checking passes ✅
- No regression in existing tests ✅

---

## Phase 3.5: Use Case Implementation (Make Integration Tests Pass) ✅ COMPLETE

### T009: Implement Multi-Root Compilation in Use Case ✅
**File**: `/workspace/src/prosemark/app/compile/use_cases.py`
**Description**: Add logic to CompileSubtreeUseCase to handle node_id=None by compiling all materialized root nodes.
**Changes**:
```python
class CompileSubtreeUseCase:
    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        """Compile a node subtree or all root nodes."""
        # New: Handle None node_id (compile all roots)
        if request.node_id is None:
            return self._compile_all_roots(request)

        # Existing: Single-node compilation
        return self._compile_single_node(request)

    def _compile_all_roots(self, request: CompileRequest) -> CompileResult:
        """Compile all materialized root nodes in binder order."""
        # Load binder
        binder = self._binder_repo.load()

        # Get materialized root node IDs
        root_node_ids = [
            item.node_id
            for item in binder.roots
            if item.node_id is not None
        ]

        # Handle empty binder
        if not root_node_ids:
            return CompileResult(
                content='',
                node_count=0,
                total_nodes=0,
                skipped_empty=0
            )

        # Compile each root and accumulate
        all_content_parts = []
        total_node_count = 0
        total_nodes_all = 0
        total_skipped = 0

        for root_id in root_node_ids:
            result = self._compile_service.compile_subtree(
                CompileRequest(node_id=root_id, include_empty=request.include_empty)
            )
            all_content_parts.append(result.content)
            total_node_count += result.node_count
            total_nodes_all += result.total_nodes
            total_skipped += result.skipped_empty

        # Combine with double newlines
        return CompileResult(
            content='\n\n'.join(all_content_parts),
            node_count=total_node_count,
            total_nodes=total_nodes_all,
            skipped_empty=total_skipped
        )

    def _compile_single_node(self, request: CompileRequest) -> CompileResult:
        """Compile a single node (existing logic)."""
        # Move existing compile_subtree logic here
        ...
```
**Dependencies**: T008 (CompileRequest change)
**Success Criteria**:
- Multi-root compilation logic implemented ✅
- Empty binder handling works ✅
- Placeholder filtering works ✅
- Result aggregation works ✅
- Integration tests T004-T007 now PASS ✅
- mypy strict passes ✅
- No regression in existing single-node tests ✅

---

## Phase 3.6: CLI Implementation (Complete Feature) ✅ COMPLETE

### T010: Make Node ID Optional in CLI Command ✅
**File**: `/workspace/src/prosemark/cli/compile.py`
**Description**: Change compile_command to accept optional node_id argument using typer.
**Changes**:
```python
def compile_command(
    node_id: Annotated[str | None, typer.Argument(help='Node ID to compile. Omit to compile all roots.')] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
    """Compile a node and its subtree, or all root nodes if no ID provided."""
    try:
        project_root = path or Path.cwd()

        # Wire up dependencies
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)
        from prosemark.adapters.binder_repo_fs import BinderRepoFs
        binder_repo = BinderRepoFs(project_root)
        compile_use_case = CompileSubtreeUseCase(node_repo, binder_repo)

        # Handle optional node_id
        if node_id is None:
            # Compile all roots
            request = CompileRequest(node_id=None, include_empty=False)
        else:
            # Validate and compile specific node (existing logic)
            try:
                target_node_id = NodeId(node_id)
            except Exception as e:
                typer.echo(f'Error: Invalid node ID format: {node_id}', err=True)
                raise typer.Exit(1) from e
            request = CompileRequest(node_id=target_node_id, include_empty=False)

        # Execute compilation
        result = compile_use_case.compile_subtree(request)

        # Output the compiled content to stdout
        typer.echo(result.content)

    except (NodeNotFoundError, CompileNodeNotFoundError) as e:
        typer.echo(f'Error: Node not found: {node_id}', err=True)
        raise typer.Exit(1) from e

    except Exception as e:
        typer.echo(f'Error: Compilation failed: {e}', err=True)
        raise typer.Exit(1) from e
```
**Dependencies**: T009 (use case multi-root support)
**Success Criteria**:
- CLI accepts both `pmk compile` and `pmk compile <node-id>` ✅
- Help text updated ✅
- All integration tests T004-T007 PASS ✅
- Backward compatibility preserved (existing CLI behavior unchanged) ✅

---

## Phase 3.7: Verification & Quality Gates ✅ COMPLETE

### T011: Run Type Checking ✅
**File**: N/A (verification task)
**Description**: Run mypy strict type checking on all modified files.
**Commands**:
```bash
mypy src/prosemark/domain/compile/models.py --strict
mypy src/prosemark/app/compile/use_cases.py --strict
mypy src/prosemark/cli/compile.py --strict
mypy tests/contract/compile/ --strict
mypy tests/integration/compile/ --strict
```
**Success Criteria**: Zero mypy errors, all type hints correct ✅

---

### T012: Run Linting ✅
**File**: N/A (verification task)
**Description**: Run ruff linting on all modified and new files.
**Commands**:
```bash
ruff check src/prosemark/domain/compile/models.py
ruff check src/prosemark/app/compile/use_cases.py
ruff check src/prosemark/cli/compile.py
ruff check tests/contract/compile/ --fix
ruff check tests/integration/compile/ --fix
ruff format src/prosemark/ tests/
```
**Success Criteria**: Zero linting errors, code formatted ✅

---

### T013: Verify 100% Test Coverage ✅
**File**: N/A (verification task)
**Description**: Run pytest with coverage to verify 100% coverage for modified code.
**Commands**:
```bash
pytest tests/contract/compile/ --cov=src/prosemark/domain/compile/models --cov-report=term-missing
pytest tests/integration/compile/ --cov=src/prosemark/app/compile --cov-report=term-missing
pytest tests/integration/compile/ --cov=src/prosemark/cli/compile --cov-report=term-missing
# Run full test suite
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100
```
**Success Criteria**: 100% coverage for all modified files, all tests pass ✅

---

### T014: Execute Quickstart Validation
**File**: `/workspace/specs/008-default-compile-all/quickstart.md`
**Description**: Manually execute all validation scenarios from quickstart.md to verify end-to-end behavior.
**Scenarios to Execute**:
1. Scenario 1: Compile All Roots (Standard Case) ✓
2. Scenario 2: Empty Binder Handling ✓
3. Scenario 3: Placeholder Filtering ✓
4. Scenario 4: Single Node Behavior Preserved ✓
5. Scenario 5: Include Empty Flag Behavior ✓
6. Scenario 6: Error Handling ✓
7. Scenario 7: Ordering Guarantee ✓

**Success Criteria**: All scenarios pass, manual validation complete

---

### T015: Performance Validation
**File**: N/A (performance test)
**Description**: Verify compilation performance with large binder (100 roots).
**Test**:
```bash
# Create test project with 100 roots
cd /tmp/pmk-perf-test
# ... setup 100 roots ...

# Measure compile time
time pmk compile > output.txt

# Verify: Completes in < 5 seconds
```
**Success Criteria**: 100 roots compile in < 5 seconds

---

### T016: Final Verification & Documentation
**File**: Multiple
**Description**: Final checks before feature completion.
**Checklist**:
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Type checking clean: `mypy src/ --strict`
- [ ] Linting clean: `ruff check src/ tests/`
- [ ] 100% coverage: `pytest --cov=src --cov-fail-under=100`
- [ ] Quickstart scenarios validated
- [ ] Performance acceptable (< 5s for 100 roots)
- [ ] No regression in existing functionality
- [ ] CLAUDE.md updated (already done in Phase 1)
- [ ] Ready for merge to master

**Success Criteria**: All quality gates pass, feature complete

---

## Dependencies

### Sequential Dependencies
```
T001 (Setup)
  ↓
T002, T003 (Contract Tests) [P]
  ↓
T008 (Domain Model Change)
  ↓
T004, T005, T006, T007 (Integration Tests) [P]
  ↓
T009 (Use Case Implementation)
  ↓
T010 (CLI Implementation)
  ↓
T011, T012, T013 (Quality Gates) [P]
  ↓
T014, T015, T016 (Final Validation)
```

### Blocking Relationships
- **T008** blocked by: T002 (must fail first)
- **T009** blocked by: T008, T004-T007 (tests must fail first)
- **T010** blocked by: T009
- **T011-T013** blocked by: T010
- **T014-T016** blocked by: T011-T013

---

## Parallel Execution Examples

### Example 1: Contract Tests (Phase 3.2)
```bash
# Launch T002 and T003 together (different files, no dependencies)
# These should FAIL initially

Task: "Write contract test for CompileRequest optional node_id in tests/contract/compile/test_compile_request_optional_node_id.py"

Task: "Write contract test for Binder roots iteration in tests/contract/compile/test_binder_roots_iteration.py"
```

### Example 2: Integration Tests (Phase 3.3)
```bash
# Launch T004-T007 together (different files, no dependencies)
# These should FAIL initially

Task: "Write integration test for compile all roots in tests/integration/compile/test_compile_all_roots.py"

Task: "Write integration test for empty binder in tests/integration/compile/test_compile_empty_binder.py"

Task: "Write integration test for placeholder filtering in tests/integration/compile/test_compile_with_placeholders.py"

Task: "Write integration test for single node behavior in tests/integration/compile/test_compile_single_root_preserved.py"
```

### Example 3: Quality Gates (Phase 3.7)
```bash
# Launch T011-T013 together (independent verification tasks)

Task: "Run mypy type checking on all modified files"

Task: "Run ruff linting on all modified files"

Task: "Verify 100% test coverage for modified code"
```

---

## Notes

### TDD Enforcement
- **CRITICAL**: Contract tests (T002-T003) MUST be written and verified to fail before T008
- **CRITICAL**: Integration tests (T004-T007) MUST be written and verified to fail before T009
- Do not proceed to implementation if tests are not failing

### Parallel Execution
- Tasks marked [P] can be executed simultaneously
- All [P] tasks within a phase are independent (different files)
- Do not parallelize tasks that modify the same file

### Quality Standards
- Every task must maintain 100% test coverage
- Every task must pass mypy strict type checking
- Every task must pass ruff linting
- No task is complete until quality gates pass

### Git Workflow
- Commit after completing each task or related group of tasks
- Use conventional commit messages: `feat(compile): description`
- Create restore point before risky changes

---

## Validation Checklist
*GATE: All must pass before feature is complete*

- [x] All contracts have corresponding tests (T002-T003)
- [x] All entities have model tasks (T008)
- [x] All tests come before implementation (T002-T007 before T008-T010)
- [x] Parallel tasks truly independent (verified)
- [x] Each task specifies exact file path (verified)
- [x] No task modifies same file as another [P] task (verified)
- [x] TDD ordering enforced (contract tests → domain → integration tests → implementation)

---

**Total Tasks**: 16
**Parallel Opportunities**: 8 tasks (T002-T003, T004-T007, T011-T013)
**Estimated Time**: 6-8 hours (with parallel execution: 4-6 hours)

**Status**: Tasks generated and ready for execution
**Next Step**: Begin execution with T001 (Setup & Verification)

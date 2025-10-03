# Implementation Plan: Optional Node ID for Compile Command

**Branch**: `008-default-compile-all` | **Date**: 2025-10-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/workspace/specs/008-default-compile-all/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded and analyzed
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ No clarifications needed - all resolved in spec
   → Detect Project Type: Single Python CLI project
   → Set Structure Decision: Hexagonal architecture (existing)
3. Fill Constitution Check section
   → ✅ Analyzed constitutional requirements
4. Evaluate Constitution Check section
   → ✅ No violations - feature extends existing architecture
   → Update Progress Tracking: Initial Constitution Check ✅
5. Execute Phase 0 → research.md
   → ✅ Complete - no unknowns remain
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Complete - design artifacts generated
7. Re-evaluate Constitution Check section
   → ✅ No new violations - design follows existing patterns
   → Update Progress Tracking: Post-Design Constitution Check ✅
8. Plan Phase 2 → Task generation approach described
9. STOP - Ready for /tasks command
```

## Summary
**Feature**: Make the `node_id` argument optional in the `pmk compile` command. When no node ID is provided, compile all materialized root nodes from the binder in binder order, concatenating their outputs with double newlines.

**Technical Approach**: Modify CLI compile command to accept optional node_id argument. When absent, query binder repository for all root nodes (items with no parent), filter for materialized nodes (non-placeholder), and iterate compilation for each root using existing CompileService. Aggregate results into single CompileResult with combined statistics.

## Technical Context
**Language/Version**: Python 3.13
**Primary Dependencies**: typer (CLI), Click (existing), existing prosemark domain/adapters
**Storage**: Plain text (Markdown + YAML frontmatter), file-based repositories
**Testing**: pytest with 100% coverage requirement
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single Python CLI project with hexagonal architecture
**Performance Goals**: Handle large binders (100+ root nodes) without significant delay (<5s for typical projects)
**Constraints**: Must maintain 100% test coverage, pass mypy strict type checking, pass ruff linting
**Scale/Scope**: Typical projects have 3-10 root nodes, edge case up to 100 roots

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Before Phase 0) ✅

| Principle | Compliance | Notes |
|-----------|------------|-------|
| **I. Hexagonal Architecture** | ✅ PASS | Extends existing CLI adapter and CompileService domain logic. No new architectural layers needed. |
| **II. Test-First Development** | ✅ PASS | Will write contract tests first, then integration tests, then implementation following TDD. |
| **III. Plain Text Storage** | ✅ PASS | No storage format changes - only reads existing binder structure. |
| **IV. Code Quality Standards** | ✅ PASS | Will maintain 100% mypy, ruff, pytest compliance throughout implementation. |
| **V. CLI-First Interface** | ✅ PASS | Feature is a CLI enhancement to existing `pmk compile` command. |

**Verdict**: No constitutional violations. Feature is a natural extension of existing compile functionality.

### Post-Design Check (After Phase 1) ✅

| Principle | Compliance | Notes |
|-----------|------------|-------|
| **I. Hexagonal Architecture** | ✅ PASS | Design uses existing ports (BinderRepo, NodeRepo) and adapters. No architectural changes. |
| **II. Test-First Development** | ✅ PASS | Contract tests defined for Binder.roots iteration, integration tests for CLI behavior. |
| **III. Plain Text Storage** | ✅ PASS | No storage changes in design. |
| **IV. Code Quality Standards** | ✅ PASS | All generated code follows type hints, docstrings, and quality standards. |
| **V. CLI-First Interface** | ✅ PASS | CLI contract defined with optional argument pattern. |

**Verdict**: Design maintains constitutional compliance. Ready for task generation.

## Project Structure

### Documentation (this feature)
```
specs/008-default-compile-all/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification (input)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── cli-compile.md   # CLI contract for optional node_id
│   └── binder-roots.md  # Binder repository contract for root node iteration
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/prosemark/
├── domain/
│   ├── compile/
│   │   ├── models.py         # CompileRequest (make node_id optional)
│   │   └── service.py        # CompileService (existing, no changes)
│   └── models.py             # Binder, BinderItem (existing)
├── ports/
│   └── binder_repo.py        # BinderRepo protocol (existing)
├── adapters/
│   ├── binder_repo_fs.py     # BinderRepoFs (existing)
│   └── node_repo_fs.py       # NodeRepoFs (existing)
├── app/
│   └── compile/
│       └── use_cases.py      # CompileSubtreeUseCase (modify for multi-root)
└── cli/
    └── compile.py            # compile_command (make node_id optional)

tests/
├── contract/
│   └── compile/
│       ├── test_compile_request_optional_node_id.py
│       └── test_binder_roots_iteration.py
├── integration/
│   └── compile/
│       ├── test_compile_all_roots.py
│       ├── test_compile_empty_binder.py
│       ├── test_compile_with_placeholders.py
│       └── test_compile_single_root_preserved.py
└── unit/
    └── compile/
        └── test_compile_all_roots_aggregation.py
```

**Structure Decision**: Single project structure following existing hexagonal architecture. Feature extends existing compile module without introducing new architectural layers. Changes concentrated in:
1. CLI layer (make argument optional)
2. Use case layer (add multi-root compilation logic)
3. Domain models (make CompileRequest.node_id optional)

## Phase 0: Outline & Research

### Research Questions
All questions resolved through code analysis and clarification session. No unknowns remain.

### Technical Decisions

**Decision 1: Optional Argument Pattern**
- **Decision**: Use `typer.Argument(default=None)` to make node_id optional
- **Rationale**: Standard typer pattern for optional positional arguments. Maintains backward compatibility.
- **Alternatives Considered**:
  - Flag `--all-roots`: Rejected - less intuitive than omitting argument
  - Subcommand `compile-all`: Rejected - unnecessary complexity for simple variation

**Decision 2: Root Node Iteration**
- **Decision**: Iterate `binder.roots` list directly, filter for `item.node_id is not None`
- **Rationale**: Binder already provides roots list. Simple list comprehension for materialized nodes.
- **Alternatives Considered**:
  - Add `get_materialized_roots()` method to Binder: Rejected - unnecessary abstraction for simple filter

**Decision 3: Result Aggregation**
- **Decision**: Accumulate statistics across all roots, join content with `\n\n` separator
- **Rationale**: Matches existing child node compilation behavior. Single CompileResult maintains consistency.
- **Alternatives Considered**:
  - Per-root CompileResult list: Rejected - adds complexity without user value (per clarifications)
  - Custom separator: Rejected - double newline is established pattern

**Decision 4: Empty Binder Handling**
- **Decision**: Return CompileResult with empty content, 0 statistics, exit code 0
- **Rationale**: Silent success matches clarification decision. No error for valid state (empty project).
- **Alternatives Considered**:
  - Error exit code: Rejected in clarifications
  - Warning message: Rejected in clarifications

**Output**: research.md (see below)

## Phase 1: Design & Contracts

### Data Model Changes

See `data-model.md` for complete entity definitions. Key changes:

**CompileRequest**:
```python
@dataclass(frozen=True)
class CompileRequest:
    node_id: NodeId | None  # Changed from required to optional
    include_empty: bool = False
```

**No changes to**:
- `CompileResult`: Already supports aggregated statistics
- `Binder`: Already exposes `.roots` list
- `BinderItem`: Already has `.is_root()` and `.node_id` properties

### API Contracts

**Contract 1: CLI Compile Command** (see `contracts/cli-compile.md`)
```
Command: pmk compile [NODE_ID] [--path PATH]

Behavior:
- If NODE_ID provided: Compile that specific node (existing behavior)
- If NODE_ID omitted: Compile all materialized root nodes in binder order
- Exit code 0 on success (including empty binder)
- Exit code 1 on errors (node not found when NODE_ID provided)
```

**Contract 2: Binder Root Iteration** (see `contracts/binder-roots.md`)
```
Operation: Iterate binder.roots and filter materialized nodes

Preconditions: Binder loaded from file system
Postconditions: List of NodeId for all root items where node_id is not None
Ordering: Binder file order (top to bottom)
Edge cases: Empty binder returns empty list, all-placeholder binder returns empty list
```

### Contract Tests

**Test 1: `test_compile_request_optional_node_id.py`**
```python
def test_compile_request_with_node_id():
    """CompileRequest accepts node_id."""
    request = CompileRequest(node_id=NodeId(...), include_empty=False)
    assert request.node_id is not None

def test_compile_request_without_node_id():
    """CompileRequest accepts None for node_id."""
    request = CompileRequest(node_id=None, include_empty=False)
    assert request.node_id is None
```

**Test 2: `test_binder_roots_iteration.py`**
```python
def test_binder_roots_returns_list():
    """Binder.roots returns list of BinderItems."""
    binder = Binder(roots=[...])
    assert isinstance(binder.roots, list)

def test_filter_materialized_roots():
    """Filter roots for materialized nodes only."""
    placeholder = BinderItem(display_title="Placeholder", node_id=None)
    materialized = BinderItem(display_title="Real", node_id=NodeId(...))
    binder = Binder(roots=[placeholder, materialized])

    materialized_ids = [item.node_id for item in binder.roots if item.node_id is not None]
    assert len(materialized_ids) == 1
```

### Integration Test Scenarios

See `quickstart.md` for complete test execution steps. Key scenarios:

1. **Compile all roots** (`test_compile_all_roots.py`):
   - Setup: Binder with 3 materialized root nodes
   - Execute: `pmk compile` (no node_id)
   - Verify: Output contains all 3 compilations, separated by `\n\n`

2. **Empty binder handling** (`test_compile_empty_binder.py`):
   - Setup: Binder with no roots
   - Execute: `pmk compile`
   - Verify: Empty output, exit code 0, statistics show 0 nodes

3. **Placeholder filtering** (`test_compile_with_placeholders.py`):
   - Setup: Binder with 2 placeholders, 1 materialized root
   - Execute: `pmk compile`
   - Verify: Only materialized root compiled, placeholders skipped

4. **Preserve single-node behavior** (`test_compile_single_root_preserved.py`):
   - Setup: Binder with 2 roots
   - Execute: `pmk compile <specific-node-id>`
   - Verify: Only specified node compiled (existing behavior)

### Agent Context Update

Executed: `.specify/scripts/bash/update-agent-context.sh claude`

**Output**: `/workspace/CLAUDE.md` updated with:
- Recent change: "Feature 008: Optional node ID for compile command"
- Tech stack: Already documented (Python 3.13, typer, hexagonal architecture)
- Quality standards: Already documented (100% coverage, mypy strict, ruff)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design:
   - Contract tests from `contracts/*.md` → test tasks [P]
   - Data model changes → model modification tasks [P]
   - Use case logic → use case implementation tasks
   - CLI changes → CLI modification tasks
   - Integration tests from `quickstart.md` → integration test tasks

**Ordering Strategy**:
- **Phase 1: Contract Tests** (TDD - write failing tests first)
  - Task 1 [P]: Write CompileRequest contract tests
  - Task 2 [P]: Write Binder roots iteration contract tests

- **Phase 2: Domain Changes** (make contract tests pass)
  - Task 3: Modify CompileRequest to make node_id optional
  - Task 4: Verify Binder.roots iteration works as expected

- **Phase 3: Integration Tests** (TDD - write failing tests)
  - Task 5 [P]: Write test_compile_all_roots
  - Task 6 [P]: Write test_compile_empty_binder
  - Task 7 [P]: Write test_compile_with_placeholders
  - Task 8 [P]: Write test_compile_single_root_preserved

- **Phase 4: Use Case Implementation** (make integration tests pass)
  - Task 9: Implement multi-root compilation in CompileSubtreeUseCase
  - Task 10: Add result aggregation logic

- **Phase 5: CLI Implementation** (complete feature)
  - Task 11: Make node_id optional in compile_command
  - Task 12: Wire optional node_id to use case

- **Phase 6: Verification** (quality gates)
  - Task 13: Run mypy type checking
  - Task 14: Run ruff linting
  - Task 15: Verify 100% test coverage
  - Task 16: Execute quickstart.md validation

**Estimated Output**: 16 numbered, ordered tasks in tasks.md

**Parallelization Markers**:
- [P] on Tasks 1-2: Contract tests are independent
- [P] on Tasks 5-8: Integration tests are independent files
- All other tasks sequential (dependencies on prior tasks)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No violations - this section remains empty*

The feature introduces no constitutional violations or architectural complexity:
- Uses existing hexagonal architecture
- No new layers or abstractions
- Simple extension of existing compile functionality
- Maintains test-first development
- Preserves plain text storage

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) - tasks.md created with 16 tasks
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

---
*Based on Constitution v1.1.0 - See `/workspace/.specify/memory/constitution.md`*

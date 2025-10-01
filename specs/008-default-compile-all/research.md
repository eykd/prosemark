# Phase 0: Research & Technical Decisions

**Feature**: Optional Node ID for Compile Command
**Date**: 2025-10-01

## Research Summary

All technical questions were resolved through code analysis of the existing prosemark implementation and the clarification session documented in `spec.md`. No external research was required.

## Technical Decisions

### Decision 1: Optional Argument Implementation Pattern

**Question**: How to make the node_id argument optional in typer CLI?

**Options Evaluated**:
1. `typer.Argument(default=None)` - Standard optional positional argument
2. `--all-roots` flag - Separate flag to trigger all-roots compilation
3. `compile-all` subcommand - New subcommand for multi-root compilation

**Decision**: Use `typer.Argument(default=None)`

**Rationale**:
- Standard typer pattern for optional positional arguments
- Maintains backward compatibility (existing `pmk compile <node-id>` still works)
- Most intuitive UX: omitting argument means "compile everything"
- No breaking changes to existing CLI interface
- Consistent with UNIX tool conventions (e.g., `cat` with no args vs `cat file.txt`)

**Implementation**:
```python
def compile_command(
    node_id: Annotated[str | None, typer.Argument(help='Node ID to compile')] = None,
    path: Annotated[Path | None, typer.Option('--path', '-p', help='Project directory')] = None,
) -> None:
```

**Alternatives Rejected**:
- **Flag approach**: Would require `pmk compile --all-roots`, less intuitive than omitting argument
- **Subcommand approach**: Introduces unnecessary complexity for what is essentially a parameter variation

---

### Decision 2: Root Node Discovery Strategy

**Question**: How to identify and iterate over root nodes in the binder?

**Options Evaluated**:
1. Iterate `binder.roots` list directly with list comprehension filter
2. Add `get_materialized_roots()` method to Binder domain model
3. Add root node query method to BinderRepo port

**Decision**: Iterate `binder.roots` directly, filter inline

**Rationale**:
- Binder already exposes `.roots` property (list of root-level BinderItems)
- BinderItem already has `.node_id` property (None for placeholders)
- Simple list comprehension: `[item.node_id for item in binder.roots if item.node_id is not None]`
- No domain model changes needed
- No port interface changes needed
- Follows existing patterns in codebase (e.g., child iteration in CompileService)

**Implementation**:
```python
# In use case layer
binder = binder_repo.load()
root_node_ids = [item.node_id for item in binder.roots if item.node_id is not None]
```

**Alternatives Rejected**:
- **Domain method**: `binder.get_materialized_roots()` would add unnecessary abstraction for a simple filter operation
- **Repository method**: Would mix concern of "what is a root" (domain) with data access (repository)

---

### Decision 3: Compilation Result Aggregation

**Question**: How to aggregate multiple root compilations into a single result?

**Options Evaluated**:
1. Accumulate statistics across all roots, single CompileResult with combined content
2. Return list of CompileResult (one per root)
3. Return dictionary mapping NodeId to CompileResult

**Decision**: Single CompileResult with accumulated statistics and concatenated content

**Rationale**:
- Clarification session confirmed: "Combined statistics only (total nodes across all roots, matching single-node format)"
- Maintains consistency with single-node compilation output format
- CompileResult already designed for aggregation (node_count, total_nodes, skipped_empty)
- Content concatenation with `\n\n` matches existing child node compilation behavior
- Simpler CLI output handling (single stdout stream)

**Implementation**:
```python
# Accumulate across roots
all_content_parts = []
total_node_count = 0
total_nodes_all = 0
total_skipped = 0

for root_id in root_node_ids:
    result = compile_service.compile_subtree(CompileRequest(node_id=root_id, include_empty=...))
    all_content_parts.append(result.content)
    total_node_count += result.node_count
    total_nodes_all += result.total_nodes
    total_skipped += result.skipped_empty

return CompileResult(
    content='\n\n'.join(all_content_parts),
    node_count=total_node_count,
    total_nodes=total_nodes_all,
    skipped_empty=total_skipped
)
```

**Alternatives Rejected**:
- **Per-root results**: Clarification session explicitly chose combined statistics over per-root statistics
- **Dictionary mapping**: Adds complexity without user value (per clarifications)

---

### Decision 4: Empty Binder Handling

**Question**: What behavior when binder has no materialized root nodes?

**Options Evaluated**:
1. Return empty CompileResult, exit code 0 (silent success)
2. Return error message to stderr, exit code 1 (error)
3. Return empty CompileResult with warning message to stderr, exit code 0 (warning)

**Decision**: Silent success - empty CompileResult with 0 statistics, exit code 0

**Rationale**:
- Clarification session confirmed: "Produce empty output with statistics showing 0 nodes compiled (silent success)"
- Empty project is a valid state, not an error condition
- Consistent with UNIX tool philosophy (e.g., `grep` with no matches exits 0)
- CompileResult already handles empty content naturally
- User can distinguish empty result from error via exit code

**Implementation**:
```python
if not root_node_ids:
    # No materialized roots - return empty result
    return CompileResult(
        content='',
        node_count=0,
        total_nodes=0,
        skipped_empty=0
    )
```

**Alternatives Rejected**:
- **Error exit**: Clarification session explicitly rejected this (not an error condition)
- **Warning message**: Clarification session explicitly rejected this (prefer silent success)

---

### Decision 5: Node Ordering Guarantee

**Question**: In what order should root nodes be processed?

**Options Evaluated**:
1. Binder file order (top to bottom in binder.md)
2. Creation timestamp order (oldest first)
3. Alphabetical by display title

**Decision**: Binder file order

**Rationale**:
- Clarification session confirmed: "Binder order (top to bottom as they appear in the binder hierarchy)"
- User has explicit control over ordering via binder.md file structure
- Deterministic and reproducible output
- Matches user's visual organization in Obsidian/editor
- `binder.roots` list already maintains file order

**Implementation**:
- No additional sorting needed
- Iterate `binder.roots` in natural list order
- Order is preserved from file system read by BinderRepoFs

**Alternatives Rejected**:
- **Timestamp order**: Less intuitive than visual file order
- **Alphabetical order**: Overrides user's intentional ordering in binder file

---

### Decision 6: Empty Content Handling

**Question**: How should `--include-empty` flag apply when compiling all roots?

**Options Evaluated**:
1. Honor `--include-empty` flag for all roots (consistent with single-node compilation)
2. Always include empty roots (different default for bulk compilation)
3. Always exclude empty roots (different default for bulk compilation)

**Decision**: Honor `--include-empty` flag consistently

**Rationale**:
- Clarification session confirmed: "Honor the existing --include-empty flag for all roots (consistent with single-node compilation)"
- Behavioral consistency: same flag, same effect regardless of node_id presence
- Principle of least surprise for users
- No special cases in implementation

**Implementation**:
```python
# Pass through to each root compilation
for root_id in root_node_ids:
    result = compile_service.compile_subtree(
        CompileRequest(node_id=root_id, include_empty=request.include_empty)
    )
```

**Alternatives Rejected**:
- **Different default for bulk**: Clarification session explicitly chose consistency over different behavior
- **Always include/exclude**: Would ignore user's explicit flag choice

---

## Code Analysis Findings

### Existing Architecture (No Changes Needed)

**Binder Model** (`src/prosemark/domain/models.py`):
- Already exposes `.roots: list[BinderItem]` property
- BinderItem already has `.node_id: NodeId | None` (None for placeholders)
- BinderItem already has `.is_root()` method (checks `self.parent is None`)

**CompileService** (`src/prosemark/domain/compile/service.py`):
- Already designed for single-root compilation with subtree traversal
- Can be called multiple times for multiple roots
- No changes needed to core compilation logic

**CompileRequest** (`src/prosemark/domain/compile/models.py`):
- Currently: `node_id: NodeId` (required)
- Needs change: `node_id: NodeId | None` (optional)
- This is the primary domain model change

**CompileResult** (`src/prosemark/domain/compile/models.py`):
- Already supports aggregated statistics
- Already has `content: str` for concatenated output
- No changes needed

---

## Dependencies & Integration Points

**No New Dependencies**:
- All required functionality exists in current codebase
- Uses existing typer, domain models, repositories
- No external library additions needed

**Integration Points**:
1. CLI layer (`src/prosemark/cli/compile.py`):
   - Change: Make `node_id` parameter optional
   - Wire: Pass `None` to use case when omitted

2. Use case layer (`src/prosemark/app/compile/use_cases.py`):
   - Add: Logic to handle `node_id=None` case
   - Add: Root node discovery and iteration
   - Add: Result aggregation across roots

3. Domain layer (`src/prosemark/domain/compile/models.py`):
   - Change: Make `CompileRequest.node_id` optional

---

## Performance Considerations

**Typical Case** (3-10 root nodes):
- Linear iteration over roots: O(n) where n = number of roots
- Each root compilation: O(m) where m = nodes in subtree
- Total: O(n * m_avg) - acceptable for typical projects
- Expected time: <1 second

**Edge Case** (100 root nodes):
- Same O(n * m_avg) complexity
- File I/O dominates (reading .md files)
- Expected time: <5 seconds (within performance goal)

**Optimization Opportunities** (not needed for MVP):
- Parallel compilation of roots (independent operations)
- Stream output instead of accumulating in memory
- Early exit on errors (current behavior: skip missing files)

---

## Testing Strategy

**Contract Tests** (verify interfaces):
- CompileRequest accepts `node_id=None`
- Binder.roots iteration works as expected
- Filter materialized nodes correctly

**Integration Tests** (verify end-to-end behavior):
- Compile all roots produces expected output
- Empty binder handled correctly
- Placeholders filtered out
- Single-node behavior preserved

**Quality Gates**:
- 100% test coverage required
- mypy strict type checking must pass
- ruff linting must pass

---

## Risk Assessment

**Low Risk**:
- Simple extension of existing functionality
- No breaking changes to existing behavior
- No architectural changes
- No external dependencies

**Mitigation Strategies**:
- TDD approach ensures correctness
- Contract tests verify interface contracts
- Integration tests verify end-to-end behavior
- Type checking prevents runtime errors
- Existing test suite ensures no regressions

---

## Unknowns Resolved

**Before Research**:
- ✅ How to make CLI argument optional (Decision 1)
- ✅ How to discover root nodes (Decision 2)
- ✅ How to aggregate results (Decision 3)
- ✅ How to handle empty binder (Decision 4)
- ✅ What ordering to use (Decision 5)
- ✅ How to apply --include-empty flag (Decision 6)

**After Research**:
- ✅ All technical decisions documented
- ✅ No blocking unknowns remain
- ✅ Implementation path is clear
- ✅ Ready for Phase 1 design

---

**Status**: Research complete, all NEEDS CLARIFICATION resolved
**Next Phase**: Phase 1 - Design & Contracts

# Data Model: Optional Node ID for Compile Command

## Overview

This feature makes minimal changes to the existing data model. The primary change is making the `node_id` field optional in `CompileRequest`. All other domain entities remain unchanged.

---

## Modified Entities

### CompileRequest (Domain Model)

**Location**: `src/prosemark/domain/compile/models.py`

**Current Definition**:
```python
@dataclass(frozen=True)
class CompileRequest:
    """Request to compile a node subtree."""
    node_id: NodeId  # Required
    include_empty: bool = False
```

**Modified Definition**:
```python
@dataclass(frozen=True)
class CompileRequest:
    """Request to compile a node subtree or all root nodes.

    Args:
        node_id: NodeId to compile. If None, compile all materialized root nodes.
        include_empty: Whether to include nodes with empty content in compilation.
    """
    node_id: NodeId | None  # Optional - None means "compile all roots"
    include_empty: bool = False
```

**Change Summary**:
- `node_id` type changed from `NodeId` to `NodeId | None`
- Docstring updated to document None behavior
- No other changes to the dataclass

**Backward Compatibility**:
- Existing code passing NodeId continues to work
- Type checker will enforce None handling in consuming code
- No runtime breaking changes

---

## Unchanged Entities

The following entities require no changes and are listed here for completeness:

### CompileResult (Domain Model)

**Location**: `src/prosemark/domain/compile/models.py`

**Definition** (unchanged):
```python
@dataclass(frozen=True)
class CompileResult:
    """Result of compiling a node subtree.

    Args:
        content: Concatenated content from all nodes in the subtree
        node_count: Number of nodes included in compilation
        total_nodes: Total number of nodes traversed
        skipped_empty: Number of nodes skipped due to empty content
    """
    content: str
    node_count: int
    total_nodes: int
    skipped_empty: int
```

**Why No Changes**:
- Already designed to support aggregated statistics
- `content` field already holds concatenated text
- Statistics fields (node_count, total_nodes, skipped_empty) already represent combined totals
- Works naturally for single-root and multi-root compilation

---

### Binder (Domain Model)

**Location**: `src/prosemark/domain/models.py`

**Relevant Properties** (unchanged):
```python
@dataclass
class Binder:
    """Aggregate root for document hierarchy.

    Args:
        roots: List of root-level BinderItem objects
        project_title: Optional title for the entire project/binder
    """
    roots: list[BinderItem] = field(default_factory=list)
    project_title: str | None = field(default=None)
```

**Why No Changes**:
- `roots` property already exposes root-level items
- List maintains binder file order naturally
- Binder invariants already prevent duplicate NodeIds
- No new methods needed for root iteration

---

### BinderItem (Domain Model)

**Location**: `src/prosemark/domain/models.py`

**Relevant Properties** (unchanged):
```python
@dataclass
class BinderItem:
    """Individual node in the binder hierarchy.

    Args:
        display_title: Display title for the item
        node_id: Optional NodeId reference (None for placeholders)
        children: List of child BinderItem objects
        parent: Optional parent BinderItem reference
    """
    display_title: str
    node_id: NodeId | None = None
    children: list['BinderItem'] = field(default_factory=list)
    parent: 'BinderItem | None' = None

    def is_root(self) -> bool:
        """Check if this item is a root item (no parent)."""
        return self.parent is None

    def is_materialized(self) -> bool:
        """Check if this item is materialized (has node_id)."""
        return self.node_id is not None
```

**Why No Changes**:
- `node_id` field already optional (None for placeholders)
- `is_root()` method already identifies root items
- `is_materialized()` method already identifies materialized items
- No new properties or methods needed

---

### NodeContent (Domain Model)

**Location**: `src/prosemark/domain/compile/models.py`

**Definition** (unchanged):
```python
@dataclass(frozen=True)
class NodeContent:
    """Content of a single node during compilation.

    Args:
        id: Node identifier
        content: Node content with frontmatter stripped
        children: List of child node identifiers
    """
    id: NodeId
    content: str
    children: list[NodeId]
```

**Why No Changes**:
- Used internally by CompileService for traversal
- Not affected by optional node_id in CompileRequest
- CompileService continues to work node-by-node

---

## Data Flow

### Single-Node Compilation (Existing)

```
CompileRequest(node_id=specific_id, include_empty=False)
    ↓
CompileService.compile_subtree(request)
    ↓
Traverse subtree starting from node_id
    ↓
CompileResult(content=..., node_count=..., ...)
```

**No changes to this flow**.

---

### Multi-Root Compilation (New)

```
CompileRequest(node_id=None, include_empty=False)
    ↓
CompileSubtreeUseCase identifies None
    ↓
Load binder via BinderRepo
    ↓
Filter: [item.node_id for item in binder.roots if item.node_id is not None]
    ↓
For each root_id:
    CompileService.compile_subtree(CompileRequest(node_id=root_id, include_empty=...))
    ↓
    Accumulate results
    ↓
CompileResult(content=combined, node_count=total, ...)
```

**New logic in use case layer only** - domain models unchanged.

---

## Type Safety

### Before Change

```python
# Type checker enforces node_id is always present
request = CompileRequest(node_id=some_id, include_empty=False)
assert request.node_id is not None  # Always true
```

### After Change

```python
# Type checker requires handling both cases
request = CompileRequest(node_id=None, include_empty=False)

if request.node_id is None:
    # Handle multi-root compilation
    ...
else:
    # Handle single-node compilation
    ...
```

**Type Safety Preserved**:
- mypy strict mode enforces None checks
- No silent None access (would be caught by type checker)
- Explicit Optional[NodeId] type in signature

---

## Database/Storage Impact

**No Storage Changes**:
- CompileRequest is in-memory only (not persisted)
- Binder structure unchanged (same YAML format)
- Node files unchanged (same Markdown format)
- No migration needed

---

## Validation Rules

### CompileRequest Validation

**Before** (implicit):
- `node_id` must be valid NodeId (type system enforces)

**After** (explicit):
- `node_id` can be None OR valid NodeId (type system enforces)
- No additional validation needed

### Binder Validation

**Unchanged**:
- Binder enforces no duplicate NodeIds across tree
- Root items must have parent=None
- These invariants already enforced by Binder class

---

## Relationships

### CompileRequest → NodeId

**Type**: Optional reference
- **Cardinality**: 0..1 (None or one NodeId)
- **Meaning**: None = "compile all roots", NodeId = "compile this specific node"

### Binder → BinderItem (roots)

**Type**: Composition
- **Cardinality**: 0..* (zero or more root items)
- **Meaning**: Root-level items in binder hierarchy

### BinderItem → NodeId

**Type**: Optional reference
- **Cardinality**: 0..1 (None for placeholder, NodeId for materialized)
- **Meaning**: None = "placeholder item", NodeId = "materialized node"

---

## State Transitions

### CompileRequest State

**No state transitions** - CompileRequest is immutable (frozen dataclass)

**Creation States**:
1. Create with specific NodeId: `CompileRequest(node_id=id, ...)`
2. Create with None: `CompileRequest(node_id=None, ...)`

### BinderItem State

**Materialization** (existing):
- Initial: `BinderItem(display_title="X", node_id=None)` (placeholder)
- Materialized: `item.materialize(NodeId(...))` → node_id set
- This transition already exists, feature doesn't change it

---

## Domain Invariants Maintained

1. **Binder Invariant**: No duplicate NodeIds
   - **Maintained**: Feature only reads NodeIds, doesn't create duplicates

2. **BinderItem Invariant**: Root items have parent=None
   - **Maintained**: Feature only reads root property, doesn't modify structure

3. **CompileRequest Invariant**: Immutability
   - **Maintained**: node_id field remains frozen

4. **CompileResult Invariant**: Non-negative statistics
   - **Maintained**: Accumulation preserves non-negative values

---

## Testing Implications

### Contract Tests Required

```python
def test_compile_request_accepts_none():
    """CompileRequest accepts None for node_id."""
    request = CompileRequest(node_id=None, include_empty=False)
    assert request.node_id is None

def test_compile_request_accepts_node_id():
    """CompileRequest accepts NodeId for node_id."""
    node_id = NodeId.generate()
    request = CompileRequest(node_id=node_id, include_empty=False)
    assert request.node_id == node_id

def test_binder_roots_are_list_of_binder_items():
    """Binder.roots returns list of BinderItems."""
    binder = Binder(roots=[])
    assert isinstance(binder.roots, list)

def test_binder_item_node_id_can_be_none():
    """BinderItem.node_id can be None."""
    item = BinderItem(display_title="Test", node_id=None)
    assert item.node_id is None
    assert not item.is_materialized()
```

---

## Documentation Updates

### Docstring Updates Required

1. **CompileRequest**:
   - Document that None means "compile all roots"
   - Document that NodeId means "compile specific node"

2. **CompileSubtreeUseCase** (or new use case method):
   - Document multi-root compilation behavior
   - Document result aggregation

### No Documentation Changes

- Binder: Already documents roots property
- BinderItem: Already documents optional node_id
- CompileResult: Already documents aggregated statistics

---

## Summary

**Changed**: 1 entity (CompileRequest.node_id type)
**Unchanged**: 4 entities (CompileResult, Binder, BinderItem, NodeContent)
**New Entities**: 0
**Deleted Entities**: 0
**Storage Changes**: 0
**Migration Required**: No

**Impact**: Minimal, localized to CompileRequest type signature. All other domain entities work as-is for multi-root compilation.

---

**Status**: Data model changes identified and documented
**Next Step**: Update CompileRequest in domain/compile/models.py

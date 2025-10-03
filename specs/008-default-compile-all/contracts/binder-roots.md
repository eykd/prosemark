# Binder Contract: Root Node Iteration and Filtering

## Interface Contract

### Operation: Get Materialized Root Nodes

**Signature**:
```python
def get_materialized_root_node_ids(binder: Binder) -> list[NodeId]:
    """Get list of NodeIds for all materialized root nodes in binder order.

    Args:
        binder: Loaded binder with root nodes

    Returns:
        List of NodeId for root nodes that are materialized (node_id is not None),
        in binder file order (top to bottom)
    """
```

**Implementation Pattern**:
```python
materialized_root_ids = [
    item.node_id
    for item in binder.roots
    if item.node_id is not None
]
```

---

## Preconditions

1. **Binder Loaded**: Binder object has been loaded from file system via BinderRepo
2. **Roots Populated**: Binder.roots list contains all root-level BinderItems
3. **Valid Structure**: Each BinderItem has valid node_id or None (for placeholders)

---

## Postconditions

1. **Filtered List**: Result contains only NodeIds from materialized root nodes
2. **Ordering Preserved**: NodeIds appear in same order as binder.roots list
3. **No Duplicates**: Each NodeId appears at most once (enforced by Binder invariants)
4. **Non-Empty NodeIds**: All returned NodeIds are non-None and valid UUIDv7

---

## Behavior Matrix

| Binder State | Input | Output | Notes |
|--------------|-------|--------|-------|
| Empty binder | `Binder(roots=[])` | `[]` | Valid state, empty list returned |
| All placeholders | `Binder(roots=[ph1, ph2])` where all node_id=None | `[]` | No materialized nodes to compile |
| All materialized | `Binder(roots=[m1, m2, m3])` where all node_id present | `[id1, id2, id3]` | Standard case, all roots included |
| Mixed | `Binder(roots=[ph, m1, ph, m2])` | `[id1, id2]` | Placeholders filtered out, order preserved |
| Single root | `Binder(roots=[m1])` | `[id1]` | Works with one root |

---

## Invariants Relied Upon

### Binder Invariants (from Domain Model)
1. **No Duplicate NodeIds**: Binder enforces no duplicate NodeIds across entire tree
2. **Valid Root Items**: All items in binder.roots are valid BinderItems
3. **File Order Preserved**: binder.roots list maintains file order from binder.md

### BinderItem Invariants (from Domain Model)
1. **Root Definition**: Root items have `parent=None`
2. **Materialization**: Item is materialized if and only if `node_id is not None`
3. **Valid NodeId**: When present, node_id is a valid UUIDv7

---

## Edge Cases

### Edge Case 1: Empty Binder

**Input**:
```python
binder = Binder(roots=[])
```

**Expected Output**:
```python
[]  # Empty list
```

**Contract**: Valid state, no error

---

### Edge Case 2: All Placeholder Roots

**Input**:
```python
binder = Binder(roots=[
    BinderItem(display_title="Section 1", node_id=None),
    BinderItem(display_title="Section 2", node_id=None),
])
```

**Expected Output**:
```python
[]  # No materialized nodes
```

**Contract**: Valid state, no error, empty list returned

---

### Edge Case 3: Single Materialized Root

**Input**:
```python
binder = Binder(roots=[
    BinderItem(display_title="Novel", node_id=NodeId("01234567-89ab-cdef-0123-456789abcdef"))
])
```

**Expected Output**:
```python
[NodeId("01234567-89ab-cdef-0123-456789abcdef")]
```

**Contract**: Works correctly with single element

---

### Edge Case 4: Interleaved Placeholders

**Input**:
```python
binder = Binder(roots=[
    BinderItem(display_title="Placeholder 1", node_id=None),
    BinderItem(display_title="Chapter 1", node_id=id1),
    BinderItem(display_title="Placeholder 2", node_id=None),
    BinderItem(display_title="Chapter 2", node_id=id2),
    BinderItem(display_title="Chapter 3", node_id=id3),
])
```

**Expected Output**:
```python
[id1, id2, id3]  # Order preserved, placeholders removed
```

**Contract**: Filtering maintains relative order of materialized nodes

---

### Edge Case 5: Large Number of Roots

**Input**:
```python
binder = Binder(roots=[
    BinderItem(display_title=f"Chapter {i}", node_id=NodeId(...))
    for i in range(100)
])
```

**Expected Output**:
```python
[id_0, id_1, ..., id_99]  # All 100 NodeIds in order
```

**Contract**: Performance acceptable for 100+ roots (<100ms)

---

## Performance Characteristics

**Time Complexity**: O(n) where n = number of root nodes
**Space Complexity**: O(m) where m = number of materialized root nodes
**Expected Performance**: <1ms for typical case (3-10 roots), <100ms for edge case (100 roots)

---

## Error Handling

### No Errors Expected

This operation does not raise errors for:
- Empty binder (returns empty list)
- All-placeholder binder (returns empty list)
- Large number of roots (handles within performance constraints)

### Errors Propagated from Dependencies

- **Binder Loading Errors**: If binder_repo.load() fails, error propagates
- **File System Errors**: If binder file unreadable, error propagates
- **Parse Errors**: If binder.md malformed, error propagates

These errors are handled by caller (use case layer), not by this filtering operation.

---

## Testing Requirements

### Contract Tests

1. **Test empty binder returns empty list**
```python
def test_empty_binder_returns_empty_list():
    binder = Binder(roots=[])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == []
```

2. **Test all placeholders returns empty list**
```python
def test_all_placeholders_returns_empty_list():
    binder = Binder(roots=[
        BinderItem(display_title="A", node_id=None),
        BinderItem(display_title="B", node_id=None),
    ])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == []
```

3. **Test filtering preserves order**
```python
def test_filtering_preserves_order():
    id1 = NodeId.generate()
    id2 = NodeId.generate()
    binder = Binder(roots=[
        BinderItem(display_title="P1", node_id=None),
        BinderItem(display_title="M1", node_id=id1),
        BinderItem(display_title="P2", node_id=None),
        BinderItem(display_title="M2", node_id=id2),
    ])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == [id1, id2]
```

4. **Test all materialized returns all**
```python
def test_all_materialized_returns_all():
    ids = [NodeId.generate() for _ in range(3)]
    binder = Binder(roots=[
        BinderItem(display_title=f"Ch{i}", node_id=id)
        for i, id in enumerate(ids)
    ])
    result = [item.node_id for item in binder.roots if item.node_id is not None]
    assert result == ids
```

---

## Integration with Existing Code

**No Changes Required** to existing Binder or BinderItem classes:
- `Binder.roots` property already exists
- `BinderItem.node_id` property already exists
- `BinderItem.is_root()` method already exists (not needed for filtering)

**Implementation Location**: Use case layer (CompileSubtreeUseCase)

**Dependencies**: None (uses existing domain models)

---

**Status**: Contract defined and ready for implementation
**Next Step**: Implement contract tests for root node filtering

# CLI Contract: Compile Command with Optional Node ID

## Command Signature

```bash
pmk compile [NODE_ID] [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NODE_ID` | string (UUIDv7) | No | Node ID to compile. If omitted, compiles all materialized root nodes. |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--path`, `-p` | Path | Current directory | Project directory containing binder and nodes |
| `--include-empty` | Flag | False | Include nodes with empty content in compilation |

## Behavior Contract

### Case 1: Node ID Provided (Existing Behavior)

**Input**: `pmk compile 01234567-89ab-cdef-0123-456789abcdef --path /project`

**Preconditions**:
- Valid project directory exists at specified path
- Binder file exists and is readable
- Node with specified ID exists in binder

**Postconditions**:
- Compiles specified node and its subtree
- Output contains concatenated content to stdout
- Exit code 0 on success
- Exit code 1 if node not found

**Example Output**:
```
Content of node 01234567...
Double newline separator
Content of child node...
```

---

### Case 2: Node ID Omitted (New Behavior)

**Input**: `pmk compile --path /project`

**Preconditions**:
- Valid project directory exists at specified path
- Binder file exists and is readable

**Postconditions**:
- Identifies all root nodes in binder (items with no parent)
- Filters for materialized nodes only (node_id is not None)
- Compiles each root node and its subtree in binder order
- Concatenates all compilations with double newline separators
- Output contains all compiled content to stdout
- Reports combined statistics (total nodes across all roots)
- Exit code 0 on success (including empty binder case)

**Example Output** (3 roots):
```
Content of root 1 and its subtree...

Content of root 2 and its subtree...

Content of root 3 and its subtree...
```

---

### Case 3: Empty Binder (New Behavior)

**Input**: `pmk compile --path /project`

**Preconditions**:
- Valid project directory exists
- Binder file exists but has no root nodes

**Postconditions**:
- Output is empty string
- Exit code 0 (silent success)
- No error message

**Example Output**:
```
(empty output)
```

---

### Case 4: All Placeholder Roots (New Behavior)

**Input**: `pmk compile --path /project`

**Preconditions**:
- Valid project directory exists
- Binder has root nodes but all are placeholders (node_id=None)

**Postconditions**:
- Output is empty string (no materialized nodes to compile)
- Exit code 0 (silent success)
- No error message

**Example Output**:
```
(empty output)
```

---

### Case 5: Include Empty Flag Applied to All Roots

**Input**: `pmk compile --include-empty --path /project`

**Preconditions**:
- Valid project directory exists
- Binder has multiple root nodes
- Some nodes have empty content

**Postconditions**:
- Compiles all materialized root nodes
- Includes nodes with empty content in compilation
- Flag behavior consistent with single-node compilation

---

## Error Handling

### Error 1: Invalid Node ID (When Provided)

**Input**: `pmk compile invalid-id`

**Output**:
```
Error: Invalid node ID format: invalid-id
```

**Exit Code**: 1

---

### Error 2: Node Not Found (When Provided)

**Input**: `pmk compile 01234567-89ab-cdef-0123-456789abcdef` (node doesn't exist)

**Output**:
```
Error: Node not found: 01234567-89ab-cdef-0123-456789abcdef
```

**Exit Code**: 1

---

### Error 3: Project Path Invalid

**Input**: `pmk compile --path /nonexistent`

**Output**:
```
Error: Project directory not found: /nonexistent
```

**Exit Code**: 1

---

## Ordering Guarantee

**Contract**: When compiling all roots (no NODE_ID provided), roots are processed in binder file order (top to bottom as they appear in the binder.md file).

**Rationale**: Provides deterministic, reproducible output that matches user's visual organization.

---

## Statistics Output

**Contract**: Compilation statistics (node count, total nodes, skipped empty) represent combined totals across all compiled roots.

**Format** (same as single-node compilation):
- Output goes to stdout
- No separate statistics section
- Statistics can be inferred from output structure

---

## Backward Compatibility

**Contract**: Existing behavior is preserved when NODE_ID is provided.

**Guarantee**:
- `pmk compile <node-id>` behaves exactly as before
- No breaking changes to existing CLI interface
- No changes to output format for single-node compilation
- No changes to exit codes for single-node compilation

---

## Contract Test Requirements

1. **Test optional argument acceptance**: Verify CLI accepts both `pmk compile` and `pmk compile <node-id>`
2. **Test empty binder handling**: Verify exit code 0 with empty output
3. **Test placeholder filtering**: Verify placeholders are skipped
4. **Test ordering**: Verify roots compiled in binder order
5. **Test flag consistency**: Verify `--include-empty` applies to all roots
6. **Test error codes**: Verify exit code 1 for errors, 0 for success
7. **Test backward compatibility**: Verify single-node behavior unchanged

---

**Status**: Contract defined and ready for implementation
**Next Step**: Implement contract tests, then CLI modification

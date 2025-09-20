# CLI Command Contracts

**Feature**: Prosemark CLI Writing Project Manager MVP
**Date**: 2025-09-20

## Command Interface Specification

### Global Options
```bash
pmk [COMMAND] [OPTIONS] [ARGUMENTS]

Global Options:
  --help     Show help message
  --version  Show version information
```

### Command: init
**Purpose**: Initialize new prosemark project
**Usage**: `pmk init --title TITLE [--path PATH]`

**Parameters**:
- `--title TEXT`: Project title (required)
- `--path PATH`: Project directory (optional, defaults to current)

**Success Response**:
```
Project "My Novel" initialized successfully
Created _binder.md with project structure
```

**Error Responses**:
- Exit code 1: Directory already contains prosemark project
- Exit code 2: Invalid path or permission denied

### Command: add
**Purpose**: Add new node to binder hierarchy
**Usage**: `pmk add TITLE [--parent PARENT_ID] [--position INDEX]`

**Parameters**:
- `TITLE`: Display title for new node (required)
- `--parent UUID`: Parent node ID (optional, defaults to root level)
- `--position INT`: Position in parent's children (optional, defaults to end)

**Success Response**:
```
Added "Chapter 1: Beginning" (01234567)
Created files: 01234567.md, 01234567.notes.md
Updated binder structure
```

**Error Responses**:
- Exit code 1: Parent node not found
- Exit code 2: Invalid position index
- Exit code 3: File creation failed

### Command: edit
**Purpose**: Open node content in preferred editor
**Usage**: `pmk edit NODE_ID --part {draft|notes|synopsis}`

**Parameters**:
- `NODE_ID`: Node identifier (required)
- `--part`: Content part to edit (required)
  - `draft`: Edit {id}.md content
  - `notes`: Edit {id}.notes.md content
  - `synopsis`: Edit synopsis in {id}.md frontmatter

**Success Response**:
```
Opened 01234567.md in editor
```

**Error Responses**:
- Exit code 1: Node not found
- Exit code 2: Editor not available
- Exit code 3: File permission denied

### Command: structure
**Purpose**: Display project hierarchy
**Usage**: `pmk structure [--format {tree|json}]`

**Parameters**:
- `--format`: Output format (optional, defaults to tree)

**Success Response** (tree format):
```
Project Structure:
├─ Chapter 1: Beginning (01234567)
│  ├─ Section 1.1 (89abcdef)
│  └─ Section 1.2 (deadbeef)
├─ Chapter 2: Development (cafebabe)
└─ [Future Chapter]
```

**Success Response** (json format):
```json
{
  "roots": [
    {
      "display_title": "Chapter 1: Beginning",
      "node_id": "01234567",
      "children": [
        {"display_title": "Section 1.1", "node_id": "89abcdef"},
        {"display_title": "Section 1.2", "node_id": "deadbeef"}
      ]
    }
  ]
}
```

### Command: write
**Purpose**: Create timestamped freeform writing file
**Usage**: `pmk write [TITLE]`

**Parameters**:
- `TITLE`: Optional title for freeform content

**Success Response**:
```
Created freeform file: 20250920T1530_01234567-89ab-cdef-0123-456789abcdef.md
Opened in editor
```

**Error Responses**:
- Exit code 1: File creation failed
- Exit code 2: Editor launch failed

### Command: materialize
**Purpose**: Convert placeholder to actual node
**Usage**: `pmk materialize TITLE [--parent PARENT_ID]`

**Parameters**:
- `TITLE`: Display title of placeholder to materialize (required)
- `--parent UUID`: Parent node ID to search within (optional)

**Success Response**:
```
Materialized "Future Chapter" (01234567)
Created files: 01234567.md, 01234567.notes.md
Updated binder structure
```

**Error Responses**:
- Exit code 1: Placeholder not found
- Exit code 2: File creation failed

### Command: move
**Purpose**: Reorganize binder hierarchy
**Usage**: `pmk move NODE_ID [--parent NEW_PARENT] [--position INDEX]`

**Parameters**:
- `NODE_ID`: Node to move (required)
- `--parent UUID`: New parent node (optional, defaults to root)
- `--position INT`: Position in new parent's children (optional, defaults to end)

**Success Response**:
```
Moved "Chapter 2" to position 1 under root
Updated binder structure
```

**Error Responses**:
- Exit code 1: Node not found
- Exit code 2: Invalid parent or position
- Exit code 3: Would create circular reference

### Command: remove
**Purpose**: Remove node from binder
**Usage**: `pmk remove NODE_ID [--delete-files] [--force]`

**Parameters**:
- `NODE_ID`: Node to remove (required)
- `--delete-files`: Also delete node files (optional)
- `--force`: Skip confirmation prompt (optional)

**Success Response**:
```
Removed "Chapter 1: Beginning" from binder
Files preserved: 01234567.md, 01234567.notes.md
```

**Error Responses**:
- Exit code 1: Node not found
- Exit code 2: User cancelled operation
- Exit code 3: File deletion failed

### Command: audit
**Purpose**: Check project integrity
**Usage**: `pmk audit [--fix]`

**Parameters**:
- `--fix`: Attempt to fix discovered issues (optional)

**Success Response**:
```
Project integrity check completed
✓ All nodes have valid files
✓ All references are consistent
✓ No orphaned files found
```

**Warning Response**:
```
Project integrity issues found:
⚠ PLACEHOLDER: "Future Chapter" (no associated files)
⚠ MISSING: Node 89abcdef referenced but files not found
⚠ ORPHAN: File deadbeef.md exists but not in binder
```

**Error Responses**:
- Exit code 1: Critical integrity violations found
- Exit code 2: Unable to fix issues automatically

## Exit Codes

- `0`: Success
- `1`: General error (invalid input, resource not found)
- `2`: System error (file I/O, permissions)
- `3`: User cancellation or validation failure

## Output Formats

### Standard Output
- Human-readable messages for success cases
- Structured data when --format json specified
- Progress indicators for long operations

### Standard Error
- Error messages with actionable guidance
- Warning messages for non-critical issues
- Debug information when --verbose specified

### File Output
- Modified project files (_binder.md, node files)
- Created freeform files with timestamps
- Backup files for critical operations (when applicable)

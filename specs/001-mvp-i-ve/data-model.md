# Data Model

**Feature**: Prosemark CLI Writing Project Manager MVP
**Date**: 2025-09-20

## Core Entities

### Project
**Description**: Root container for a writing project
**Fields**:
- `title`: str - Human-readable project name
- `root_path`: Path - File system location of project
- `binder_file`: Path - Location of _binder.md file
- `created`: datetime - Project creation timestamp

**Validation Rules**:
- Title must be non-empty string
- Root path must be valid directory
- Binder file must exist or be creatable

**State Transitions**: Created → Active → (optional) Archived

### Binder
**Description**: Hierarchical structure of project content
**Fields**:
- `roots`: List[BinderItem] - Top-level items in hierarchy
- `managed_content`: str - Markdown content between managed markers

**Validation Rules**:
- Must maintain tree structure (no cycles)
- All node IDs must be unique
- Parent-child relationships must be consistent

**Relationships**:
- Contains multiple BinderItems in hierarchical structure

### BinderItem
**Description**: Individual item in binder hierarchy
**Fields**:
- `display_title`: str - Human-readable title
- `node_id`: Optional[NodeId] - Reference to content node (None for placeholders)
- `children`: List[BinderItem] - Child items
- `parent`: Optional[BinderItem] - Parent item reference

**Validation Rules**:
- Display title must be non-empty
- Node ID must be valid UUIDv7 format if present
- Children list maintains order

**State Transitions**: Placeholder → Materialized Node

### NodeId
**Description**: Unique identifier for content nodes using UUIDv7
**Fields**:
- `value`: str - UUIDv7 string representation

**Validation Rules**:
- Must follow UUIDv7 format specification
- Must be unique across project
- Must be immutable once assigned

### Node
**Description**: Individual content item with metadata
**Fields**:
- `id`: NodeId - Unique identifier
- `title`: Optional[str] - Content title
- `synopsis`: Optional[str] - Multi-line content summary
- `created`: datetime - Creation timestamp
- `updated`: datetime - Last modification timestamp
- `draft_path`: Path - Location of {id}.md file
- `notes_path`: Path - Location of {id}.notes.md file

**Validation Rules**:
- ID must be valid NodeId
- Timestamps must be ISO 8601 UTC format
- File paths must be within project structure

**Relationships**:
- Referenced by BinderItem through node_id

### FreeformContent
**Description**: Timestamped writing file independent of project structure
**Fields**:
- `id`: str - UUIDv7 identifier
- `title`: Optional[str] - Optional content title
- `created`: datetime - Creation timestamp
- `file_path`: Path - Location of timestamped file

**Validation Rules**:
- Filename must follow YYYYMMDDTHHMM_{uuid7}.md pattern
- ID must be valid UUIDv7
- Created timestamp must match filename timestamp

## Data Storage Format

### Binder File (_binder.md)
```markdown
# User content above managed block

<!-- pmk:begin-binder -->
- [Chapter 1: Beginning](01234567.md)
  - [Section 1.1](89abcdef.md)
  - [Section 1.2](deadbeef.md)
- [Chapter 2: Development](cafebabe.md)
- [Future Chapter]()
<!-- pmk:end-binder -->

# User content below managed block
```

### Node Files
**Draft File ({id}.md)**:
```markdown
---
id: 01234567
title: "Chapter 1: Beginning"
synopsis: |
  Opening chapter that introduces
  the main character and setting
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Chapter 1: Beginning

Content goes here...
```

**Notes File ({id}.notes.md)**:
```markdown
---
id: 01234567
title: "Chapter 1: Beginning"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Notes for Chapter 1

Research notes, character details, etc.
```

### Freeform Files
**Filename**: `20250920T1530_01234567-89ab-cdef-0123-456789abcdef.md`
```markdown
---
id: 01234567-89ab-cdef-0123-456789abcdef
title: "Character Development Ideas"
created: 2025-09-20T15:30:00Z
---

Quick thoughts about character backstory...
```

## Domain Rules

### Hierarchy Constraints
1. No circular references in binder structure
2. Each node can appear at most once in hierarchy
3. Placeholder items can be converted to nodes but not vice versa
4. Parent-child relationships must be consistent

### File System Constraints
1. All operations must be atomic to prevent corruption
2. Content outside managed blocks must be preserved byte-for-byte
3. File paths must be relative to project root
4. Backup copies created for critical operations

### Identifier Constraints
1. Node IDs must be unique across entire project
2. UUIDv7 format ensures temporal ordering
3. IDs are immutable once assigned
4. Generated IDs must not conflict with existing ones

### Content Preservation
1. User content outside managed sections never modified
2. Frontmatter fields preserve unknown/custom values
3. Markdown content below frontmatter preserved exactly
4. File encoding and line endings maintained

## Audit Rules

### Consistency Checks
- **PLACEHOLDER**: Items with empty href in binder
- **MISSING**: Node referenced in binder but files don't exist
- **ORPHAN**: Node files exist but not referenced in binder
- **MISMATCH**: Node ID in frontmatter doesn't match filename

### Data Integrity
- All timestamps in valid ISO 8601 UTC format
- All UUIDs in valid UUIDv7 format
- All file paths within project boundaries
- All parent-child relationships are bidirectional

## Performance Characteristics

### Read Operations
- Binder parsing: O(n) where n = number of items
- Node lookup: O(1) with ID index
- Tree traversal: O(n) depth-first

### Write Operations
- Node creation: O(1) file operations
- Binder update: O(n) for structure modification
- Audit scan: O(n) for all project files

### Memory Usage
- Streaming parser for large files
- Lazy loading of node content
- Minimal memory footprint for CLI operations

# Research & Technical Decisions

**Feature**: Prosemark CLI Writing Project Manager MVP
**Date**: 2025-09-20

## Overview

Research phase for prosemark MVP based on comprehensive TDD specifications in sol files (sol-51 through sol-83). All major technical decisions are well-documented in the existing implementation roadmap.

## Key Technical Decisions

### 1. CLI Framework
**Decision**: Typer for CLI implementation
**Rationale**: Type-safe CLI framework with excellent help generation, integrates well with Python type annotations
**Alternatives considered**: Click (more complex), argparse (less type-safe)

### 2. File Format Strategy
**Decision**: Markdown files with YAML frontmatter, managed blocks in _binder.md
**Rationale**: Human-readable, editor-agnostic, Obsidian-compatible, version control friendly
**Alternatives considered**: JSON (less human-readable), custom binary format (not interoperable)

### 3. Identifier Strategy
**Decision**: UUIDv7 for node identifiers
**Rationale**: Timestamp-ordered for natural sorting, collision-resistant, stable across sessions
**Alternatives considered**: Sequential integers (not stable), UUIDv4 (no temporal ordering)

### 4. Architecture Pattern
**Decision**: Hexagonal architecture with ports and adapters
**Rationale**: Separates business logic from I/O, enables testing, supports future GUI/web interfaces
**Alternatives considered**: Layered architecture (tighter coupling), monolithic (harder to test)

### 5. File Storage Design
**Decision**: Atomic file operations with managed block preservation
**Rationale**: Prevents corruption, preserves user content outside prosemark management
**Alternatives considered**: In-place editing (corruption risk), database storage (not plain text)

### 6. Editor Integration
**Decision**: Launch user's preferred editor via subprocess
**Rationale**: Leverages existing editor expertise, supports all platforms and editors
**Alternatives considered**: Built-in editor (complex), web editor (not CLI-first)

### 7. Timestamp Format
**Decision**: ISO 8601 UTC timestamps
**Rationale**: Unambiguous, sortable, internationally standardized
**Alternatives considered**: Local timestamps (timezone confusion), Unix timestamps (not human-readable)

### 8. Testing Strategy
**Decision**: TDD with pytest, 100% coverage requirement
**Rationale**: Prevents regression, ensures reliability for writing tool
**Alternatives considered**: Manual testing (unreliable), partial coverage (regression risk)

## Implementation Patterns

### File System Adapters
- BinderRepoFs: Load/save _binder.md with managed block parsing
- NodeRepoFs: CRUD operations for {id}.md and {id}.notes.md files
- DailyRepoFs: Timestamped freeform writing file creation

### System Adapters
- FrontmatterCodec: YAML frontmatter parsing/generation
- MarkdownBinderParser: Convert between markdown lists and domain objects
- IdGeneratorUuid7: Generate UUIDv7 identifiers
- ClockSystem: ISO 8601 UTC timestamp generation
- EditorLauncher: Cross-platform editor launching
- ConsolePretty: Tree visualization with Unicode box drawing

### CLI Commands
- `pmk init`: Initialize new project with binder structure
- `pmk add`: Add nodes to hierarchy
- `pmk edit`: Launch editor for node content
- `pmk structure`: Display project tree
- `pmk write`: Create freeform writing files
- `pmk materialize`: Convert placeholders to nodes
- `pmk move`: Reorganize hierarchy
- `pmk remove`: Remove nodes with optional file deletion
- `pmk audit`: Check project integrity

## Dependencies Analysis

### Core Dependencies
- **Typer**: CLI framework with type support
- **PyYAML**: YAML parsing for frontmatter
- **uv**: Package management and environment

### Development Dependencies
- **pytest**: Testing framework
- **ruff**: Code formatting and linting
- **mypy**: Type checking
- **coverage**: Test coverage measurement

## Performance Considerations

### File I/O Optimization
- Parse only managed blocks, not entire files
- Use atomic operations for corruption prevention
- Implement efficient tree traversal for large hierarchies

### Memory Management
- Stream-based parsing for large files
- Lazy loading of node content
- Minimal memory footprint for CLI operations

## Security Considerations

### File Safety
- Atomic operations prevent partial writes
- Validation of user input (node IDs, file paths)
- Protection against path traversal attacks

### Data Integrity
- Checksums for critical operations
- Backup strategies for important files
- Comprehensive auditing for inconsistency detection

## Conclusion

All technical decisions are well-researched and documented in the sol files. The architecture supports the constitutional requirements while providing a robust foundation for the CLI writing tool. No additional research needed - ready to proceed to Phase 1 design.

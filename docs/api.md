# Prosemark API Documentation

This document provides comprehensive API documentation for the Prosemark CLI Writing Project Manager, generated from source code docstrings and interfaces.

## Architecture Overview

Prosemark follows hexagonal (ports and adapters) architecture with these main components:

- **Domain**: Core business logic and entities
- **Ports**: Abstract interfaces for external dependencies
- **Adapters**: Concrete implementations of ports
- **Application**: Use cases orchestrating domain operations
- **CLI**: Command-line interface layer

## Domain Layer

### Core Models

#### NodeId
**Location**: `src/prosemark/domain/models.py`

Unique identifier for content nodes using UUIDv7 format.

```python
@dataclass(frozen=True)
class NodeId:
    value: str  # UUIDv7 string representation
```

**Validation**: Must follow UUIDv7 format specification and be unique across project.

#### Binder
**Location**: `src/prosemark/domain/models.py`

Root aggregate representing the hierarchical project structure.

```python
@dataclass
class Binder:
    roots: list[Item]  # Top-level hierarchy items
```

**Invariants**:
- Maintains tree structure (no cycles)
- All node IDs must be unique
- Parent-child relationships must be consistent

#### Item
**Location**: `src/prosemark/domain/binder.py`

Individual item in the binder hierarchy.

```python
@dataclass
class Item:
    display_title: str                    # Human-readable title
    id: NodeId | None = None             # Reference to content node (None for placeholders)
    children: list[Item] = field(default_factory=list)  # Child items
```

**States**:
- **Placeholder**: `id` is None, represents future content
- **Materialized**: `id` is set, references actual content node

### Domain Exceptions

All exceptions inherit from `ProsemarkError` base class.

#### Binder Exceptions
- **BinderNotFoundError**: When `_binder.md` file doesn't exist
- **BinderFormatError**: When binder format is invalid
- **BinderIntegrityError**: When binder data is corrupted

#### Node Exceptions
- **NodeNotFoundError**: When referenced node doesn't exist
- **NodeAlreadyExistsError**: When creating node that already exists
- **InvalidPartError**: When invalid part specified for editing

#### System Exceptions
- **EditorError**: Base for editor-related failures
- **FileSystemError**: For file system operation failures

## Ports Layer

Ports define abstract interfaces that adapters must implement.

### BinderRepo Protocol
**Location**: `src/prosemark/ports/binder_repo.py`

Repository interface for binder persistence operations.

```python
class BinderRepo(ABC):
    @abstractmethod
    def load(self) -> Binder:
        """Load binder from storage.

        Returns:
            The loaded Binder aggregate.

        Raises:
            BinderNotFoundError: If binder file doesn't exist.
            FileSystemError: If file cannot be read.
            BinderIntegrityError: If binder data is corrupted.
        """

    @abstractmethod
    def save(self, binder: Binder) -> None:
        """Save binder to storage.

        Args:
            binder: The Binder aggregate to persist.

        Raises:
            FileSystemError: If file cannot be written.
        """
```

**Preservation Contract**: Implementations must preserve text outside managed blocks during round-trip operations.

### NodeRepo Protocol
**Location**: `src/prosemark/ports/node_repo.py`

Repository interface for node file operations.

```python
class NodeRepo(ABC):
    @abstractmethod
    def create(self, node_id: NodeId, title: str | None, synopsis: str | None) -> None:
        """Create new node files with frontmatter."""

    @abstractmethod
    def read_frontmatter(self, node_id: NodeId) -> dict[str, Any]:
        """Read frontmatter from node's draft file."""

    @abstractmethod
    def write_frontmatter(self, node_id: NodeId, frontmatter: dict[str, Any]) -> None:
        """Update frontmatter while preserving content."""

    @abstractmethod
    def open_in_editor(self, node_id: NodeId, part: str) -> None:
        """Launch editor for node content.

        Args:
            part: Content part ("draft"|"notes"|"synopsis")
        """

    @abstractmethod
    def delete(self, node_id: NodeId, delete_files: bool = False) -> None:
        """Remove node files from file system."""
```

### DailyRepo Protocol
**Location**: `src/prosemark/ports/daily_repo.py`

Repository interface for freeform writing.

```python
class DailyRepo(ABC):
    @abstractmethod
    def write_freeform(self, title: str | None = None) -> str:
        """Create timestamped freeform writing file.

        Returns:
            Created filename/path
        """
```

### Supporting Ports

#### IdGenerator Protocol
Generates unique UUIDv7 identifiers.

```python
class IdGenerator(ABC):
    @abstractmethod
    def new(self) -> NodeId:
        """Generate new UUIDv7 identifier."""
```

#### Clock Protocol
Provides timestamp generation.

```python
class Clock(ABC):
    @abstractmethod
    def now_iso(self) -> str:
        """Get current timestamp in ISO 8601 UTC format."""
```

#### EditorPort Protocol
Handles editor integration.

```python
class EditorPort(ABC):
    @abstractmethod
    def open(self, file_path: str) -> None:
        """Launch editor for specified file."""
```

#### ConsolePort Protocol
Manages console output.

```python
class ConsolePort(ABC):
    @abstractmethod
    def print(self, message: str) -> None:
        """Print message to console."""

    @abstractmethod
    def print_tree(self, binder: Binder) -> None:
        """Display binder structure as tree."""
```

#### Logger Protocol
Provides logging capabilities.

```python
class Logger(ABC):
    @abstractmethod
    def info(self, message: str) -> None: ...
    @abstractmethod
    def warn(self, message: str) -> None: ...
    @abstractmethod
    def error(self, message: str) -> None: ...
```

## Application Layer

### Use Cases

#### InitProject
**Location**: `src/prosemark/app/init_project.py`

Initialize a new prosemark writing project.

```python
class InitProject:
    def execute(self, *, project_title: str, project_path: Path | None = None) -> None:
        """Initialize a new prosemark project.

        Args:
            project_title: Title for the new project.
            project_path: Optional path for project, defaults to current directory.
        """
```

#### AddNode
**Location**: `src/prosemark/app/add_node.py`

Add new content nodes to the binder hierarchy.

```python
class AddNode:
    def execute(
        self,
        *,
        title: str,
        parent_id: NodeId | None = None,
        position: int | None = None
    ) -> NodeId:
        """Add new node to binder structure.

        Args:
            title: Display title for node.
            parent_id: Optional parent node.
            position: Optional position in parent's children.

        Returns:
            Generated node identifier.
        """
```

#### MaterializeNode
**Location**: `src/prosemark/app/materialize_node.py`

Convert placeholder items to actual content nodes.

```python
class MaterializeNode:
    def execute(
        self,
        *,
        title: str,
        parent_id: NodeId | None = None
    ) -> NodeId:
        """Convert placeholder to actual node.

        Args:
            title: Display title of placeholder.
            parent_id: Optional parent to search within.

        Returns:
            Generated node identifier.
        """
```

#### MoveNode
**Location**: `src/prosemark/app/move_node.py`

Reorganize nodes within the binder hierarchy.

```python
class MoveNode:
    def execute(
        self,
        *,
        node_id: NodeId,
        new_parent_id: NodeId | None = None,
        position: int | None = None
    ) -> None:
        """Move node within binder hierarchy.

        Args:
            node_id: Node to move.
            new_parent_id: New parent node.
            position: Position in new parent's children.
        """
```

#### RemoveNode
**Location**: `src/prosemark/app/remove_node.py`

Remove nodes from the binder structure.

```python
class RemoveNode:
    def execute(
        self,
        *,
        node_id: NodeId,
        delete_files: bool = False,
        force: bool = False
    ) -> None:
        """Remove node from binder structure.

        Args:
            node_id: Node to remove.
            delete_files: Whether to delete node files.
            force: Skip confirmation prompts.
        """
```

#### AuditProject
**Location**: `src/prosemark/app/audit_project.py`

Check project integrity and consistency.

```python
class AuditProject:
    def execute(self, *, fix_issues: bool = False) -> list[AuditIssue]:
        """Check project integrity and optionally fix issues.

        Args:
            fix_issues: Whether to attempt automatic fixes.

        Returns:
            List of discovered integrity problems.
        """
```

## Adapters Layer

### File System Adapters

#### BinderRepoFs
**Location**: `src/prosemark/adapters/binder_repo_fs.py`

File system implementation of BinderRepo using `_binder.md` files.

**Features**:
- Preserves content outside managed blocks
- Atomic file operations
- Markdown parsing with managed content sections

#### NodeRepoFs
**Location**: `src/prosemark/adapters/node_repo_fs.py`

File system implementation of NodeRepo managing `{id}.md` and `{id}.notes.md` files.

**Features**:
- YAML frontmatter parsing/generation
- Content preservation during metadata updates
- Editor integration for content editing

#### DailyRepoFs
**Location**: `src/prosemark/adapters/daily_repo_fs.py`

File system implementation creating timestamped freeform files.

**File Format**: `YYYYMMDDTHHMM_{uuid7}.md`

### System Adapters

#### FrontmatterCodec
**Location**: `src/prosemark/adapters/frontmatter_codec.py`

YAML frontmatter parsing and generation.

#### MarkdownBinderParser
**Location**: `src/prosemark/adapters/markdown_binder_parser.py`

Convert between markdown lists and domain objects.

#### IdGeneratorUuid7
**Location**: `src/prosemark/adapters/id_generator_uuid7.py`

Generate UUIDv7 identifiers with temporal ordering.

#### ClockSystem
**Location**: `src/prosemark/adapters/clock_system.py`

System clock providing ISO 8601 UTC timestamps.

#### EditorLauncherSystem
**Location**: `src/prosemark/adapters/editor_launcher_system.py`

Cross-platform editor launching via subprocess.

#### ConsolePretty
**Location**: `src/prosemark/adapters/console_pretty.py`

Console output with tree visualization using Unicode box drawing.

#### LoggerStdout
**Location**: `src/prosemark/adapters/logger_stdout.py`

Standard output logging implementation.

## CLI Layer

### Commands

All CLI commands are implemented using Typer framework with consistent error handling and user feedback.

#### `pmk init`
**Location**: `src/prosemark/cli/init.py`

Initialize new prosemark project.

```bash
pmk init --title "Project Title" [--path /project/path]
```

#### `pmk add`
**Location**: `src/prosemark/cli/add.py`

Add new content nodes.

```bash
pmk add "Node Title" [--parent parent_id] [--position index]
```

#### `pmk edit`
**Location**: `src/prosemark/cli/edit.py`

Edit node content in preferred editor.

```bash
pmk edit node_id --part {draft|notes|synopsis}
```

#### `pmk structure`
**Location**: `src/prosemark/cli/structure.py`

Display project hierarchy.

```bash
pmk structure [--format {tree|json}]
```

#### `pmk write`
**Location**: `src/prosemark/cli/write.py`

Create freeform writing files.

```bash
pmk write ["Optional Title"]
```

#### `pmk materialize`
**Location**: `src/prosemark/cli/materialize.py`

Convert placeholders to content nodes.

```bash
pmk materialize "Placeholder Title" [--parent parent_id]
```

#### `pmk move`
**Location**: `src/prosemark/cli/move.py`

Reorganize hierarchy structure.

```bash
pmk move node_id [--parent new_parent] [--position index]
```

#### `pmk remove`
**Location**: `src/prosemark/cli/remove.py`

Remove nodes from project.

```bash
pmk remove node_id [--delete-files] [--force]
```

#### `pmk audit`
**Location**: `src/prosemark/cli/audit.py`

Check project integrity.

```bash
pmk audit [--fix]
```

### Exit Codes

- `0`: Success
- `1`: General error (invalid input, resource not found)
- `2`: System error (file I/O, permissions)
- `3`: User cancellation or validation failure

## Data Formats

### Binder File Format

The `_binder.md` file contains managed content between markers:

```markdown
# Project Title

User content above managed section.

<!-- pmk:begin-binder -->
- [Chapter 1: Beginning](01234567.md)
  - [Section 1.1](89abcdef.md)
  - [Future Section]()
- [Chapter 2: Development](cafebabe.md)
<!-- pmk:end-binder -->

User content below managed section.
```

### Node File Formats

**Content file ({id}.md)**:
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

**Notes file ({id}.notes.md)**:
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

### Freeform File Format

**Filename**: `20250920T1530_01234567-89ab-cdef-0123-456789abcdef.md`

```markdown
---
id: 01234567-89ab-cdef-0123-456789abcdef
title: "Optional Title"
created: 2025-09-20T15:30:00Z
---

Freeform content...
```

## Extension Points

### Custom Adapters

Implement port interfaces to create custom adapters:

- **Alternative Storage**: Database, cloud storage, etc.
- **Different Editors**: IDE integration, web editors
- **Output Formats**: Different console formatting, export formats
- **Identity Schemes**: Alternative ID generation strategies

### Use Case Composition

Combine use cases for complex workflows:

```python
# Example: Bulk operations
def bulk_add_chapters(titles: list[str], parent_id: NodeId) -> list[NodeId]:
    add_node = AddNode(...)
    return [add_node.execute(title=title, parent_id=parent_id) for title in titles]
```

### Custom Validation

Extend domain models with additional validation:

```python
# Example: Custom node policies
class ProjectSpecificNodeValidator:
    def validate_title_format(self, title: str) -> bool:
        # Custom title validation logic
        pass
```

## Testing

### Test Adapters

The project includes fake adapters for testing:

- **FakeConsole**: In-memory console for testing output
- **FakeLogger**: Captured logging for test verification
- **FakeNodeRepo**: In-memory node storage for tests
- **FakeStorage**: Mock file system operations

### Test Categories

- **Contract Tests**: Verify port interface compliance
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete workflows
- **Performance Tests**: Ensure scalability requirements

## Migration and Compatibility

### File Format Evolution

The API supports backward-compatible changes:

- New frontmatter fields are ignored by older versions
- Content outside managed blocks is preserved
- UUIDv7 format ensures forward compatibility

### Deprecation Policy

- Breaking changes require major version increment
- Deprecated features include migration guides
- Support matrix documented for each release

## Performance Characteristics

### Time Complexity

- **Binder parsing**: O(n) where n = number of items
- **Node lookup**: O(1) with ID index
- **Tree traversal**: O(n) depth-first

### Memory Usage

- Streaming parser for large files
- Lazy loading of node content
- Minimal memory footprint for CLI operations

### File I/O

- Atomic operations prevent corruption
- Efficient parsing of managed blocks only
- Optimized for typical project sizes (hundreds of nodes)

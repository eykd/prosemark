# Domain Interface Contracts

**Feature**: Prosemark CLI Writing Project Manager MVP
**Date**: 2025-09-20

## Port Interfaces (Hexagonal Architecture)

### BinderRepo Protocol
**Purpose**: Repository interface for binder persistence

```python
class BinderRepo(Protocol):
    def load(self) -> Binder:
        """Load binder structure from _binder.md file.

        Returns:
            Binder: Parsed binder structure

        Raises:
            BinderNotFoundError: When _binder.md doesn't exist
            BinderFormatError: When managed block is malformed
        """

    def save(self, binder: Binder) -> None:
        """Save binder structure to _binder.md file.

        Args:
            binder: Binder structure to save

        Raises:
            FileSystemError: When file cannot be written
        """
```

### NodeRepo Protocol
**Purpose**: Repository interface for node file operations

```python
class NodeRepo(Protocol):
    def create(self, node_id: NodeId, title: Optional[str], synopsis: Optional[str]) -> None:
        """Create new node files with frontmatter.

        Args:
            node_id: Unique identifier for node
            title: Optional node title
            synopsis: Optional node synopsis

        Raises:
            NodeAlreadyExistsError: When node files already exist
            FileSystemError: When files cannot be created
        """

    def read_frontmatter(self, node_id: NodeId) -> Dict[str, Any]:
        """Read frontmatter from node's draft file.

        Args:
            node_id: Node identifier

        Returns:
            Dict containing frontmatter fields

        Raises:
            NodeNotFoundError: When node files don't exist
            FrontmatterFormatError: When YAML is malformed
        """

    def write_frontmatter(self, node_id: NodeId, frontmatter: Dict[str, Any]) -> None:
        """Update frontmatter while preserving content.

        Args:
            node_id: Node identifier
            frontmatter: New frontmatter values

        Raises:
            NodeNotFoundError: When node files don't exist
            FileSystemError: When files cannot be written
        """

    def open_in_editor(self, node_id: NodeId, part: str) -> None:
        """Launch editor for node content.

        Args:
            node_id: Node identifier
            part: Content part ("draft"|"notes"|"synopsis")

        Raises:
            NodeNotFoundError: When node files don't exist
            InvalidPartError: When part is not supported
            EditorError: When editor cannot be launched
        """

    def delete(self, node_id: NodeId, delete_files: bool = False) -> None:
        """Remove node files from file system.

        Args:
            node_id: Node identifier
            delete_files: Whether to actually delete files

        Raises:
            FileSystemError: When files cannot be deleted
        """
```

### DailyRepo Protocol
**Purpose**: Repository interface for freeform writing

```python
class DailyRepo(Protocol):
    def write_freeform(self, title: Optional[str] = None) -> str:
        """Create timestamped freeform writing file.

        Args:
            title: Optional title for content

        Returns:
            str: Created filename/path

        Raises:
            FileSystemError: When file cannot be created
        """
```

### IdGenerator Protocol
**Purpose**: Interface for generating unique identifiers

```python
class IdGenerator(Protocol):
    def new(self) -> NodeId:
        """Generate new UUIDv7 identifier.

        Returns:
            NodeId: New unique identifier
        """
```

### Clock Protocol
**Purpose**: Interface for timestamp generation

```python
class Clock(Protocol):
    def now_iso(self) -> str:
        """Get current timestamp in ISO 8601 UTC format.

        Returns:
            str: Current timestamp (e.g., "2025-09-20T15:30:00Z")
        """
```

### EditorPort Protocol
**Purpose**: Interface for editor integration

```python
class EditorPort(Protocol):
    def open(self, file_path: str) -> None:
        """Launch editor for specified file.

        Args:
            file_path: Absolute path to file to edit

        Raises:
            EditorNotFoundError: When editor executable not found
            EditorLaunchError: When editor fails to launch
        """
```

### ConsolePort Protocol
**Purpose**: Interface for console output

```python
class ConsolePort(Protocol):
    def print(self, message: str) -> None:
        """Print message to console.

        Args:
            message: Text to display
        """

    def print_tree(self, binder: Binder) -> None:
        """Display binder structure as tree.

        Args:
            binder: Binder structure to visualize
        """
```

### Logger Protocol
**Purpose**: Interface for logging operations

```python
class Logger(Protocol):
    def info(self, message: str) -> None:
        """Log informational message.

        Args:
            message: Information to log
        """

    def warn(self, message: str) -> None:
        """Log warning message.

        Args:
            message: Warning to log
        """

    def error(self, message: str) -> None:
        """Log error message.

        Args:
            message: Error to log
        """
```

## Use Case Interfaces

### InitProject Use Case
```python
def init_project(title: str, path: Optional[str] = None) -> None:
    """Initialize new prosemark project.

    Args:
        title: Project title
        path: Optional project directory

    Raises:
        ProjectAlreadyExistsError: When project already exists
        FileSystemError: When directory cannot be created
    """
```

### AddNode Use Case
```python
def add_node(
    title: str,
    parent_id: Optional[NodeId] = None,
    position: Optional[int] = None
) -> NodeId:
    """Add new node to binder structure.

    Args:
        title: Display title for node
        parent_id: Optional parent node
        position: Optional position in parent's children

    Returns:
        NodeId: Generated node identifier

    Raises:
        ParentNotFoundError: When parent_id doesn't exist
        InvalidPositionError: When position is out of range
    """
```

### MaterializeNode Use Case
```python
def materialize_node(
    title: str,
    parent_id: Optional[NodeId] = None
) -> NodeId:
    """Convert placeholder to actual node.

    Args:
        title: Display title of placeholder
        parent_id: Optional parent to search within

    Returns:
        NodeId: Generated node identifier

    Raises:
        PlaceholderNotFoundError: When placeholder doesn't exist
        FileSystemError: When node files cannot be created
    """
```

### MoveNode Use Case
```python
def move_node(
    node_id: NodeId,
    new_parent_id: Optional[NodeId] = None,
    position: Optional[int] = None
) -> None:
    """Move node within binder hierarchy.

    Args:
        node_id: Node to move
        new_parent_id: New parent node
        position: Position in new parent's children

    Raises:
        NodeNotFoundError: When node_id doesn't exist
        CircularReferenceError: When move would create cycle
        InvalidPositionError: When position is out of range
    """
```

### RemoveNode Use Case
```python
def remove_node(
    node_id: NodeId,
    delete_files: bool = False,
    force: bool = False
) -> None:
    """Remove node from binder structure.

    Args:
        node_id: Node to remove
        delete_files: Whether to delete node files
        force: Skip confirmation prompts

    Raises:
        NodeNotFoundError: When node_id doesn't exist
        UserCancelledError: When user cancels operation
        FileSystemError: When files cannot be deleted
    """
```

### AuditProject Use Case
```python
def audit_project(fix_issues: bool = False) -> List[AuditIssue]:
    """Check project integrity and optionally fix issues.

    Args:
        fix_issues: Whether to attempt automatic fixes

    Returns:
        List[AuditIssue]: Discovered integrity problems

    Raises:
        FileSystemError: When files cannot be accessed
    """
```

## Exception Hierarchy

### Domain Exceptions
```python
class ProsemarkError(Exception):
    """Base exception for all prosemark errors."""

class BinderError(ProsemarkError):
    """Base exception for binder-related errors."""

class BinderNotFoundError(BinderError):
    """Raised when _binder.md file is not found."""

class BinderFormatError(BinderError):
    """Raised when binder format is invalid."""

class NodeError(ProsemarkError):
    """Base exception for node-related errors."""

class NodeNotFoundError(NodeError):
    """Raised when referenced node doesn't exist."""

class NodeAlreadyExistsError(NodeError):
    """Raised when creating node that already exists."""

class InvalidPartError(NodeError):
    """Raised when invalid part specified for editing."""

class EditorError(ProsemarkError):
    """Base exception for editor-related errors."""

class EditorNotFoundError(EditorError):
    """Raised when editor executable is not found."""

class EditorLaunchError(EditorError):
    """Raised when editor fails to launch."""

class FileSystemError(ProsemarkError):
    """Raised for file system operation failures."""
```

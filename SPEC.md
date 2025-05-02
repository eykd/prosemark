# Prosemark Specification

## Overview

Prosemark is a Python application for planning, organizing, and writing stories. It provides a hierarchical document structure similar to Scrivener, with Markdown as the primary formatting language. The application follows a Hexagonal (Ports and Adapters) architecture to separate business logic from I/O concerns.

## Core Concepts

### Document Hierarchy

- Documents are organized in a hierarchical tree structure
- Each node in the hierarchy represents a document component
- Nodes can be nested to any depth
- The hierarchy can be reorganized by moving nodes

### Node Structure

Each node in the hierarchy may contain:
- **Main Text**: The primary content of the node
- **Notecard**: A brief summary or description of the node's purpose
- **Notes**: Additional information, research, or comments about the node
- **Metadata**: Information about the node (creation date, status, tags, etc.)

### Markdown Formatting

- All document content uses Markdown for formatting
- Support for standard Markdown syntax (headers, lists, emphasis, links, etc.)
- Potential for extended Markdown features (tables, footnotes, etc.)

## Architecture

### Core Domain Entities

#### Project
- **Attributes**:
  - `name`: String - The name of the project
  - `description`: String - A description of the project
  - `root_node`: Node - The top-level node of the document hierarchy
  - `metadata`: Dict - Project-level metadata (creation date, author, etc.)
- **Methods**:
  - `create_node(parent_id, title)` - Creates a new node under the specified parent
  - `move_node(node_id, new_parent_id, position)` - Relocates a node in the hierarchy
  - `delete_node(node_id)` - Removes a node and its children
  - `get_node(node_id)` - Retrieves a specific node
  - `get_structure()` - Returns the complete document hierarchy

#### Node
- **Attributes**:
  - `id`: String - Unique identifier (Zettelkasten-style timestamp in YYYYMMDDHHmm format, e.g., "202405101023")
    - Automatically generated when a node is created
    - Used as the primary identifier for nodes in the system
    - Ensures chronological ordering and uniqueness
    - When used in filenames, combined with the node title (e.g., "202405101023 Chapter 1 Beginning.md")
    - Spaces in titles are preserved in filenames to maintain readability
    - Special characters in titles are handled appropriately for filesystem compatibility
  - `title`: String - The title of the node
  - `notecard`: String - Brief description or summary (Markdown)
  - `content`: String - Main text content (Markdown)
  - `notes`: String - Additional notes or research (Markdown)
  - `metadata`: Dict - Node-specific metadata (status, tags, etc.)
  - `parent`: Node - Reference to parent node
  - `children`: List[Node] - Ordered list of child nodes
- **Methods**:
  - `add_child(node)` - Adds a child node
  - `remove_child(node_id)` - Removes a child node
  - `get_child(node_id)` - Retrieves a specific child node by ID
  - `move_child(node_id, position)` - Reorders children
  - `update_content(content)` - Updates the main content
  - `update_notecard(notecard)` - Updates the notecard
  - `update_notes(notes)` - Updates the notes section
  - `get_content()` - Retrieves the main content
  - `get_notecard()` - Retrieves the notecard
  - `get_notes()` - Retrieves the notes section
  - `get_ancestry()` - Returns a list of nodes from root to this node's parent (excludes the current node itself)

#### Relationships
- A Project contains exactly one root Node
- Each Node (except the root) has exactly one parent Node
- A Node can have zero or more child Nodes
- Nodes form a tree structure with no cycles

### Hexagonal (Ports and Adapters)

The application follows a hexagonal architecture with:

1. **Core Domain**:
   - Business entities (Project, Node, etc.) as defined above
   - Business logic for manipulating the document hierarchy
   - Pure domain logic with no dependencies on external systems

2. **Ports**:
   - Interfaces defining how the core domain interacts with external systems
   - Primary ports: APIs exposed by the domain to the outside
   - Secondary ports: APIs required by the domain from the outside

3. **Adapters**:
   - Implementations of ports that connect to specific technologies
   - UI adapters (CLI, potential GUI)
   - Storage adapters (file system, potential database)
   - Export adapters (HTML, Word, RTF, EPUB)

## Storage Format

The application will support multiple storage formats through different adapters. The primary considerations for storage include:
- Performance for large document hierarchies
- Ease of synchronization across devices
- Human readability of stored content
- Version control compatibility

### Storage Options

#### Option 1: Individual Markdown Files (Default)
- Store each node as a separate Markdown file
- Use Zettelkasten-style naming (timestamp-based IDs) for files
- Organize the hierarchy using a main Outline/Binder markdown file
- Preserve metadata, notecards, and notes using a consistent format

```
project/
  ├── _binder.md           # Main outline/structure file
  ├── 202405101023 Chapter 1 Beginning.md     # Document node with Zettelkasten-style name
  ├── 202405101045 Scene 1 1.md               # Another document node
  └── ...
```

**Advantages**:
- Human-readable files
- Easy to edit outside the application
- Works well with version control
- Simple to implement

**Disadvantages**:
- May become unwieldy with very large projects
- Requires additional synchronization consideration
- Structure changes require updating multiple files

#### Option 2: SQLite Database
- Store all project data in a single SQLite database file
- Separate tables for nodes, structure, and metadata
- Binary storage with transaction support

**Advantages**:
- Better performance for large projects
- Atomic transactions for data integrity
- Simpler synchronization (single file)
- Efficient querying and filtering

**Disadvantages**:
- Not human-readable without the application
- More complex implementation
- Requires migration strategy for schema changes

#### Option 3: JSON/YAML Bundle
- Store entire project as a structured JSON or YAML file
- Hierarchical representation matching the document structure
- Include all metadata, content, and relationships

**Advantages**:
- Single file for easier synchronization
- Still somewhat human-readable
- Simpler than database implementation
- Good compatibility with many tools

**Disadvantages**:
- Performance issues with very large projects
- Entire file must be read/written for any change
- Potential for merge conflicts in version control

The storage adapter interface will be designed to allow switching between these formats or implementing new ones as needed.

### File Formats

#### Individual Markdown Node Format

When using the individual files approach, each node file will follow this format, using a YAML metadata header:
```markdown
---
type: node
title: Chapter 1: Beginning
created: 2024-05-10T10:23:00Z
status: Draft
tags: character, protagonist
notecard: 202405101023 Chapter 1 Beginning _notecard.md
notes: 202405101023 Chapter 1 Beginning _notes.md
---

The primary text content of the node goes here.

This can be multiple paragraphs with full Markdown formatting.
```

#### Binder/Outline Format

For the individual files approach, the binder file defines the hierarchical structure:

```markdown
# Project Title

## Structure
- [Chapter 1: Beginning](202405101023 Chapter 1 Beginning.md)
  - [Scene 1.1](202405101045 Scene 1 1.md)
  - [Scene 1.2](202405101130 Scene 1 2.md)
- [Chapter 2: Middle](202405101210 Chapter 2 Middle.md)
  - [Scene 2.1](202405101245 Scene 2 1.md)
```

#### Database Schema (SQLite Option)

When using the SQLite option, the database will include these primary tables:
- `nodes`: Stores node content, notecards, notes
- `structure`: Defines parent-child relationships and ordering
- `metadata`: Stores key-value metadata for nodes and projects

#### JSON/YAML Structure

When using the JSON/YAML option, the structure will follow this pattern:
```json
{
  "project": {
    "name": "Project Title",
    "description": "Project description",
    "metadata": { ... }
  },
  "nodes": {
    "root": {
      "id": "root",
      "title": "Project Title",
      "children": ["202405101023", "202405101210"],
      "notecard": "",
      "content": "",
      "notes": "",
      "metadata": { ... }
    },
    "202405101023": {
      "id": "202405101023",
      "title": "Chapter 1: Beginning",
      "children": ["202405101045", "202405101130"],
      "notecard": "Brief description",
      "content": "Main content...",
      "notes": "Additional notes...",
      "metadata": { ... }
    },
    ...
  }
}
```

### Storage Selection

The storage format will be configurable:
- Default to individual Markdown files for new projects
- Allow conversion between formats
- Support format selection at project creation
- Provide migration tools for existing projects

### Format Conversion

The application will support converting existing projects between different storage formats:

#### Conversion Capabilities
- Convert from any supported format to any other supported format
- Preserve all content, structure, and metadata during conversion
- Provide both CLI and UI options for format migration
- Allow selective backup before conversion

#### Conversion Process
1. **Validation**: Verify the integrity of the source project
2. **Backup**: Create an automatic backup of the original project
3. **Conversion**: Transform the project to the target format
4. **Verification**: Validate the converted project for completeness
5. **Cleanup**: Remove temporary files and update project references

#### Implementation Considerations
- Implement adapters with bidirectional conversion support
- Use a common intermediate representation during conversion
- Handle edge cases like unsupported features in target formats
- Provide detailed logs of the conversion process
- Include rollback capability if conversion fails

## Compilation

The application will support compiling selected portions of the document hierarchy into various output formats:
- Markdown
- HTML
- Word document (.docx)
- RTF
- EPUB

Compilation will:
- Follow the hierarchical structure
- Include only selected nodes
- Apply formatting according to the output format
- Optionally include or exclude notecards and notes

## User Interfaces

### Command Line Interface (CLI)

Initial implementation will provide a CLI for:
- Creating new projects
- Adding/editing/removing nodes
- Reorganizing the hierarchy
- Compiling to output formats

### Potential Future Interfaces

- GUI application
- Web interface
- Editor integrations

## Development Roadmap

### Phase 1: Core Domain (Current Priority)
- Define domain entities and relationships as specified above
  - Implement Project and Node entities first
  - Focus on pure business logic with no external dependencies
  - Follow hexagonal architecture principles from CONVENTIONS.md
- Implement business logic for document manipulation
- Define the following ports:
  - **Storage Port**: Interface for persisting and retrieving projects
  - **UI Port**: Interface for user interaction
  - **Export Port**: Interface for compiling to different formats

### Phase 2: Initial Adapters
- Implement Markdown file storage adapter (default option)
- Develop basic CLI
- Create simple compilation adapter for Markdown output

### Phase 3: Enhanced Features
- Add support for additional output formats
- Implement search functionality
- Add version control integration
- Develop additional storage adapters (SQLite, JSON/YAML)

### Phase 4: Advanced Features
- Implement collaboration features
- Add statistics and analysis tools
- Develop additional UI options
- Create synchronization mechanisms for cross-device usage

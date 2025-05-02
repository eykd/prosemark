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
  - `id`: String - Unique identifier (Zettelkasten-style timestamp)
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
  - `move_child(node_id, position)` - Reorders children
  - `update_content(content)` - Updates the main content
  - `update_notecard(notecard)` - Updates the notecard
  - `update_notes(notes)` - Updates the notes section

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

The initial storage adapter will:
- Store documents as plain Markdown text files
- Use Zettelkasten-style naming for individual files
- Organize the hierarchy using a main Outline/Binder markdown file
- Preserve metadata, notecards, and notes using a consistent format

### File Structure

```
project/
  ├── binder.md           # Main outline/structure file
  ├── 202405101023.md     # Document node with Zettelkasten-style name
  ├── 202405101045.md     # Another document node
  └── ...
```

### Node File Format

Each node file will follow a consistent format:
```markdown
# Title of the Node

## Notecard
Brief description or purpose of this node.

## Main Content
The primary text content of the node goes here.
This can be multiple paragraphs with full Markdown formatting.

## Notes
Additional notes, research, or comments about this node.

## Metadata
- Created: 2024-05-10T10:23:00Z
- Status: Draft
- Tags: character, protagonist
```

### Binder/Outline Format

The binder file defines the hierarchical structure:
```markdown
# Project Title

## Structure
- [Chapter 1: Beginning](202405101023.md)
  - [Scene 1.1](202405101045.md)
  - [Scene 1.2](202405101130.md)
- [Chapter 2: Middle](202405101210.md)
  - [Scene 2.1](202405101245.md)
```

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

### Phase 1: Core Domain
- Define domain entities and relationships as specified above
- Implement business logic for document manipulation
- Define the following ports:
  - **Storage Port**: Interface for persisting and retrieving projects
  - **UI Port**: Interface for user interaction
  - **Export Port**: Interface for compiling to different formats

### Phase 2: Initial Adapters
- Implement Markdown file storage adapter
- Develop basic CLI
- Create simple compilation adapter for Markdown output

### Phase 3: Enhanced Features
- Add support for additional output formats
- Implement search functionality
- Add version control integration

### Phase 4: Advanced Features
- Implement collaboration features
- Add statistics and analysis tools
- Develop additional UI options

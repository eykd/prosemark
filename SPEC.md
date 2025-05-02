# Prosemark Specification - Vertical Slice

## Overview

Prosemark is a Python application for planning, organizing, and writing stories. This specification focuses on a vertical slice of functionality that includes basic management of project binder and documents through a command line application (implemented with the `click` framework), with individual markdown files as the only storage option.

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
  - `get_structure()` - Returns the complete document hierarchy as a tree-like structure

#### Node
- **Attributes**:
  - `id`: String - Unique identifier (Zettelkasten-style timestamp in YYYYMMDDHHmm format)
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
  - `update_title(title)` - Updates the node's title
  - `get_content()` - Retrieves the main content
  - `get_notecard()` - Retrieves the notecard
  - `get_notes()` - Retrieves the notes section

#### Relationships
- A Project contains exactly one root Node
- Each Node (except the root) has exactly one parent Node
- A Node can have zero or more child Nodes
- Nodes form a tree structure with no cycles

### Hexagonal (Ports and Adapters)

For this vertical slice, we'll implement a simplified version of the hexagonal architecture:

1. **Core Domain**:
   - Business entities (Project, Node) as defined above
   - Business logic for manipulating the document hierarchy

2. **Ports**:
   - Storage Port: Interface for persisting and retrieving projects
   - CLI Port: Interface for command-line interaction

3. **Adapters**:
   - CLI Adapter: Implementation using the `click` framework
   - Markdown File Adapter: Implementation for file-based storage

### Persistence Layer

For this vertical slice, we'll implement a simplified persistence layer:

#### ProjectRepository
- **Interface**:
  - `save(project)` - Persists a project to storage
  - `load(project_id)` - Loads a project from storage
  - `list_projects()` - Lists available projects
  - `create_project(name, description)` - Creates a new empty project

#### MarkdownFileAdapter
Implements the ProjectRepository interface using individual Markdown files.

## Storage Format

For this vertical slice, we'll only implement the Individual Markdown Files storage option:

### Individual Markdown Files
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

### File Formats

#### Individual Markdown Node Format

Each node file will follow this format, using a YAML metadata header:
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

#### Notecard and Notes File Format

Associated notecard and notes files follow a consistent naming convention and structure:

**Notecard Files**:
- Named with the node's ID and title followed by `_notecard.md`
- Example: `202405101023 Chapter 1 Beginning _notecard.md`
- Contains a simple Markdown document with the notecard content

**Notes Files**:
- Named with the node's ID and title followed by `_notes.md`
- Example: `202405101023 Chapter 1 Beginning _notes.md`
- Contains a Markdown document with research, references, or author notes

#### Binder/Outline Format

The binder file defines the hierarchical structure:

```markdown
---
title: Project Title
---

## Structure
- [Chapter 1: Beginning](202405101023 Chapter 1 Beginning.md)
  - [Scene 1.1](202405101045 Scene 1 1.md)
  - [Scene 1.2](202405101130 Scene 1 2.md)
- [Chapter 2: Middle](202405101210 Chapter 2 Middle.md)
  - [Scene 2.1](202405101245 Scene 2 1.md)
```

## Command Line Interface (CLI)

The CLI will be implemented using the `click` framework and will provide the following commands:

### Project Management
- `prosemark init [name]` - Create a new project
- `prosemark list` - List available projects
- `prosemark open [project]` - Open a project

### Node Management
- `prosemark add [parent_id] [title]` - Add a new node
- `prosemark remove [node_id]` - Remove a node
- `prosemark move [node_id] [new_parent_id] [position]` - Move a node
- `prosemark show [node_id]` - Display node content
- `prosemark edit [node_id]` - Edit node content (opens in default editor)
- `prosemark structure` - Display the project structure

## Development Roadmap

### Phase 1: Core Domain Implementation
- Implement Project and Node entities
- Implement basic business logic for document manipulation

### Phase 2: Storage Implementation
- Implement Markdown file storage adapter
- Implement project repository

### Phase 3: CLI Implementation
- Implement CLI commands using `click`
- Connect CLI to core domain and storage

### Phase 4: Testing and Refinement
- Comprehensive testing of the vertical slice
- Refinement based on user feedback
- Documentation

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

### Hexagonal (Ports and Adapters)

The application follows a hexagonal architecture with:

1. **Core Domain**:
   - Business entities (Document, Node, etc.)
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
- Define domain entities and relationships
- Implement business logic for document manipulation
- Define ports for storage and UI

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

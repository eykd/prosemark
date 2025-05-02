# Prosemark

Prosemark is a command-line tool for planning, organizing, and writing stories using a hierarchical document structure.

## Overview

Prosemark helps writers organize their work by breaking down documents into a hierarchical structure of nodes. Each node can contain main content, a notecard (brief summary), and notes (additional information or research).

This project implements a vertical slice of functionality focused on basic project and document management through a command-line interface, with storage in individual Markdown files.

## Features

- **Hierarchical Document Structure**: Organize your writing into a tree of nodes
- **Markdown-Based**: All content is stored in standard Markdown files
- **Notecard System**: Each document node can have an associated notecard and notes
- **Command-Line Interface**: Manage your project through simple CLI commands

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/prosemark.git
cd prosemark

# Install the package in development mode
pip install -e .
```

## Usage

Prosemark uses a command-line interface with the following commands:

### Project Management

```bash
# Create a new project in the current directory
prosemark init "My Novel"
```

### Node Management

```bash
# Add a new node under a parent node
prosemark add 202405101023 "Chapter 2: The Journey Begins"

# Remove a node and its children
prosemark remove 202405101045

# Move a node to a new parent at a specific position
prosemark move 202405101045 202405101023 2

# Display node content
prosemark show 202405101023

# Edit node content in your default editor
prosemark edit 202405101023

# Display the project structure
prosemark structure
```

## File Structure

Prosemark organizes your project with the following file structure:

```
my-project/
  ├── _binder.md                              # Main outline/structure file
  ├── 202405101023 Chapter 1 Beginning.md     # Document node
  ├── 202405101023 Chapter 1 Beginning _notecard.md  # Notecard for the node
  ├── 202405101023 Chapter 1 Beginning _notes.md     # Notes for the node
  ├── 202405101045 Scene 1 1.md               # Another document node
  └── ...
```

## Development

Prosemark is built with:

- Python 3.13+
- Pydantic for data validation
- Click for the command-line interface

To set up the development environment:

```bash
# Install development dependencies
pip install -e ".[dev,test]"

# Run tests
pytest
```

## License

[MIT License](LICENSE.md)

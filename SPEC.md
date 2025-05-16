# Prosemark CLI Tool Specification

## 1. Introduction

### 1.1 Overview
Prosemark is a command-line interface (CLI) tool designed to manage writing projects using markdown files. It combines the organizational power and features of Scrivener with the flexibility and interoperability of plain text markdown files. The primary command name is `pmk`.

### 1.2 Core Principles
1. **Open Format**: All content stored in standard markdown files
2. **Flexibility**: Works with existing markdown files and directories
3. **Power**: Provides advanced writing project management features
4. **Interoperability**: Compatible with tools like Obsidian and Zettelkasten methodology
5. **Performance**: Handles large projects with hundreds of files efficiently
6. **Simplicity**: Maintains a flat file structure with internal linking for organization

### 1.3 Technology Stack
- **Implementation Language**: Python
- **Dependencies**: Markdown parsing libraries, YAML processing, Git integration, Terminal UI components

### 1.4 Licensing
- **License**: Considering GPL (GNU General Public License)
- **Documentation License**: Creative Commons for documentation

## 2. Project Structure and Organization

### 2.1 Binder System
- Uses a central `_binder.md` file to organize project structure
- Contains markdown links to individual files in a hierarchical outline
- Manually editable or automatically generated/updated
- Named with underscore prefix for lexicographic sorting priority
- Provides visual representation of the project's structure

### 2.2 File Organization
- **Flat File Structure**: Avoids nested folder hierarchies
- Internal linking for logical organization rather than physical folders
- Compatible with tools like Obsidian
- Flexible organizational schemes

### 2.3 Document Operations
- **Adding**: Adding new documents to the project
- **Editing**: Opening documents in the default text editor
- **Moving**: Relocating documents within the binder structure
- **Removing**: Removing documents from the binder or project
- **Displaying**: Showing document content in the terminal
- **Visualizing**: Viewing the project structure as a tree

## 3. Content Creation and Management

### 3.1 Writing Tools
- **Interactive Writing Mode**: Distraction-free writing environment in the terminal
- **Session Tracking**: Timer and statistics for writing sessions
- **Templates**: Built-in and custom templates for new documents
- **Editor Integration**: Configurable integration with text editors

### 3.2 Note Cards System
- Lightweight units for planning and organizing content
- Represent scenes, chapters, arguments, or key points
- Include title, synopsis, and status information
- Color-coding and labeling capabilities
- Rearrangeable for planning and outlining
- Linkable to full document sections

### 3.3 Research Management
- Structured system for storing reference materials
- Support for various research content types (citations, quotes, excerpts)
- Tagging and categorization system
- Searchable across all research materials
- Linking research notes to specific document sections

### 3.4 Metadata and Tracking
- **YAML Frontmatter**: For document metadata
  - Standard fields: id, title, creation date, etc.
  - Custom fields configurable by the user
- **Statistics Tracking**:
  - Word counts (total and per-file)
  - Time spent writing
  - Session statistics
  - Progress toward goals (daily, weekly)
  - 12 Week Year integration for scorecard metrics

### 3.5 Collaboration Features
- **Comment System**: Using `//` syntax in markdown files
- **Author Tracking**: Attribution in YAML frontmatter
- **Version Control**: Git integration for collaboration

## 4. Output and Compilation

### 4.1 Compilation System
- Compiles project files into various output formats
- Supports HTML, RTF/DOCX, EPUB, PDF
- Custom compilation settings and templates
- Integration with Pandoc for document conversion

### 4.2 Output Customization
- Control over which files to include
- Ordering and organization in compiled output
- Style and formatting options
- Comment inclusion/exclusion options

## 5. Integration and Enhancement

### 5.1 Version Control
- Git integration for version control
- Automated commit functionality (similar to flashbake)
- Session-based commits to track writing progress
- Branch management for different draft versions

### 5.2 AI Integration
- Connection to LLM APIs (Anthropic, OpenAI)
- Customizable prompts for brainstorming, outlining, content suggestions
- Editing assistance and feedback

### 5.3 External Tool Integration
- **Pandoc**: For document conversion
- **Markdown Editors**: Compatible with Obsidian and other editors
- **Cloud Storage**: Works with Dropbox, Google Drive, etc.

## 6. Command Interface

### 6.1 Core Commands
- `pmk init` - Initialize a new project
- `pmk add` - Add a new document to the project
- `pmk edit` - Edit document content in the default text editor
- `pmk move` - Move a document to a new location in the binder structure
- `pmk remove` - Remove a document from the project or binder
- `pmk show` - Display the contents of a document
- `pmk structure` - Display the project structure and organization

### 6.2 Writing and Compilation Commands
- `pmk compile` - Compile the project to an output format
- `pmk stats` - Display project statistics
- `pmk session` - Start a writing session

### 6.3 Support Commands
- `pmk ai` - Access AI assistance features
- `pmk sync` - Synchronize with version control
- `pmk card` - Manage note cards
- `pmk notes` - Manage research notes

### 6.4 Command Structure
- All commands operate on the current directory by default
- Option to specify alternate directory using `--data-dir`
- Imperative mood for all commands (create, update, delete)
- Consistent option patterns across commands

## 7. Technical Implementation

### 7.1 Installation
- **Package Managers**: pip (Python), Homebrew (macOS), Chocolatey (Windows)
- **Dependencies**: Minimal external dependencies to simplify installation

### 7.2 Configuration System
- **Command Line Arguments**: For immediate settings
- **Environment Variables**: For system-level configurations
- **Global Config File**: For user preferences (YAML format)
- **Document-Specific Settings**: Via YAML frontmatter
- **Project Config**: Project-specific settings

### 7.3 Project Initialization
- Creates `_binder.md` file as the central organization document
- Offers template selection for project types
- Sets up basic project metadata
- Initializes Git repository (optional)
- Support for existing directories with markdown files

### 7.4 Platform Support
- Windows, macOS, and Linux

### 7.5 Performance Considerations
- Optimized for large projects (hundreds of files)
- Efficient search and navigation capabilities
- Initial focus on functionality rather than optimization

### 7.6 Security
- Secure storage of LLM API keys
- Optional AI features
- Clear documentation about data privacy
- No telemetry without explicit opt-in

## 8. Error Handling and Accessibility

### 8.1 Error Handling
- Detailed, actionable error messages
- Multiple logging levels (ERROR, WARN, INFO, DEBUG)
- Log storage options
- Graceful failure modes to preserve user work

### 8.2 Accessibility Features
- High-contrast terminal output
- Screen reader friendly text formats
- Clear error messages
- Keyboard shortcuts for common operations

## 9. Data Management

### 9.1 Data Migration
- Automatic migrations for data structure updates
- Strong backward compatibility after version 1.0
- Project format version detection
- Automatic backup before migrations
- Detailed migration logs

### 9.2 Backup and Recovery
- Git-based version control and backup
- Compatibility with external sync tools
- Auto-save during writing sessions
- Project export options

## 10. Development and Extensibility

### 10.1 Testing Framework
- 100% code coverage goal
- Pragmatic exclusions with `# pragma: no cover`
- Comprehensive test suite (unit, integration, functional)
- Continuous integration

### 10.2 Versioning Strategy
- Semantic versioning (MAJOR.MINOR.PATCH)
- Feature-driven release cadence
- Pre-1.0 versions (0.x) for beta status
- Version 1.0 marks stable API and data formats

### 10.3 Plugin System
- Framework for extending functionality
- Extension points (exporters, templates, statistics, AI, commands)
- Plugin discovery and management
- API documentation for developers

## 11. Documentation

### 11.1 Documentation Formats
- Inline help for commands
- Man pages
- Dedicated documentation website
- Markdown documentation files

### 11.2 Documentation Content
- Getting started guides
- Tutorials
- Reference documentation
- Examples and use cases
- Interactive tutorial for new users

### 11.3 Localization
- Initial release in English only
- Architecture to support additional languages in the future

## 13. Command Reference

### 13.1 Project Management Commands

#### `pmk init`
```
Usage: pmk init [OPTIONS]

  Initialize a new project.
  Creates the _binder.md file. Fails if one already exists.

Options:
  --help  Show this message and exit.
```

#### `pmk add`
```
Usage: pmk add [OPTIONS] PARENT_ID TITLE

  Add a new node to the project.

  PARENT_ID is the ID of the parent node. TITLE is the title of the new node.

Options:
  -c, --card TEXT     Brief summary of the node
  -t, --text TEXT     Main text of the node
  -n, --notes TEXT    Additional notes about the node
  -p, --position INTEGER  Position to insert the node
  --help                  Show this message and exit.
```

#### `pmk edit`
```
Usage: pmk edit [OPTIONS] NODE_ID

  Edit node content with the default text editor.

  NODE_ID is the ID of the node to edit.

Options:
  --editor / --no-editor  Open in editor
  --help                  Show this message and exit.
```

#### `pmk move`
```
Usage: pmk move [OPTIONS] NODE_ID NEW_PARENT_ID

  Move a node to a new parent.

  NODE_ID is the ID of the node to move. NEW_PARENT_ID is the ID of the new
  parent node.

Options:
  -p, --position INTEGER  Position to insert the node
  --help                  Show this message and exit.
```

#### `pmk remove`
```
Usage: pmk remove [OPTIONS] NODE_ID

  Remove a node from the project.

  NODE_ID is the ID of the node to remove.

Options:
  --delete-file          Delete the file as well as removing from binder
  --help                 Show this message and exit.
```

#### `pmk show`
```
Usage: pmk show [OPTIONS] NODE_ID

  Display node content.

  NODE_ID is the ID of the node to display.

Options:
  --help  Show this message and exit.
```

#### `pmk structure`
```
Usage: pmk structure [OPTIONS]

  Display the project structure.

Options:
  -n, --node-id TEXT  ID of the node to start from (defaults to root)
  --help              Show this message and exit.
```

### 13.2 Writing and Output Commands

#### `pmk compile`
```
Usage: pmk compile [OPTIONS] [NODE_ID]

  Compile the project or a specific node into another format.

  If NODE_ID is provided, compiles from that node. Otherwise compiles the entire project.

Options:
  -f, --format [html|epub|pdf|docx|rtf]  Output format (default: html)
  -o, --output PATH                      Output file path
  --include-comments / --no-comments     Include or exclude comments (default: exclude)
  --include-notes / --no-notes           Include or exclude research notes (default: exclude)
  --include-cards / --no-cards           Include or exclude cards (default: exclude)
  --toc / --no-toc                       Include table of contents (default: include)
  --template PATH                        Use custom template file
  --css PATH                             Use custom CSS file (for HTML/EPUB)
  --metadata PATH                        YAML file with additional metadata
  --help                                 Show this message and exit.
```

#### `pmk stats`
```
Usage: pmk stats [OPTIONS] [NODE_ID]

  Display statistics about the project or a specific node.

  If NODE_ID is provided, shows stats for that node and its children.
  Otherwise shows stats for the entire project.

Options:
  --today              Show only today's statistics
  --week               Show this week's statistics
  --month              Show this month's statistics
  --history            Show historical trends
  --session            Show current/last session statistics
  --goals              Show progress toward goals
  --detailed / --brief Display detailed or summarized statistics (default: brief)
  --format [text|json] Output format (default: text)
  --help               Show this message and exit.

Statistics displayed include:
  - Word count (total and by document)
  - Reading time estimate
  - Writing time logged
  - Session count
  - Daily/weekly averages
  - Progress toward configured goals
```

#### `pmk session`
```
Usage: pmk session [OPTIONS] [NODE_ID]

  Start a focused writing session on a specific node.

  If NODE_ID is provided, starts editing that node. Otherwise prompts for
  node selection. Provides real-time statistics and focused line-by-line editing.

  Once a line is committed (by pressing Enter), it cannot be edited within
  the session, encouraging forward progress rather than revision.

Options:
  -w, --words INTEGER      Word count goal for this session
  -t, --time INTEGER       Session time limit in minutes
  --timer [none|visible|alert]  Timer display mode (default: visible)
  --stats [none|minimal|detailed]  Stats display mode (default: minimal)
  --no-prompt              Skip goal/time prompts when not specified
  --help                   Show this message and exit.
```

### 13.3 Support and Enhancement Commands

#### `pmk snapshot`
```
Usage: pmk snapshot [OPTIONS]

  Create a snapshot of the current project state using Git.

  Commits all changes in the working directory with an automatically
  generated commit message that includes basic context.

Options:
  -m, --message TEXT      Custom commit message (appended to automatic context)
  --push / --no-push      Push changes to remote repository (default: no-push)
  --context [minimal|standard|detailed]
                          Amount of contextual info in commit message:
                            minimal: timestamp only
                            standard: timestamp, session stats (default)
                            detailed: adds location, weather (if configured)
  --help                  Show this message and exit.
```

#### `pmk ai`
```
Usage: pmk ai [OPTIONS] COMMAND [ARGS]...

  AI assistance tools for writing and project management.

Commands:
  brainstorm      Generate ideas related to a topic or node
  outline         Create or expand an outline for a node
  expand          Expand a brief description into fuller content

  # Editing commands
  developmental   Suggest structural improvements and content development
  line-edit       Suggest improvements to flow, clarity, and style
  copyedit        Check for grammar, punctuation, and consistency issues
  proofread       Check for typos and formatting issues

  # Other creative assistance
  rewrite         Suggest alternative phrasings or improvements
  summarize       Create a summary of a node's content
  research        Generate factual information on a topic
  characterize    Develop character details and traits
  dialogue        Generate sample dialogue between characters

  config          Configure AI settings and API keys

Options:
  --model TEXT    Specify which LLM to use
  --help          Show this message and exit.
```

### 13.4 Note Card and Research Commands

#### `pmk card`
```
Usage: pmk card [OPTIONS] COMMAND [ARGS]...

  Manage note cards associated with project nodes.

Commands:
  create      Create a note card for a node (if none exists)
  edit        Edit a node's note card in the default text editor
  show        Display a node's note card content
  list        List all nodes with note cards
  remove      Remove a node's note card
  session     Start a focused note card writing session

Options:
  --help      Show this message and exit.
```

#### `pmk notes`
```
Usage: pmk notes [OPTIONS] COMMAND [ARGS]...

  Manage research notes associated with project nodes.

Commands:
  create      Create research notes for a node (if none exist)
  edit        Edit a node's research notes in the default text editor
  show        Display a node's research notes content
  list        List all nodes with research notes
  remove      Remove a node's research notes
  session     Start a focused research notes writing session

Options:
  --help      Show this message and exit.
```

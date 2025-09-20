# Quickstart Guide

**Feature**: Prosemark CLI Writing Project Manager MVP
**Date**: 2025-09-20

## Installation

```bash
# Install from PyPI (when available)
pip install prosemark

# Or install from source
git clone https://github.com/username/prosemark
cd prosemark
uv sync
uv run pmk --help
```

## Basic Usage

### 1. Initialize a New Project

```bash
# Create a new writing project
mkdir my-novel
cd my-novel
pmk init --title "My Great Novel"
```

**Expected Output**:
```
Project "My Great Novel" initialized successfully
Created _binder.md with project structure
```

**Files Created**:
- `_binder.md` - Project structure file with managed content sections

### 2. Add Content Nodes

```bash
# Add top-level chapters
pmk add "Part 1: The Beginning"
pmk add "Part 2: The Journey"

# Add nested sections (use the node ID from previous output)
pmk add "Chapter 1: Origins" --parent 01234567
pmk add "Chapter 2: Discovery" --parent 01234567
```

**Expected Output**:
```
Added "Part 1: The Beginning" (01234567)
Created files: 01234567.md, 01234567.notes.md
Updated binder structure
```

### 3. View Project Structure

```bash
# Display the project hierarchy
pmk structure
```

**Expected Output**:
```
Project Structure:
├─ Part 1: The Beginning (01234567)
│  ├─ Chapter 1: Origins (89abcdef)
│  └─ Chapter 2: Discovery (deadbeef)
└─ Part 2: The Journey (cafebabe)
```

### 4. Edit Content

```bash
# Edit the main content of a chapter
pmk edit 89abcdef --part draft

# Edit notes for a chapter
pmk edit 89abcdef --part notes

# Edit the synopsis (in frontmatter)
pmk edit 89abcdef --part synopsis
```

**Expected Behavior**:
- Launches your preferred editor (set via EDITOR environment variable)
- Opens the appropriate file for editing

### 5. Create Freeform Writing

```bash
# Quick writing for ideas that don't fit the structure
pmk write "Character backstory ideas"
```

**Expected Output**:
```
Created freeform file: 20250920T1530_01234567-89ab-cdef-0123-456789abcdef.md
Opened in editor
```

### 6. Reorganize Structure

```bash
# Move a chapter to a different position
pmk move deadbeef --parent cafebabe --position 0

# View updated structure
pmk structure
```

### 7. Work with Placeholders

```bash
# Add a placeholder for future content
pmk add "Chapter 3: The Revelation" --parent 01234567

# Later, materialize it into actual content
pmk materialize "Chapter 3: The Revelation"
```

### 8. Check Project Integrity

```bash
# Audit the project for consistency issues
pmk audit
```

**Expected Output**:
```
Project integrity check completed
✓ All nodes have valid files
✓ All references are consistent
✓ No orphaned files found
```

## File Structure

After following the quickstart, your project will look like this:

```
my-novel/
├── _binder.md                    # Project structure
├── 01234567.md                   # Part 1 draft content
├── 01234567.notes.md             # Part 1 notes
├── 89abcdef.md                   # Chapter 1 draft
├── 89abcdef.notes.md             # Chapter 1 notes
├── deadbeef.md                   # Chapter 2 draft
├── deadbeef.notes.md             # Chapter 2 notes
├── cafebabe.md                   # Part 2 draft
├── cafebabe.notes.md             # Part 2 notes
└── 20250920T1530_*.md            # Freeform writing files
```

## Understanding the Binder File

The `_binder.md` file contains your project structure with managed content:

```markdown
# My Great Novel

This is my project overview and notes.

<!-- pmk:begin-binder -->
- [Part 1: The Beginning](01234567.md)
  - [Chapter 1: Origins](89abcdef.md)
  - [Chapter 2: Discovery](deadbeef.md)
- [Part 2: The Journey](cafebabe.md)
<!-- pmk:end-binder -->

Additional notes and content can go here.
Prosemark will never modify content outside the managed markers.
```

## Node File Format

Each content node consists of two files:

**Draft file (01234567.md)**:
```markdown
---
id: 01234567
title: "Part 1: The Beginning"
synopsis: |
  The opening section where we establish
  the world and introduce key characters
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Part 1: The Beginning

Your story content goes here...
```

**Notes file (01234567.notes.md)**:
```markdown
---
id: 01234567
title: "Part 1: The Beginning"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Notes for Part 1

Research, character development, plot notes...
```

## Configuration

### Editor Selection
Prosemark uses your preferred editor via the EDITOR environment variable:

```bash
# Set your editor preference
export EDITOR="code --wait"    # VS Code
export EDITOR="vim"            # Vim
export EDITOR="nano"           # Nano
```

### Project Settings
No configuration files needed - prosemark uses sensible defaults and follows your project structure.

## Validation Tests

To verify your installation works correctly:

### Test 1: Basic Project Lifecycle
```bash
# Create test project
mkdir test-project && cd test-project
pmk init --title "Test Project"
pmk add "Test Chapter"
pmk structure
pmk audit
```

### Test 2: Content Editing
```bash
# Test editor integration
pmk edit $(pmk structure --format json | jq -r '.roots[0].node_id') --part draft
# Verify editor opens with node content
```

### Test 3: Integrity Preservation
```bash
# Manually edit _binder.md to add content outside managed blocks
echo "# My Custom Notes" >> _binder.md
pmk add "Another Chapter"
# Verify custom content is preserved
grep "My Custom Notes" _binder.md
```

## Troubleshooting

### Editor Not Found
```bash
# Check your EDITOR setting
echo $EDITOR

# Test editor manually
$EDITOR test.md
```

### Permission Issues
```bash
# Check file permissions
ls -la _binder.md

# Fix if needed
chmod 644 _binder.md
```

### Project Not Found
Make sure you're in a directory with a `_binder.md` file, or run `pmk init` first.

## Next Steps

1. **Explore Advanced Features**: Try moving nodes, removing content, and using placeholders
2. **Integrate with Your Workflow**: Set up your preferred editor and file organization
3. **Large Projects**: Test with complex hierarchies and multiple content types
4. **Backup Strategy**: Consider version control (git) for your writing projects

## Integration with Other Tools

### Git Version Control
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial project structure"

# Prosemark files work well with git
# Node files are small and diff-friendly
# Timestamps help track writing progress
```

### Obsidian Compatibility
Prosemark files are fully compatible with Obsidian:
- Node files appear as individual notes
- Frontmatter is preserved and visible
- Links between files work naturally
- Tags and other Obsidian features can be added

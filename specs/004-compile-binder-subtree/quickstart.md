# Quickstart Guide: Compile Binder Subtree

## Overview
The compile command allows you to extract and concatenate all content from a node and its descendants into a single plain text output.

## Prerequisites
- Prosemark installed and configured
- Existing binder with nodes containing content
- Node IDs (UUIDv7 format) for target nodes

## Basic Usage

### 1. Compile a Single Node (No Children)
```bash
# Compile a leaf node (returns only its content)
pmk compile 0192f0c1-2345-7123-8abc-def012345678
```

### 2. Compile a Node with Children
```bash
# Compile a parent node and all descendants
pmk compile 0192f0c1-2345-7123-8abc-def012345678 > chapter.txt
```

### 3. Handle Empty Nodes
```bash
# By default, empty nodes are skipped
pmk compile 0192f0c1-2345-7123-8abc-def012345678

# Include empty nodes (future enhancement)
# pmk compile --include-empty 0192f0c1-2345-7123-8abc-def012345678
```

## Test Scenarios

### Scenario 1: Simple Hierarchy
```
Setup:
- Parent node (id: parent-001) with content "Chapter 1"
- Child 1 (id: child-001) with content "Section 1.1"
- Child 2 (id: child-002) with content "Section 1.2"

Command:
pmk compile parent-001

Expected Output:
Chapter 1

Section 1.1

Section 1.2
```

### Scenario 2: Deep Nesting
```
Setup:
- Root (id: root-001) with content "Book Title"
  - Chapter 1 (id: ch-001) with content "Chapter One"
    - Section 1.1 (id: sec-001) with content "Introduction"
    - Section 1.2 (id: sec-002) with content "Main Content"
  - Chapter 2 (id: ch-002) with content "Chapter Two"

Command:
pmk compile root-001

Expected Output:
Book Title

Chapter One

Introduction

Main Content

Chapter Two
```

### Scenario 3: Empty Nodes Skipped
```
Setup:
- Parent (id: parent-001) with content "Header"
- Child 1 (id: child-001) with empty content
- Child 2 (id: child-002) with content "Footer"

Command:
pmk compile parent-001

Expected Output:
Header

Footer
```

### Scenario 4: Node Not Found
```
Command:
pmk compile non-existent-node-id

Expected Output:
Error: Node not found: non-existent-node-id
```

## Verification Steps

1. **Create Test Nodes**:
   ```bash
   pmk add --title "Test Parent"
   pmk add --parent <parent-id> --title "Test Child 1"
   pmk add --parent <parent-id> --title "Test Child 2"
   ```

2. **Add Content**:
   ```bash
   pmk write <node-id>
   # Add content in the editor
   ```

3. **Compile and Verify**:
   ```bash
   pmk compile <parent-id> > output.txt
   cat output.txt
   ```

4. **Check Statistics** (if verbose mode available):
   ```bash
   pmk compile --verbose <node-id>
   # Should show: nodes compiled, nodes skipped, total traversed
   ```

## Common Use Cases

### Export Chapter for Review
```bash
pmk compile <chapter-node-id> > chapter_draft.txt
```

### Create Full Document
```bash
pmk compile <root-node-id> > full_document.txt
```

### Extract Section for Editing
```bash
pmk compile <section-node-id> | pbcopy  # Copy to clipboard (macOS)
pmk compile <section-node-id> | xclip   # Copy to clipboard (Linux)
```

## Troubleshooting

### Issue: No output produced
- Check if node has content: `pmk show <node-id>`
- Check if node has children: `pmk tree <node-id>`
- Verify node exists: `pmk list`

### Issue: Missing content
- Empty nodes are skipped by default
- Check traversal order matches expectations
- Verify all child nodes are properly linked

### Issue: Performance with large trees
- Consider compiling subtrees separately
- Monitor with --verbose flag for node counts
- Target performance: 1000 nodes in <1 second

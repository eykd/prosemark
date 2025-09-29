# Quickstart: Node Templates

## Prerequisites
- Prosemark CLI installed and configured
- Basic knowledge of Markdown and YAML frontmatter
- Access to command line interface

## Quick Start Examples

### 1. List Available Templates
```bash
# Display all available templates
pmk add --list-templates
```

**Expected Output**:
```
Available templates:
- meeting-notes
- project-setup/
- daily-journal
- research-notes
```

### 2. Create Node from Simple Template
```bash
# Create node from single template file
pmk add --template meeting-notes
```

**Interactive Flow**:
1. System prompts: "Enter meeting title:"
2. User enters: "Sprint Planning Meeting"
3. System prompts: "Enter date (YYYY-MM-DD):"
4. User enters: "2025-09-29"
5. System creates node with populated content

**Expected Result**: New node created with meeting template structure and user-provided values.

### 3. Create Node Tree from Directory Template
```bash
# Create multiple related nodes from directory template
pmk add --template project-setup
```

**Interactive Flow**:
1. System prompts: "Enter project name:"
2. User enters: "My New Project"
3. System prompts: "Enter project description:"
4. User enters: "A sample project for testing"
5. System creates multiple nodes preserving directory structure

**Expected Result**: Multiple related nodes created (e.g., project overview, tasks, notes) with consistent project information.

## Template Creation Guide

### 1. Simple Template File
Create `./templates/meeting-notes.md`:

```markdown
---
type: meeting
created: {{current_date}}
tags: [meetings, {{project_tag}}]
---

# {{meeting_title}}

**Date**: {{meeting_date}}
**Attendees**: {{attendees}}

## Agenda
- {{agenda_item_1}}
- {{agenda_item_2}}

## Notes

## Action Items
- [ ] {{action_item}}

## Next Steps
```

### 2. Directory Template Structure
Create `./templates/project-setup/` with multiple files:

```
./templates/project-setup/
├── overview.md      # Project overview template
├── tasks.md         # Task tracking template
└── notes.md         # General notes template
```

Each file uses shared placeholders like `{{project_name}}` for consistency.

## Validation Examples

### 1. Invalid Template Error
```bash
pmk add --template broken-template
```

**Error Output**:
```
Error: Template validation failed
File: ./templates/broken-template.md
Issue: Invalid YAML frontmatter at line 2
Suggestion: Check YAML syntax and ensure proper indentation
```

### 2. Missing Template Error
```bash
pmk add --template nonexistent
```

**Error Output**:
```
Error: Template not found
Template: nonexistent
Search path: ./templates/
Suggestion: Use 'pmk add --list-templates' to see available templates
```

## Advanced Usage

### 1. Template with Optional Placeholders
Template content with default values:
```markdown
---
priority: {{priority:medium}}
status: {{status:draft}}
---

# {{title}}

Priority: {{priority}}
Status: {{status}}
```

**Interactive Flow**:
- User can press Enter to accept defaults
- Or provide custom values

### 2. Nested Directory Templates
```
./templates/research-project/
├── main/
│   ├── hypothesis.md
│   └── methodology.md
├── data/
│   └── collection.md
└── analysis/
    └── results.md
```

Creates complete research project structure with related nodes.

## Testing Scenarios

### Test 1: Basic Template Instantiation
1. Create simple template with 2 placeholders
2. Run `pmk add --template simple`
3. Provide values for both placeholders
4. Verify node created with correct content
5. Verify placeholders replaced with user values

### Test 2: Directory Template Creation
1. Create directory with 3 template files
2. Use shared placeholders across files
3. Run `pmk add --template directory`
4. Provide values once for shared placeholders
5. Verify all 3 nodes created with consistent values

### Test 3: Template Validation
1. Create template with invalid YAML
2. Run `pmk add --template invalid`
3. Verify clear error message displayed
4. Verify operation halts without creating nodes

### Test 4: Template Listing
1. Create multiple templates and directories
2. Run `pmk add --list-templates`
3. Verify all templates displayed correctly
4. Verify directories marked with '/' suffix

### Test 5: Missing Template Handling
1. Run `pmk add --template missing`
2. Verify appropriate error message
3. Verify suggestion to list available templates

## Performance Expectations

### Response Times
- Template listing: < 100ms for up to 50 templates
- Template validation: < 500ms for templates up to 10KB
- Node creation: < 1 second for single templates
- Directory processing: < 2 seconds for up to 10 related templates

### Resource Usage
- Memory: < 50MB for template processing
- Disk I/O: Minimal beyond necessary file operations
- CPU: Lightweight text processing operations

## Troubleshooting

### Common Issues

1. **Templates not found**
   - Verify `./templates/` directory exists
   - Check template file has `.md` extension
   - Ensure file permissions allow reading

2. **Placeholder errors**
   - Verify placeholder syntax: `{{variable_name}}`
   - Check for matching opening/closing braces
   - Ensure variable names are valid identifiers

3. **Validation failures**
   - Check YAML frontmatter syntax
   - Verify Markdown format compliance
   - Ensure prosemark format requirements met

### Debug Steps
1. Use `--list-templates` to verify template discovery
2. Check template file manually for syntax issues
3. Verify file permissions and accessibility
4. Test with simple template first before complex ones

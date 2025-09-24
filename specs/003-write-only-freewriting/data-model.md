# Data Model: Write-Only Freewriting Interface

## Entities

### FreewriteSession
Represents a single freewriting session with metadata and configuration.

**Fields**:
- `session_id`: str (UUID) - Unique identifier for the session
- `target_node`: Optional[str] (UUID) - Target node for content, if specified
- `title`: Optional[str] - Optional session title from --title flag
- `start_time`: datetime - When the session began
- `word_count_goal`: Optional[int] - Target word count, if set
- `time_limit`: Optional[int] - Session time limit in seconds, if set
- `current_word_count`: int - Running count of words written
- `elapsed_time`: int - Seconds elapsed in current session
- `output_file_path`: str - Path to the output file being written
- `content_lines`: List[str] - Lines of content written during session

**Validation Rules**:
- `target_node` must be valid UUID format if provided
- `start_time` must not be in the future
- `word_count_goal` and `time_limit` must be positive integers if set
- `current_word_count` and `elapsed_time` must be non-negative
- `output_file_path` must be valid file path
- `content_lines` preserves exact user input including empty lines

**State Transitions**:
- INITIALIZING → ACTIVE (when TUI starts)
- ACTIVE → PAUSED (on focus loss or manual pause)
- PAUSED → ACTIVE (on focus return or resume)
- ACTIVE → COMPLETED (on user exit or time limit reached)
- COMPLETED → ARCHIVED (after session cleanup)

### FrewriteContent
Represents a single line of content entered by the user.

**Fields**:
- `content`: str - The actual text content entered by user
- `timestamp`: datetime - When this content was entered
- `line_number`: int - Sequential line number in the session
- `word_count`: int - Number of words in this specific content line

**Validation Rules**:
- `content` preserves exact user input (including leading/trailing spaces)
- `timestamp` must be after session start_time
- `line_number` must be positive and sequential
- `word_count` calculated using standard whitespace splitting

### FileTarget
Represents the destination file for freewriting content.

**Fields**:
- `file_path`: str - Absolute path to the target file
- `is_node`: bool - Whether this targets a node (True) or daily file (False)
- `node_uuid`: Optional[str] - UUID if targeting a node
- `created_timestamp`: datetime - When the target file was created
- `file_format`: str - File format (always "markdown")

**Validation Rules**:
- `file_path` must be writable location
- `node_uuid` required if `is_node` is True, must be valid UUID
- `created_timestamp` must be valid datetime
- `file_format` must be "markdown"

**Relationships**:
- `FreewriteSession` → `FileTarget` (one-to-one)
- `FreewriteSession` → `FrewriteContent` (one-to-many)
- `FileTarget` stores the physical location
- `FrewriteContent` stores the actual written content

## File Format Structure

### Daily Freewrite File (YYYY-MM-DD-HHmm.md)
```markdown
---
type: freewrite
session_id: "01234567-89ab-cdef-0123-456789abcdef"
created: "2025-09-24T14:30:00Z"
title: "Optional session title"
word_count_goal: 500
time_limit: 1800
---

# Freewrite Session

[Content lines appended as user types and hits ENTER]
Line 1 content here
Line 2 content here
...
```

### Node File (UUID.md)
```markdown
---
id: "01234567-89ab-cdef-0123-456789abcdef"
type: node
created: "2025-09-24T14:30:00Z"
modified: "2025-09-24T14:35:23Z"
tags: ["freewrite"]
---

# Node Title

## Freewrite Session - 2025-09-24 14:30

[Appended content with session metadata]
```

## Persistence Strategy

### File Operations
- **Atomic writes**: Each ENTER creates atomic append operation
- **Immediate persistence**: No in-memory buffering, direct file writes
- **Failure recovery**: Display error but continue session, retry on next input
- **File locking**: Handle concurrent access gracefully

### Session State
- **No session persistence**: Sessions exist only during TUI execution
- **Metadata in file**: Store session info in YAML frontmatter
- **Progress tracking**: Word count and timing calculated from file content

### Node Integration
- **Binder updates**: Automatically add new nodes to binder index
- **UUID validation**: Strict UUID format checking before file operations
- **Conflict resolution**: Append to existing nodes, create if missing

## Configuration Model

### SessionConfig
Runtime configuration passed from CLI to TUI.

**Fields**:
- `target_node`: Optional[str] - UUID of target node
- `title`: Optional[str] - Session title
- `word_count_goal`: Optional[int] - Word count target
- `time_limit`: Optional[int] - Time limit in seconds
- `theme`: str - UI theme name (default: "dark")
- `current_directory`: str - Working directory for daily files

**Validation Rules**:
- `target_node` must be valid UUID if provided
- `word_count_goal` and `time_limit` must be positive if provided
- `theme` must match available themes
- `current_directory` must be writable directory

This data model supports all functional requirements while maintaining constitutional compliance with plain text storage, hexagonal architecture separation, and comprehensive validation rules.

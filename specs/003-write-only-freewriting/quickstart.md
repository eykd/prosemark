# Quickstart: Write-Only Freewriting Interface

This guide demonstrates the freewriting feature through practical test scenarios based on the user stories from the specification.

## Prerequisites

- Python 3.13+
- Textual library installed
- Typer library installed
- prosemark project properly configured

## Test Scenarios

### Scenario 1: Daily Freewrite File Creation

**Test**: Basic freewriting without specifying a node
```bash
# Start freewriting interface
pmk write

# Expected behavior:
# - TUI opens with 80% content area, 20% input area
# - Empty content area initially
# - Cursor in input box at bottom
# - Status shows word count: 0, timer running
```

**Expected file creation**:
- File: `2025-09-24-1430.md` (timestamp when started)
- Location: Current working directory
- Format: Markdown with YAML frontmatter

**User actions in TUI**:
1. Type "This is my first thought" in input box
2. Press ENTER
3. Content appears in top area, input box clears
4. Word count updates to 5
5. Type another line, press ENTER
6. Both lines visible in content area
7. Press Ctrl+C or quit command to exit

**Validation**:
- File exists with correct timestamp name
- Content matches what was typed
- YAML frontmatter includes session metadata
- Each ENTER press created new line in file

### Scenario 2: Writing to Specific Node

**Test**: Freewriting to a specified UUID node
```bash
# Start freewriting to specific node
pmk write 01234567-89ab-cdef-0123-456789abcdef
```

**Expected behavior**:
- TUI opens same as Scenario 1
- Content gets appended to node file instead of daily file
- If node doesn't exist, it gets created automatically
- Node gets added to binder index

**Expected file operations**:
- File: `01234567-89ab-cdef-0123-456789abcdef.md`
- Location: Node directory (as per prosemark conventions)
- Content appended with session header

**Validation**:
- Node file exists at correct path
- Content appended with session metadata
- Binder updated with new node if it didn't exist
- Node YAML frontmatter properly formatted

### Scenario 3: Session with Title

**Test**: Freewriting with custom title
```bash
pmk write --title "Morning thoughts"
```

**Expected behavior**:
- TUI shows title in header or status area
- Daily file includes title in frontmatter
- Session metadata references the title

**Validation**:
- Title appears in file frontmatter
- TUI displays title appropriately

### Scenario 4: Session with Goals

**Test**: Freewriting with word count goal and time limit
```bash
pmk write --word-count-goal 500 --time-limit 900
```

**Expected behavior**:
- TUI shows progress toward 500 words
- Timer counts down from 15 minutes (900 seconds)
- Progress indicators update in real-time
- Session continues if goals are reached (no auto-exit)

**Validation**:
- Progress displayed correctly
- Timer functionality works
- Session doesn't terminate at goal achievement

### Scenario 5: Error Handling

**Test**: Various error conditions
```bash
# Invalid UUID
pmk write invalid-uuid-format

# Unwritable directory (simulate)
chmod 444 .
pmk write

# Disk full (simulate)
# Fill disk or set quota
```

**Expected behavior**:
- Invalid UUID: Error message, command exits with non-zero code
- Unwritable directory: Error in TUI, continues session, retries on next input
- Disk full: Error in TUI, continues session, allows user to resolve

**Validation**:
- Appropriate error messages displayed
- CLI errors prevent TUI launch
- TUI errors allow session continuation
- Recovery possible after error resolution

### Scenario 6: Multiple Sessions Same Day

**Test**: Multiple freewriting sessions on same day
```bash
# First session at 14:30
pmk write
# ... write some content, exit

# Second session at 16:45
pmk write
# ... write more content, exit
```

**Expected behavior**:
- First session creates `2025-09-24-1430.md`
- Second session creates `2025-09-24-1645.md`
- Each session is completely separate
- No content mixing between sessions

**Validation**:
- Two separate files created
- Different timestamps in filenames
- Independent content in each file
- Separate session metadata

## Integration Test Checklist

### TUI Functionality
- [ ] 80/20 layout displays correctly
- [ ] Input box has readline-style editing
- [ ] ENTER appends content and clears input
- [ ] Content area shows bottom of file
- [ ] Word count updates in real-time
- [ ] Timer displays and counts correctly
- [ ] Error messages appear in UI without crashing

### File Operations
- [ ] Daily files created with correct naming
- [ ] Node files created/appended correctly
- [ ] YAML frontmatter properly formatted
- [ ] Content preserves exact user input
- [ ] Atomic write operations (no corruption)

### CLI Integration
- [ ] Typer commands parse arguments correctly
- [ ] Invalid arguments show helpful errors
- [ ] TUI launches with correct configuration
- [ ] Exit codes appropriate for different scenarios

### Domain Logic
- [ ] UUID validation works correctly
- [ ] Word counting accurate
- [ ] Time tracking precise
- [ ] Session state maintained during TUI operation

### Error Recovery
- [ ] File system errors handled gracefully
- [ ] Network issues (if applicable) handled
- [ ] Invalid input sanitized appropriately
- [ ] Recovery possible after transient failures

## Performance Validation

### Response Times
- [ ] TUI startup < 1 second
- [ ] Input to display < 100ms
- [ ] File write operations < 50ms
- [ ] Real-time updates smooth and responsive

### Resource Usage
- [ ] Memory usage reasonable for long sessions
- [ ] No memory leaks during extended use
- [ ] CPU usage minimal when idle
- [ ] File handles properly closed

## Manual Testing Protocol

1. **Setup**: Clean test environment, ensure dependencies
2. **Basic Flow**: Run through Scenarios 1-6 systematically
3. **Edge Cases**: Test error conditions and boundary cases
4. **Long Session**: Extended session testing (30+ minutes)
5. **Concurrent**: Multiple sessions, file conflicts
6. **Recovery**: Interrupt and resume testing
7. **Integration**: Compatibility with existing prosemark features

## Success Criteria

All test scenarios pass without errors, TUI is responsive and stable, files are created correctly, and the feature integrates cleanly with existing prosemark architecture while following constitutional requirements for testing, code quality, and hexagonal design patterns.

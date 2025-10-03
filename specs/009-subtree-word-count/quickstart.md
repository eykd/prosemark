# Quickstart: Subtree Word Count

## Overview

This quickstart validates the word count feature end-to-end through user acceptance scenarios. It should be executable as a manual test or automated integration test.

## Prerequisites

- Prosemark installed and available as `pmk` command
- Test project directory with write permissions
- Basic familiarity with CLI and Markdown

## Setup Test Project

```bash
# Create test directory
mkdir -p /tmp/pmk-wc-test
cd /tmp/pmk-wc-test

# Initialize prosemark project
pmk init

# Create test nodes with various content
```

## Test Scenario 1: Basic Word Count (Single Node)

**Objective**: Verify word count for a single node with simple content.

```bash
# Create a simple node
pmk add "Test Node"
# Get the node ID from output (e.g., 01JX...)
NODE_ID="<paste-node-id-here>"

# Edit node to add content: "Hello world"
# (Edit via your preferred method - pmk edit, or directly in .pmk/nodes/)

# Count words
pmk wc "$NODE_ID"
# Expected output: 2
```

**Validation**:
- Output is exactly `2` (plain number, no labels)
- Exit code is 0
- No errors to stderr

---

## Test Scenario 2: Subtree Word Count (Parent + Children)

**Objective**: Verify word count across a node subtree (parent + all descendants).

```bash
# Create parent node
pmk add "Chapter One"
PARENT_ID="<paste-parent-id-here>"

# Create child nodes
pmk add "Scene A" --parent "$PARENT_ID"
CHILD_A="<paste-child-a-id-here>"

pmk add "Scene B" --parent "$PARENT_ID"
CHILD_B="<paste-child-b-id-here>"

# Add content to each:
# - Chapter One: "Chapter introduction."  (2 words)
# - Scene A: "First scene content."  (3 words)
# - Scene B: "Second scene content."  (3 words)
# Total expected: 8 words

# Count words in subtree
pmk wc "$PARENT_ID"
# Expected output: 8
```

**Validation**:
- Output is `8`
- Counts parent + all children
- Exit code is 0

---

## Test Scenario 3: All Root Nodes (No Argument)

**Objective**: Verify word count across all root nodes when no node ID specified.

```bash
# Create multiple root nodes
pmk add "Root One"
ROOT_1="<paste-root-1-id-here>"

pmk add "Root Two"
ROOT_2="<paste-root-2-id-here>"

# Add content:
# - Root One: "First root content."  (3 words)
# - Root Two: "Second root content."  (3 words)
# Total expected: 6 words

# Count all roots
pmk wc
# Expected output: 6
```

**Validation**:
- Output is `6`
- Counts all root nodes
- Exit code is 0

---

## Test Scenario 4: Contractions and Hyphens

**Objective**: Verify US English word-splitting rules for contractions and hyphens.

```bash
# Create test node
pmk add "Grammar Test"
GRAMMAR_ID="<paste-id-here>"

# Add content: "I don't think it's a well-known fact."
# Expected: 7 words (don't=1, it's=1, well-known=1)

# Count words
pmk wc "$GRAMMAR_ID"
# Expected output: 7
```

**Validation**:
- Contractions count as one word
- Hyphenated compounds count as one word
- Exit code is 0

---

## Test Scenario 5: Numbers, URLs, and Emails

**Objective**: Verify special token handling (numbers, URLs, emails).

```bash
# Create test node
pmk add "Special Tokens"
SPECIAL_ID="<paste-id-here>"

# Add content: "There are 123 items at https://example.com or email user@example.com"
# Expected: 9 words (123=1, https://example.com=1, user@example.com=1)

# Count words
pmk wc "$SPECIAL_ID"
# Expected output: 9
```

**Validation**:
- Numbers count as words
- URLs count as single words (not split on punctuation)
- Emails count as single words
- Exit code is 0

---

## Test Scenario 6: Empty Node

**Objective**: Verify behavior for nodes with no content.

```bash
# Create empty node
pmk add "Empty Node"
EMPTY_ID="<paste-id-here>"

# Don't add any content (leave empty)

# Count words
pmk wc "$EMPTY_ID"
# Expected output: 0
```

**Validation**:
- Output is `0`
- Exit code is 0 (success, not error)
- No stderr output

---

## Test Scenario 7: Invalid Node ID

**Objective**: Verify error handling for non-existent node ID.

```bash
# Use non-existent but valid-format UUID
pmk wc "01JXXXXXXXXXXXXXXXXXXXXX" 2>/tmp/pmk-wc-stderr.txt
EXIT_CODE=$?

# Check output
cat /tmp/pmk-wc-stderr.txt
# Expected stderr: "Error: Node not found: 01JXXXXXXXXXXXXXXXXXXXXX"

# Expected stdout: "0"

echo "Exit code: $EXIT_CODE"
# Expected exit code: 1
```

**Validation**:
- Stdout outputs `0`
- Stderr contains error message
- Exit code is 1 (failure)

---

## Test Scenario 8: Invalid Node ID Format

**Objective**: Verify error handling for invalid UUID format.

```bash
# Use invalid UUID format
pmk wc "not-a-uuid" 2>/tmp/pmk-wc-stderr.txt
EXIT_CODE=$?

# Check stderr
cat /tmp/pmk-wc-stderr.txt
# Expected: "Error: Invalid node ID format: not-a-uuid"

# Expected stdout: "0"

echo "Exit code: $EXIT_CODE"
# Expected exit code: 1
```

**Validation**:
- Stdout outputs `0`
- Stderr contains error message about invalid format
- Exit code is 1

---

## Test Scenario 9: Scriptable Integration

**Objective**: Verify command works in shell pipelines and scripts.

```bash
# Create test node
pmk add "Script Test"
SCRIPT_ID="<paste-id-here>"

# Add content: "This is a test sentence with exactly ten words here."
# Expected: 10 words

# Use in script
COUNT=$(pmk wc "$SCRIPT_ID")
echo "Word count: $COUNT"

# Test arithmetic
if [ "$COUNT" -eq 10 ]; then
    echo "✓ Count matches expected value"
else
    echo "✗ Count mismatch: expected 10, got $COUNT"
fi

# Use with wc for comparison (should match)
pmk compile "$SCRIPT_ID" | wc -w
# Should output close to same count (slight variation acceptable for edge cases)
```

**Validation**:
- Plain number output is scriptable
- Can be used in arithmetic comparisons
- Works in pipelines

---

## Test Scenario 10: Whitespace Normalization

**Objective**: Verify multiple spaces and newlines are handled correctly.

```bash
# Create test node
pmk add "Whitespace Test"
SPACE_ID="<paste-id-here>"

# Add content with multiple spaces and newlines:
# "word  \n\n  word"
# (literally: word, 2 spaces, 2 newlines, 2 spaces, word)
# Expected: 2 words

# Count words
pmk wc "$SPACE_ID"
# Expected output: 2
```

**Validation**:
- Multiple spaces count as single separator
- Newlines count as separators
- Exit code is 0

---

## Performance Test (Optional)

**Objective**: Verify performance on large documents.

```bash
# Create large node
pmk add "Novel Chapter"
LARGE_ID="<paste-id-here>"

# Add content: Typical novel chapter (~3000 words)
# (Generate or paste large text)

# Time the word count
time pmk wc "$LARGE_ID"

# Should complete in < 1 second for typical novel-length content
```

**Validation**:
- Completes in < 1 second
- Accurate count
- No errors

---

## Cleanup

```bash
# Remove test directory
cd /tmp
rm -rf pmk-wc-test
```

---

## Acceptance Criteria Summary

All scenarios must pass:

✅ Basic single node count
✅ Subtree traversal (parent + children)
✅ All root nodes (no argument)
✅ Contractions and hyphens (US English rules)
✅ Numbers, URLs, emails (special tokens)
✅ Empty nodes (return 0, exit 0)
✅ Invalid node ID (error to stderr, 0 to stdout, exit 1)
✅ Invalid UUID format (error to stderr, 0 to stdout, exit 1)
✅ Scriptable integration (plain number output)
✅ Whitespace normalization (multiple spaces/newlines)

---

## Automated Test Conversion

These scenarios map directly to integration tests in:
`tests/integration/wordcount/test_wc_command.py`

Each scenario becomes a test function following TDD approach:
1. Write test (expect failure)
2. Implement feature
3. Verify test passes

---

## Troubleshooting

**Issue**: Count doesn't match expected
- Check actual content in node file
- Verify contractions/hyphens are preserved
- Compare with `pmk compile <id> | wc -w` output

**Issue**: Command not found
- Verify `pmk wc` is registered in CLI
- Check `pmk --help` for wc command
- Ensure implementation is complete

**Issue**: Errors to stdout instead of stderr
- Check CLI error handling
- Verify typer.echo(err=True) for errors

---

## Success Criteria

This quickstart is considered complete when:
- All 10 test scenarios pass manually
- Each scenario can be automated as an integration test
- Command behavior matches specification
- Error handling is consistent with compile command
- Performance meets stated goals (<1 second for 100K words)

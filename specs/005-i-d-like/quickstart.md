# Quickstart: Text Preservation in Binder Operations

## Overview
This feature enhances all binder operations to preserve extraneous text (narrative content outside Markdown lists and UUID7 links) while only modifying structural hierarchy elements.

## Quick Test Scenarios

### 1. Basic Text Preservation
**Test**: Narrative text around structural elements is preserved
```bash
# Create test binder with mixed content
cat > test_binder.md << EOF
**Act I - The Beginning**
Director Kolteo's journey starts with conflict and mystery.

- [Chapter 1: The Return](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

  This chapter introduces our protagonist in his everyday world,
  showing his mastery over the fleet while hinting at past trauma.

  - [Scene 1: The Director's Office](01998718-2674-7ec0-8b34-514c1c5f0c28.md)
  - [Scene 2: Meeting Preparation](01998718-267c-7c68-94a6-b26b25eaced0.md)

More narrative content continues here...
EOF

# Test any binder operation (compile, add, remove, restructure)
pmk compile test_binder.md

# Verify all narrative text remains unchanged
# Expected: Act I header, chapter description, "More narrative content" all preserved
```

### 2. Malformed Syntax Handling
**Test**: Malformed structural elements are treated as extraneous text
```bash
cat > malformed_binder.md << EOF
- [Broken link(missing-bracket.md)
Normal text that should be preserved
- [Valid Chapter](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
- Malformed list item without proper brackets
EOF

pmk compile malformed_binder.md

# Expected: Only valid chapter remains structural
# Malformed elements preserved as extraneous text
```

### 3. UUID7 Validation
**Test**: Only valid UUID7 links are treated as structural
```bash
cat > uuid_test_binder.md << EOF
- [Valid UUID7](01998718-2670-7879-81d4-8cd08c4bfe2f.md)
- [Invalid short ID](chapter-1.md)
- [Another invalid](12345-not-uuid.md)
- [Also invalid](some-file-name.md)
EOF

pmk compile uuid_test_binder.md

# Expected: Only first link treated as structural
# Other links preserved as extraneous text
```

### 4. Formatting Preservation
**Test**: All text formatting is preserved exactly
```bash
cat > formatting_test.md << EOF
# Main Title

**Bold introduction text**
*Italic description*

- [Chapter 1](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

> Blockquote that should be preserved

  - [Nested Scene](01998718-2674-7ec0-8b34-514c1c5f0c28.md)

## Another Section

Final paragraph with `code snippets` and [regular links](example.com).
EOF

pmk compile formatting_test.md

# Expected: All formatting preserved character-for-character
# Headers, bold, italic, blockquotes, code, regular links unchanged
```

### 5. Round-Trip Integrity Test
**Test**: Parse and render operations preserve all content
```bash
# Create complex test file
cat > roundtrip_test.md << EOF
**Complex Document**

Narrative introduction with multiple paragraphs.
This should all be preserved exactly.

- [First Chapter](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

  Chapter description here.

  - [Scene A](01998718-2674-7ec0-8b34-514c1c5f0c28.md)
  - [Scene B](01998718-267c-7c68-94a6-b26b25eaced0.md)

- [Second Chapter](01998718-2671-7879-81d4-8cd08c4bfe2f.md)

Concluding narrative text.
EOF

# Perform round-trip test
cp roundtrip_test.md original.md
pmk compile roundtrip_test.md  # Any binder operation
diff original.md roundtrip_test.md

# Expected: No differences - files should be identical
```

## Integration Test Scenarios

### End-to-End Workflow Test
```bash
# 1. Create project with mixed content binder
pmk init test_project
cd test_project

# 2. Create binder with narrative structure
cat > outline.md << EOF
**The Lost Fleet Chronicles**
An epic space opera exploring themes of loyalty, sacrifice, and redemption.

- [Book I: Return of the Exile](book1-uuid.md)

  Director Kolteo's story begins here.

  - [Part I: The Return](part1-uuid.md)
    **Everyday world, everyday conflict**
    The protagonist's normal life before the inciting incident.

    - [Chapter 1: The Director](01998718-2670-7879-81d4-8cd08c4bfe2f.md)

The story continues with more books and complexity...
EOF

# 3. Test all major operations preserve text
pmk add outline.md "New Chapter" parent-uuid
pmk remove outline.md target-uuid
pmk move outline.md source-uuid new-parent-uuid
pmk compile outline.md

# 4. Verify narrative preservation throughout
# Expected: All narrative text, formatting, structure preserved
```

### Performance Test
```bash
# Test with large binder (hundreds of nodes)
python -c "
content = '**Large Binder Test**\n\n'
for i in range(100):
    content += f'Narrative section {i}\n'
    content += f'- [Chapter {i}](0199871{i:04d}-2670-7879-81d4-8cd08c4bfe2f.md)\n'
    content += f'  Description for chapter {i}\n\n'
with open('large_binder.md', 'w') as f:
    f.write(content)
"

# Test performance with preservation
time pmk compile large_binder.md

# Expected: Reasonable performance, all text preserved
```

## Expected Outcomes

### Success Criteria
1. **Text Preservation**: All non-structural text preserved exactly
2. **Formatting Integrity**: Bold, italic, headers, code blocks unchanged
3. **Position Maintenance**: Text appears in original relative positions
4. **Structural Operations**: List items and UUID7 links modified correctly
5. **Error Resilience**: Malformed syntax becomes preserved text
6. **Round-Trip Accuracy**: Parse/render cycles maintain perfect fidelity

### Validation Commands
```bash
# Verify implementation meets all requirements
pytest tests/contract/test_enhanced_parser_contract.py -v
pytest tests/integration/test_text_preservation.py -v
pytest tests/unit/test_uuid7_validation.py -v

# Check quality standards
uv run ruff check src/
uv run mypy src/
pytest --cov=src --cov-report=term:skip-covered
```

This quickstart provides concrete test scenarios that validate the feature works as specified while maintaining the existing user experience for binder operations.

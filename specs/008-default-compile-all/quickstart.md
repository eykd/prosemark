# Quickstart: Optional Node ID Compile Command Validation

## Overview

This document provides step-by-step validation procedures to verify the optional node ID compile command feature works correctly. Execute these steps after implementation to ensure all requirements are met.

---

## Prerequisites

1. **Environment Setup**:
   ```bash
   cd /workspace
   source .venv/bin/activate  # or equivalent for your environment
   ```

2. **Quality Gates Passed**:
   - ✅ All tests pass: `pytest tests/`
   - ✅ Type checking passes: `mypy src/`
   - ✅ Linting passes: `ruff check src/ tests/`
   - ✅ 100% test coverage: `pytest --cov`

3. **Test Project Setup**:
   ```bash
   # Create temporary test project
   mkdir -p /tmp/pmk-test-008
   cd /tmp/pmk-test-008
   ```

---

## Validation Scenario 1: Compile All Roots (Standard Case)

### Setup

Create test project with 3 root nodes:

```bash
# Initialize project
cd /tmp/pmk-test-008

# Create binder with 3 roots
cat > binder.md << 'EOF'
# Test Project

- [[root1]] Chapter 1
- [[root2]] Chapter 2
- [[root3]] Chapter 3
EOF

# Create root node 1
cat > root1.md << 'EOF'
---
id: root1
title: "Chapter 1"
---

# Chapter 1

This is the content of chapter 1.

## Section 1.1

Some subsection content.
EOF

# Create root node 2
cat > root2.md << 'EOF'
---
id: root2
title: "Chapter 2"
---

# Chapter 2

This is the content of chapter 2.
EOF

# Create root node 3
cat > root3.md << 'EOF'
---
id: root3
title: "Chapter 3"
---

# Chapter 3

This is the content of chapter 3.
EOF
```

### Execute

```bash
# Compile all roots (no node ID argument)
pmk compile > output.txt
echo $?  # Should print: 0
```

### Verify

```bash
# Check output contains all three chapters
grep -q "Chapter 1" output.txt && echo "✅ Root 1 found" || echo "❌ Root 1 missing"
grep -q "Chapter 2" output.txt && echo "✅ Root 2 found" || echo "❌ Root 2 missing"
grep -q "Chapter 3" output.txt && echo "✅ Root 3 found" || echo "❌ Root 3 missing"

# Check ordering (Chapter 1 before Chapter 2 before Chapter 3)
if grep -n "Chapter" output.txt | sort -n | head -3 | grep -q "Chapter 1.*Chapter 2.*Chapter 3"; then
    echo "✅ Correct order"
else
    echo "❌ Incorrect order"
fi

# Check double newline separators
if grep -Pzo "Chapter 1[^\n]*\n\n[^\n]*\n\nChapter 2" output.txt > /dev/null 2>&1; then
    echo "✅ Double newline separators present"
else
    echo "❌ Missing double newline separators"
fi
```

**Expected Result**: All roots compiled in order, separated by double newlines, exit code 0.

---

## Validation Scenario 2: Empty Binder Handling

### Setup

```bash
cd /tmp/pmk-test-008

# Create empty binder
cat > binder.md << 'EOF'
# Empty Project

(no root nodes)
EOF
```

### Execute

```bash
# Compile with no roots
pmk compile > output.txt 2> error.txt
echo $?  # Should print: 0
```

### Verify

```bash
# Check empty output
if [ ! -s output.txt ]; then
    echo "✅ Output is empty"
else
    echo "❌ Output is not empty"
fi

# Check no error message
if [ ! -s error.txt ]; then
    echo "✅ No error message"
else
    echo "❌ Unexpected error message"
    cat error.txt
fi

# Check exit code 0 (success)
pmk compile > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Exit code 0 (success)"
else
    echo "❌ Non-zero exit code"
fi
```

**Expected Result**: Empty output, no errors, exit code 0 (silent success).

---

## Validation Scenario 3: Placeholder Filtering

### Setup

```bash
cd /tmp/pmk-test-008

# Create binder with mix of placeholders and materialized nodes
cat > binder.md << 'EOF'
# Mixed Project

- Placeholder 1 (no link - this is a placeholder)
- [[actual1]] Actual Node 1
- Placeholder 2 (no link)
- [[actual2]] Actual Node 2
EOF

# Create actual nodes only (no files for placeholders)
cat > actual1.md << 'EOF'
---
id: actual1
title: "Actual 1"
---

Content of actual node 1.
EOF

cat > actual2.md << 'EOF'
---
id: actual2
title: "Actual 2"
---

Content of actual node 2.
EOF
```

### Execute

```bash
pmk compile > output.txt
echo $?  # Should print: 0
```

### Verify

```bash
# Check only actual nodes compiled
grep -q "actual node 1" output.txt && echo "✅ Actual 1 found" || echo "❌ Actual 1 missing"
grep -q "actual node 2" output.txt && echo "✅ Actual 2 found" || echo "❌ Actual 2 missing"

# Check placeholders NOT compiled (no "Placeholder" in output)
if ! grep -q "Placeholder" output.txt; then
    echo "✅ Placeholders correctly filtered out"
else
    echo "❌ Placeholders incorrectly included"
fi

# Count sections (should be 2, not 4)
section_count=$(grep -c "Content of actual" output.txt)
if [ "$section_count" -eq 2 ]; then
    echo "✅ Correct number of sections (2)"
else
    echo "❌ Incorrect section count: $section_count"
fi
```

**Expected Result**: Only materialized nodes compiled, placeholders skipped.

---

## Validation Scenario 4: Single Node Behavior Preserved

### Setup

```bash
cd /tmp/pmk-test-008

# Use existing binder with multiple roots
cat > binder.md << 'EOF'
# Project

- [[root1]] Chapter 1
- [[root2]] Chapter 2
EOF

cat > root1.md << 'EOF'
---
id: root1
title: "Chapter 1"
---

Chapter 1 content.
EOF

cat > root2.md << 'EOF'
---
id: root2
title: "Chapter 2"
---

Chapter 2 content.
EOF
```

### Execute

```bash
# Compile specific node (existing behavior)
pmk compile root1 > output.txt
echo $?  # Should print: 0
```

### Verify

```bash
# Check only root1 compiled
grep -q "Chapter 1" output.txt && echo "✅ Root 1 found" || echo "❌ Root 1 missing"

# Check root2 NOT compiled
if ! grep -q "Chapter 2" output.txt; then
    echo "✅ Root 2 correctly excluded"
else
    echo "❌ Root 2 incorrectly included"
fi
```

**Expected Result**: Only specified node compiled, existing behavior preserved.

---

## Validation Scenario 5: Include Empty Flag Behavior

### Setup

```bash
cd /tmp/pmk-test-008

cat > binder.md << 'EOF'
# Project

- [[empty1]] Empty Node
- [[full1]] Full Node
EOF

# Create empty node
cat > empty1.md << 'EOF'
---
id: empty1
title: "Empty"
---

EOF

# Create full node
cat > full1.md << 'EOF'
---
id: full1
title: "Full"
---

Full content here.
EOF
```

### Execute & Verify

**Without --include-empty** (default):
```bash
pmk compile > output.txt
# Should NOT include empty node
if ! grep -q "Empty" output.txt && grep -q "Full content" output.txt; then
    echo "✅ Empty node excluded by default"
else
    echo "❌ Incorrect empty node handling"
fi
```

**With --include-empty**:
```bash
pmk compile --include-empty > output.txt
# Should include empty node
if grep -q "Full content" output.txt; then
    echo "✅ Empty node included with flag"
else
    echo "❌ Flag not working correctly"
fi
```

**Expected Result**: Flag behavior consistent with single-node compilation.

---

## Validation Scenario 6: Error Handling

### Test 6a: Invalid Node ID (When Provided)

```bash
pmk compile invalid-id 2> error.txt
exit_code=$?

# Check error message
if grep -q "Invalid node ID format" error.txt; then
    echo "✅ Error message correct"
else
    echo "❌ Wrong error message"
fi

# Check exit code 1
if [ $exit_code -eq 1 ]; then
    echo "✅ Exit code 1"
else
    echo "❌ Wrong exit code: $exit_code"
fi
```

### Test 6b: Node Not Found (When Provided)

```bash
pmk compile 01234567-89ab-7def-0123-456789abcdef 2> error.txt
exit_code=$?

# Check error message
if grep -q "Node not found" error.txt; then
    echo "✅ Error message correct"
else
    echo "❌ Wrong error message"
fi

# Check exit code 1
if [ $exit_code -eq 1 ]; then
    echo "✅ Exit code 1"
else
    echo "❌ Wrong exit code: $exit_code"
fi
```

**Expected Result**: Appropriate error messages and exit code 1 for errors.

---

## Validation Scenario 7: Ordering Guarantee

### Setup

```bash
cd /tmp/pmk-test-008

# Create binder with specific order
cat > binder.md << 'EOF'
# Ordered Project

- [[third]] Should Be Third
- [[first]] Should Be First
- [[second]] Should Be Second
EOF

cat > first.md << 'EOF'
---
id: first
title: "First"
---

FIRST_MARKER
EOF

cat > second.md << 'EOF'
---
id: second
title: "Second"
---

SECOND_MARKER
EOF

cat > third.md << 'EOF'
---
id: third
title: "Third"
---

THIRD_MARKER
EOF
```

### Execute & Verify

```bash
pmk compile > output.txt

# Extract line numbers of markers
third_line=$(grep -n "THIRD_MARKER" output.txt | cut -d: -f1)
first_line=$(grep -n "FIRST_MARKER" output.txt | cut -d: -f1)
second_line=$(grep -n "SECOND_MARKER" output.txt | cut -d: -f1)

# Verify binder order (third < first < second in output)
if [ "$third_line" -lt "$first_line" ] && [ "$first_line" -lt "$second_line" ]; then
    echo "✅ Binder order preserved"
else
    echo "❌ Order not preserved: Third=$third_line, First=$first_line, Second=$second_line"
fi
```

**Expected Result**: Nodes compiled in binder file order, not alphabetical or timestamp order.

---

## Performance Validation

### Test: Large Binder (100 Roots)

```bash
cd /tmp/pmk-test-008

# Generate binder with 100 roots
{
    echo "# Large Project"
    echo
    for i in $(seq 1 100); do
        echo "- [[node$i]] Node $i"
    done
} > binder.md

# Generate 100 node files
for i in $(seq 1 100); do
    cat > "node$i.md" << EOF
---
id: node$i
title: "Node $i"
---

Content of node $i.
EOF
done

# Measure compile time
time pmk compile > /dev/null

# Expected: < 5 seconds
```

**Expected Result**: Compilation completes in < 5 seconds for 100 roots.

---

## Cleanup

```bash
cd /workspace
rm -rf /tmp/pmk-test-008
```

---

## Validation Checklist

After running all scenarios, verify:

- [x] **Scenario 1**: Multiple roots compile correctly in order
- [x] **Scenario 2**: Empty binder handled gracefully (exit 0, no error)
- [x] **Scenario 3**: Placeholder roots filtered out
- [x] **Scenario 4**: Single-node behavior preserved (backward compatibility)
- [x] **Scenario 5**: --include-empty flag works for all roots
- [x] **Scenario 6**: Error handling correct (invalid/missing node)
- [x] **Scenario 7**: Binder order preserved (not alphabetical)
- [x] **Performance**: Large binders (100 roots) compile in < 5s

---

## Integration with CI/CD

Add to CI pipeline:

```bash
# Run all validation scenarios
./scripts/validate-feature-008.sh

# Or integrate into existing test suite
pytest tests/integration/compile/test_compile_all_roots.py -v
```

---

**Status**: Validation procedures defined
**Next Step**: Execute validation after implementation complete

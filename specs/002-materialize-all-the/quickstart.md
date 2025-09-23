# Quickstart: Materialize All Command Option

## Overview
This quickstart guide validates the `--all` option for `pmk materialize` through end-to-end test scenarios.

## Prerequisites
- PMK project with existing `_binder.md` file
- Multiple unmaterialized placeholders in binder
- PMK CLI properly installed and configured

## Test Scenario 1: Basic Bulk Materialization

### Setup
```bash
# Create test project with placeholders
mkdir test-materialize-all
cd test-materialize-all

# Create _binder.md with multiple placeholders
cat > _binder.md << 'EOF'
# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1]()
  - [Section 1.1]()
  - [Section 1.2]()
- [Chapter 2]()
- [Appendix A]()
<!-- END_MANAGED_BLOCK -->
EOF
```

### Expected Behavior
```bash
# Execute materialize all command
pmk materialize --all

# Expected output:
# Found 5 placeholders to materialize...
# ✓ Materialized 'Chapter 1' → 01923f0c-1234-7123-8abc-def012345678
# ✓ Materialized 'Section 1.1' → 01923f0c-1234-7123-8abc-def012345679
# ✓ Materialized 'Section 1.2' → 01923f0c-1234-7123-8abc-def012345680
# ✓ Materialized 'Chapter 2' → 01923f0c-1234-7123-8abc-def012345681
# ✓ Materialized 'Appendix A' → 01923f0c-1234-7123-8abc-def012345682
# Successfully materialized all 5 placeholders
```

### Validation
```bash
# Verify binder was updated with node IDs
grep -E '\[[^\]]+\]\([^)]+\.md\)' _binder.md | wc -l
# Expected: 5 lines (all placeholders now have node IDs)

# Verify node files were created
ls *.md | grep -E '^[0-9a-f-]{36}\.md$' | wc -l
# Expected: 5 main node files

ls *.notes.md | wc -l
# Expected: 5 notes files

# Verify no placeholders remain
pmk audit | grep PLACEHOLDER
# Expected: no output (no placeholders remaining)
```

## Test Scenario 2: Empty Binder Handling

### Setup
```bash
# Create project with no placeholders
mkdir test-empty-binder
cd test-empty-binder

cat > _binder.md << 'EOF'
# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Chapter 1](01923f0c-1234-7123-8abc-def012345678.md)
- [Chapter 2](01923f0c-1234-7123-8abc-def012345679.md)
<!-- END_MANAGED_BLOCK -->
EOF
```

### Expected Behavior
```bash
# Execute materialize all command
pmk materialize --all

# Expected output:
# No placeholders found in binder
```

### Validation
```bash
# Verify command exits successfully
echo $?
# Expected: 0 (success exit code)
```

## Test Scenario 3: Partial Failure Handling

### Setup
```bash
# Create test scenario with filesystem issues
mkdir test-partial-failure
cd test-partial-failure

# Create binder with placeholders
cat > _binder.md << 'EOF'
# Test Project

<!-- BEGIN_MANAGED_BLOCK -->
- [Valid Chapter]()
- [Another Valid Chapter]()
- [Chapter with "Invalid/Name"]()
<!-- END_MANAGED_BLOCK -->
EOF

# Create readonly directory to cause failure
mkdir readonly-test
chmod 444 readonly-test
```

### Expected Behavior
```bash
# Execute materialize all command
pmk materialize --all

# Expected output (partial failure scenario):
# Found 3 placeholders to materialize...
# ✓ Materialized 'Valid Chapter' → 01923f0c-1234-7123-8abc-def012345678
# ✓ Materialized 'Another Valid Chapter' → 01923f0c-1234-7123-8abc-def012345679
# ✗ Failed to materialize 'Chapter with "Invalid/Name"': Invalid characters in filename
# Materialized 2 of 3 placeholders (1 failure)
```

### Validation
```bash
# Verify partial success
grep -E '\[[^\]]+\]\([^)]+\.md\)' _binder.md | wc -l
# Expected: 2 lines (2 successful materializations)

# Verify error reporting
echo $?
# Expected: 1 (error exit code due to partial failure)
```

## Test Scenario 4: Command Validation

### Setup
```bash
mkdir test-validation
cd test-validation
echo "# Empty project" > _binder.md
```

### Expected Behavior: Mutually Exclusive Options
```bash
# Test mutual exclusion with title argument
pmk materialize "Some Title" --all

# Expected output:
# Error: Cannot specify both 'title' and '--all' options
# Exit code: 1
```

### Expected Behavior: Missing Options
```bash
# Test missing required options
pmk materialize

# Expected output:
# Error: Must specify either placeholder 'title' or '--all' flag
# Exit code: 1
```

## Test Scenario 5: Performance Validation

### Setup
```bash
# Create binder with many placeholders
mkdir test-performance
cd test-performance

# Generate binder with 100 placeholders
cat > _binder.md << 'EOF'
# Large Test Project

<!-- BEGIN_MANAGED_BLOCK -->
EOF

for i in {1..100}; do
    echo "- [Chapter $i]()" >> _binder.md
done

echo "<!-- END_MANAGED_BLOCK -->" >> _binder.md
```

### Expected Behavior
```bash
# Execute with time measurement
time pmk materialize --all

# Expected:
# - Completes in under 30 seconds
# - Reports progress during execution
# - All 100 placeholders materialized successfully
```

### Validation
```bash
# Verify all placeholders were materialized
ls *.md | grep -E '^[0-9a-f-]{36}\.md$' | wc -l
# Expected: 100

# Verify binder integrity
pmk audit | grep ERROR
# Expected: no output (no errors)
```

## Integration Test Validation

### Success Criteria
All test scenarios must pass with expected behaviors:

1. **Basic functionality**: Multiple placeholders materialized successfully
2. **Empty handling**: Graceful handling of binders with no placeholders
3. **Error resilience**: Partial failures don't prevent other materializations
4. **Input validation**: Proper error messages for invalid command usage
5. **Performance**: Acceptable performance with large numbers of placeholders

### Automation Script
```bash
#!/bin/bash
# run_quickstart_tests.sh

set -e

echo "Running Materialize All Quickstart Tests..."

# Test 1: Basic bulk materialization
echo "Test 1: Basic bulk materialization"
./test_basic_bulk.sh

# Test 2: Empty binder handling
echo "Test 2: Empty binder handling"
./test_empty_binder.sh

# Test 3: Partial failure handling
echo "Test 3: Partial failure handling"
./test_partial_failure.sh

# Test 4: Command validation
echo "Test 4: Command validation"
./test_command_validation.sh

# Test 5: Performance validation
echo "Test 5: Performance validation"
./test_performance.sh

echo "All quickstart tests passed! ✅"
```

## Troubleshooting

### Common Issues

**Issue**: `Error: No _binder.md file found`
**Solution**: Ensure you're in a PMK project directory with a valid binder file

**Issue**: `Error: Permission denied creating file`
**Solution**: Check directory permissions and available disk space

**Issue**: `Error: Already materialized`
**Solution**: Use `pmk audit` to identify which items are already materialized

**Issue**: Performance degradation with large binders
**Solution**: Consider using `--parent` option (when implemented) to limit scope

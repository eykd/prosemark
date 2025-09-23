#!/bin/sh
# Conflict-safe quality check script that prevents ruff/mypy conflicts
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "${YELLOW}🔍 Starting conflict-safe quality check...${NC}"

# Step 1: Initial state check
echo "${YELLOW}📋 Step 1: Checking initial state...${NC}"
if ! uv run mypy src tests >/dev/null 2>&1; then
    echo "${RED}❌ Initial mypy check failed. Please fix mypy errors first.${NC}"
    echo "Run: uv run mypy src tests"
    exit 1
fi

if ! uv run ruff check . >/dev/null 2>&1; then
    echo "${YELLOW}⚠️  Initial ruff check has violations. Will fix safely...${NC}"
fi

echo "${GREEN}✅ Initial mypy check passed${NC}"

# Step 2: Save state for conflict detection
echo "${YELLOW}💾 Step 2: Saving current state...${NC}"
mypy_baseline=$(uv run mypy src tests 2>&1 | grep -E "(error|Success)" | head -1)
echo "Baseline mypy status: $mypy_baseline"

# Step 3: Conservative ruff fixes (formatting only, no import changes)
echo "${YELLOW}🎨 Step 3: Applying safe formatting fixes...${NC}"
uv run ruff check --fix --select E,W --unsafe-fixes --ignore T100 --ignore ERA001 .
uv run ruff format

# Step 4: Check if mypy still passes after formatting
echo "${YELLOW}🔍 Step 4: Verifying mypy still passes after formatting...${NC}"
mypy_after_format=$(uv run mypy src tests 2>&1 | grep -E "(error|Success)" | head -1)

if [ "$mypy_baseline" != "$mypy_after_format" ]; then
    echo "${RED}❌ CONFLICT DETECTED: Ruff formatting changes affected mypy!${NC}"
    echo "Before: $mypy_baseline"
    echo "After:  $mypy_after_format"
    echo "Please review and fix manually."
    exit 1
fi

echo "${GREEN}✅ Formatting applied safely${NC}"

# Step 5: Apply remaining ruff fixes carefully, excluding conflict-prone rules
echo "${YELLOW}🔧 Step 5: Applying remaining safe fixes...${NC}"
# Apply import sorting and other safe fixes, but NOT unused import removal
uv run ruff check --fix --select I,F402,F403,F405,F811,F821,F822,F823,F841 --ignore F401 .

# Step 6: Final mypy check
echo "${YELLOW}🔍 Step 6: Final mypy verification...${NC}"
mypy_final=$(uv run mypy src tests 2>&1 | grep -E "(error|Success)" | head -1)

if [ "$mypy_baseline" != "$mypy_final" ]; then
    echo "${RED}❌ CONFLICT DETECTED: Ruff fixes affected mypy!${NC}"
    echo "Before: $mypy_baseline"
    echo "After:  $mypy_final"
    echo "Please review and fix manually."
    exit 1
fi

# Step 7: Check for remaining ruff violations that need manual attention
echo "${YELLOW}🔍 Step 7: Checking for remaining violations...${NC}"
if ! uv run ruff check . >/dev/null 2>&1; then
    echo "${YELLOW}⚠️  Some ruff violations remain (likely F401 unused imports with type: ignore)${NC}"
    echo "Please review these manually:"
    uv run ruff check . | head -10
    echo "These may be intentional due to mypy requirements."
fi

echo "${GREEN}✅ Conflict-safe quality check completed successfully!${NC}"
echo "${GREEN}✅ Mypy: PASSED${NC}"
echo "${GREEN}✅ Ruff formatting: APPLIED${NC}"
echo "${GREEN}✅ No conflicts detected${NC}"

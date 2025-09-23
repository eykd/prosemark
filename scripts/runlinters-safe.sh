#!/bin/sh
# Safe version of runlinters.sh that prevents ruff/mypy conflicts
set -e
set -x

set -a # automatically export all variables
source .env.test
set +a

echo "🔍 Running safe linting workflow..."

# Step 1: Check initial mypy state
echo "📋 Checking initial mypy state..."
mypy_initial=$(uv run mypy src tests 2>&1 || true)
mypy_status=$?

if [ $mypy_status -ne 0 ]; then
    echo "❌ Mypy has errors. Please fix mypy issues first:"
    echo "$mypy_initial"
    exit 1
fi

# Step 2: Apply safe ruff fixes (formatting + safe fixes, avoid F401)
echo "🎨 Applying safe ruff fixes..."
## Automatically reformat code, but ignore breakpoint() and commented code:
## Also ignore F401 (unused imports) to avoid conflicts with mypy type: ignore
uv run ruff check --fix --unsafe-fixes --ignore T100 --ignore ERA001 --ignore F401
uv run ruff format

# Step 3: Verify mypy still passes
echo "🔍 Verifying mypy after ruff changes..."
uv run mypy src tests

# Step 4: Report any remaining F401 violations for manual review
echo "📋 Checking for remaining unused imports (may be intentional for mypy)..."
remaining_f401=$(uv run ruff check --select F401 . 2>&1 || true)
if [ -n "$remaining_f401" ]; then
    echo "⚠️  Unused imports detected (review if needed for mypy):"
    echo "$remaining_f401"
fi

echo "✅ Safe linting completed successfully!"

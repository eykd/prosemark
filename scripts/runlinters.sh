#!/bin/sh
set -e
set -x

set -a # automatically export all variables
source .env.test
set +a

## Automatically reformat code, but ignore breakpoint() and commented code:
uv run ruff check --fix --unsafe-fixes --ignore T100  --ignore ERA001
uv run ruff format
uv run mypy src tests

#!/bin/sh
set -e
set -x

set -a # automatically export all variables
source .env.test
set +a

## # Automatically reformat code, but ignore breakpoint() and commented code:
uv run ruff check --fix --ignore T100  --ignore ERA001
uv run ruff format
uv run mypy src tests
uv run  --env-file=.env.test \
   pytest \
   -vv \
   --new-first \
   --exitfirst \
   --disable-warnings \
   --capture=no \
   -m "not slow" \
   "$@"

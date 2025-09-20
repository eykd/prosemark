#!/bin/sh
set -e
set -x

set -a # automatically export all variables
. "$(dirname "$0")/../.env.test"
set +a

uv run ruff check --fix
uv run ruff format
uv run mypy src tests
uv run  --env-file=.env.test \
   pytest \
   -vv \
   --cov-fail-under=100

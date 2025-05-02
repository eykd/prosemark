#!/bin/sh
set -e
set -x

set -a # automatically export all variables
source .env.test
set +a

## # Automatically reformat code, but ignore breakpoint() and commented code:
uv run  --env-file=.env.test \
   pytest \
   -vv \
   --cov-fail-under=100

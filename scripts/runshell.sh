#!/bin/sh
set -e
set -x

set -a # automatically export all variables
source .env
source .venv/bin/activate
set +a

uv run ipython

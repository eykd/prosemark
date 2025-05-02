#!/usr/bin/env bash
set -x
while sleep 1; do find . -iname '*.py' | entr -d ./scripts/runtests.sh; done

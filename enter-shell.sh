#!/bin/bash

set -euo pipefail

# Simple shell script for development container

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }

# Check if container is running, start if not
if ! docker-compose ps -q claude-container 2>/dev/null | xargs docker inspect --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
    log_info "Container is not running. Starting it first..."
    ./start-container.sh
    echo
fi

log_info "Syncing Python dependencies..."
docker-compose exec claude-container uv sync --all-groups

log_info "Opening shell in container..."
docker-compose exec claude-container zsh

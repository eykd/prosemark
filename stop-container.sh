#!/bin/bash

set -euo pipefail

# Simple stop script for development container

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }

# Check if container is running
if ! docker-compose ps -q claude-container 2>/dev/null | xargs docker inspect --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
    log_warning "Container is not running"
    exit 0
fi

log_info "Stopping container (preserving state)..."
docker-compose stop
log_success "Container stopped. Use './start-container.sh' to resume"

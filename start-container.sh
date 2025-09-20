#!/bin/bash

set -euo pipefail

# Simple start script for development container

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Check if .claude.json is empty and destroy container if so
if [[ -f ".claude.json" ]]; then
    content=$(cat .claude.json | tr -d '[:space:]')
    if [[ "$content" == "{}" || -z "$content" ]]; then
        log_warning ".claude.json is empty - destroying existing container..."
        docker-compose down -v 2>/dev/null || true
        log_info "Container destroyed due to empty .claude.json"
    fi
fi

# Check if container is already running
if docker-compose ps -q claude-container 2>/dev/null | xargs docker inspect --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
    log_warning "Container is already running"
    log_info "Use './enter-shell.sh' to connect"
    exit 0
fi

log_info "Starting development container..."
docker-compose up -d

# Wait for container to be ready
sleep 2

if docker-compose ps -q claude-container 2>/dev/null | xargs docker inspect --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
    log_success "Container started successfully"
    log_info "Use './enter-shell.sh' to connect"
else
    log_error "Failed to start container"
    exit 1
fi

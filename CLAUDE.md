# Claude Code Context

## Project: Prosemark Write-Only Freewriting Interface

### Current Feature: 003-write-only-freewriting

**Branch**: `003-write-only-freewriting`
**Status**: Design Phase (Phase 1 complete)

**Technology Stack**:
- Python 3.13
- Textual TUI framework
- Typer CLI framework
- pytest testing
- Plain text storage (Markdown + YAML frontmatter)

**Architecture**: Hexagonal (Ports & Adapters)
- Domain services with port interfaces
- TUI adapter using Textual
- CLI adapter using Typer
- File system adapter for persistence

**Key Components**:
- `FreewriteServicePort`: Core domain operations
- `TUIAdapterPort`: Terminal UI interface
- `CLIAdapterPort`: Command line interface
- `NodeServicePort`: Node management
- `FileSystemPort`: File operations

**Recent Changes**:
- Created comprehensive research on Textual framework
- Designed domain model with entities and validation rules
- Created hexagonal architecture contracts
- Built quickstart guide with test scenarios

**Quality Requirements** (Constitutional):
- 100% test coverage required
- 100% mypy type checking
- 100% ruff linting compliance
- Test-first development (TDD) mandatory

**File Locations**:
- Specs: `/workspace/specs/003-write-only-freewriting/`
- Research: `research.md`
- Data model: `data-model.md`
- Contracts: `contracts/`
- Quickstart: `quickstart.md`

**Next Steps**:
- Phase 2: Task generation via `/tasks` command
- Implementation following TDD principles
- Integration with existing prosemark domain

**Command Pattern**:
- `pmk write` - Daily freewrite file
- `pmk write <uuid>` - Write to specific node
- `pmk write --title "title"` - Add session title
- Optional: `--word-count-goal`, `--time-limit`

**UI Layout**:
- 80% top: Content display (bottom of file)
- 20% bottom: Input box with readline editing
- Real-time word count and timer display
- Error handling within TUI (no crashes)

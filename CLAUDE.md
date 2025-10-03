# Claude Code Context

## Project: Prosemark Node Templates System

### Completed Feature: 007-node-templates-i

**Branch**: `master`
**Status**: Implementation Complete (All phases finished)

**Technology Stack**:
- Python 3.13
- Click CLI framework
- pytest testing
- Plain text storage (Markdown + YAML frontmatter)

**Architecture**: Hexagonal (Ports & Adapters)
- Domain entities with validation
- Template services with business logic
- File-based repository adapter
- CLI user prompter adapter
- Template validator adapter

**Key Components** (Templates Module):
- `Template` & `Placeholder`: Core domain entities
- `TemplateService`: Business logic orchestration
- `FileTemplateRepository`: File-based template storage
- `CLIUserPrompter`: Interactive placeholder input
- `ProsemarkTemplateValidator`: Template validation
- `TemplatesContainer`: Dependency injection

**Implementation Highlights**:
- 26 Python files implementing complete template system
- CLI integration with `pmk add --template` and `--list-templates`
- Interactive placeholder replacement system
- Support for both single templates and directory templates
- Hexagonal architecture with ports and adapters
- Container-based dependency injection

**Quality Requirements** (Constitutional):
- 100% test coverage required
- 100% mypy type checking
- 100% ruff linting compliance
- Test-first development (TDD) mandatory

**File Locations**:
- Implementation: `/workspace/src/prosemark/templates/`
- Specs: `/workspace/specs/007-node-templates-i/`
- Tests: `/workspace/tests/integration/templates/`
- CLI integration: `/workspace/src/prosemark/cli/add.py`

**Template Commands**:
- `pmk add "Title" --template template-name` - Create node from template
- `pmk add --list-templates` - List available templates
- Templates stored in `./templates/` directory
- Supports interactive placeholder replacement
- Markdown + YAML frontmatter format

**Template Format**:
```markdown
---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
---

# {{title}}

Written by {{author}}.

{{content}}
```

**Placeholder Features**:
- Required placeholders: `{{name}}` (must provide value)
- Optional placeholders: `{{name}}` with `name_default: "value"`
- Interactive prompting during node creation
- Support for descriptions via `name_description: "help text"`

### Current Feature: 009-subtree-word-count (Planning Phase)

**Branch**: `009-subtree-word-count`
**Status**: Planning Complete - Ready for /tasks

**Feature Summary**: Add `pmk wc` subcommand to count words in compiled node subtrees using US English word-splitting conventions.

**Technology Stack**:
- Python 3.13
- Click 8.1.8+, Typer 0.12.0+ (CLI)
- PyYAML 6.0.2+ (storage)
- Pydantic 2.11.4+ (validation)
- pytest 8.3.5+ with coverage
- mypy 1.15.0+ strict mode
- ruff 0.11.8+ linting

**Architecture**: Hexagonal (extends existing pattern)
- Domain: `domain/wordcount/` - Pure word counting logic
- Ports: `ports/wordcount/` - WordCounterPort protocol
- Adapters: `adapters/wordcount/` - Regex-based counter
- Use Cases: `app/wordcount/` - WordCountUseCase orchestration
- CLI: `cli/wc.py` - Command entry point

**Key Design Decisions**:
1. Reuse existing `CompileSubtreeUseCase` for text compilation
2. Regex-based word-splitting with US English conventions
3. Error handling matches `compile` command patterns
4. Plain number output to stdout for scriptability

**Word Counting Rules**:
- Contractions count as one word (don't, it's)
- Hyphenated compounds count as one word (well-known)
- Numbers count as words (123, 3.14)
- URLs count as single words (https://example.com)
- Emails count as single words (user@example.com)
- Split on whitespace, normalize multiple spaces/newlines

**Models**:
- `WordCountRequest(node_id, include_empty)` - Input
- `WordCountResult(count, content)` - Output
- `WordCounterPort` - Port interface for counting implementations

**File Locations**:
- Specs: `/workspace/specs/009-subtree-word-count/`
- Implementation: `/workspace/src/prosemark/wordcount/` (pending)
- Tests: `/workspace/tests/{unit,contract,integration}/wordcount/` (pending)

**Next Steps**:
- Run `/tasks` to generate task list
- Implement following TDD approach
- Ensure 100% coverage, mypy, ruff compliance

### Previous Feature: 003-write-only-freewriting (Design Phase)

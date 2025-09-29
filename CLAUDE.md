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

### Previous Feature: 003-write-only-freewriting (Design Phase)

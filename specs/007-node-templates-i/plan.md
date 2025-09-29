
# Implementation Plan: Node Templates

**Branch**: `007-node-templates-i` | **Date**: 2025-09-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/workspace/specs/007-node-templates-i/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Enable users to create predefined node structures from templates stored in `./templates` directory. The system will extend the `pmk add` command to support `--template` parameter for creating individual nodes or node trees from template files. Templates use prosemark format with interactive placeholder replacement and strict validation with immediate error handling for invalid templates.

## Technical Context
**Language/Version**: Python 3.13
**Primary Dependencies**: Typer (CLI), Click, PyYAML, Pydantic, Textual (TUI), UUID Extension
**Storage**: Plain text files (Markdown + YAML frontmatter), local file system
**Testing**: pytest with coverage, mypy for type checking, ruff for linting
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single CLI application with hexagonal architecture
**Performance Goals**: Interactive CLI response (<100ms), template validation (<500ms)
**Constraints**: Maintain Obsidian compatibility, 100% test coverage, strict type checking
**Scale/Scope**: Local templates directory, individual user workflows, small to medium template collections

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Hexagonal Architecture**: ✅ PASS - Template functionality will be implemented through ports and adapters, with domain logic separated from CLI and file system concerns.

**Test-First Development**: ✅ PASS - All template functionality will be developed using TDD with tests written first, confirmed to fail, then implementation to pass.

**Plain Text Storage**: ✅ PASS - Templates use existing Markdown + YAML frontmatter format, maintaining Obsidian compatibility.

**Code Quality Standards**: ✅ PASS - All code will meet 100% mypy type checking, 100% ruff linting, 100% test coverage requirements with no exceptions.

**CLI-First Interface**: ✅ PASS - Template functionality extends existing `pmk add` command with new `--template` and `--list-templates` flags.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/prosemark/
├── templates/                    # NEW: Template management feature
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── template.py      # Template entity with validation
│   │   │   └── placeholder.py   # Placeholder entity
│   │   ├── services/
│   │   │   ├── template_service.py      # Core template operations
│   │   │   └── placeholder_service.py   # Placeholder processing
│   │   └── exceptions/
│   │       └── template_exceptions.py   # Template-specific errors
│   ├── ports/
│   │   ├── template_repository_port.py  # Template storage interface
│   │   ├── template_validator_port.py   # Template validation interface
│   │   └── user_prompter_port.py        # User interaction interface
│   └── adapters/
│       ├── file_template_repository.py  # File system template storage
│       ├── prosemark_template_validator.py # Prosemark format validation
│       └── cli_user_prompter.py         # CLI-based user prompting
├── cli/
│   └── commands/
│       └── add.py               # EXTEND: Add --template support
└── app/                         # EXTEND: Add template use cases
    └── use_cases/
        ├── create_from_template.py      # Template instantiation
        └── list_templates.py            # Template discovery

tests/
├── unit/
│   └── prosemark/
│       └── templates/
│           ├── domain/
│           ├── ports/
│           └── adapters/
├── contract/
│   └── templates/               # Template port contract tests
└── integration/
    └── templates/               # End-to-end template workflows
```

**Structure Decision**: Single CLI application following existing hexagonal architecture. Template functionality is added as a new domain module with complete separation of concerns through ports and adapters pattern.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Port contract tests for each interface (3 ports = 3 contract test tasks) [P]
- Domain entity creation tasks following data model (4 entities) [P]
- Service layer implementation (2 services: template, placeholder) [P]
- Adapter implementations (3 adapters: file repo, validator, prompter)
- CLI integration (extend add command with new parameters)
- Use case implementations (2 use cases: create from template, list templates)
- Integration tests for complete workflows (4 user scenarios)
- Documentation and error handling validation

**Ordering Strategy**:
- **Phase A**: Contract tests (all parallel) [P]
- **Phase B**: Domain entities and value objects [P]
- **Phase C**: Services implementation (depends on entities)
- **Phase D**: Adapter implementations (depends on contracts)
- **Phase E**: Use cases (depends on services and adapters)
- **Phase F**: CLI integration (depends on use cases)
- **Phase G**: Integration tests (depends on complete implementation)
- **Phase H**: Documentation and final validation

**Dependency Analysis**:
- Entities are independent → parallel implementation
- Services depend on entities → sequential after Phase B
- Adapters implement ports → parallel within phase
- CLI integration requires use cases → sequential after Phase E
- Integration tests require complete system → final phase

**Estimated Output**: 28-32 numbered, ordered tasks in tasks.md
- 3 contract test tasks
- 6 entity/value object tasks
- 4 service implementation tasks
- 6 adapter implementation tasks
- 4 use case tasks
- 2 CLI integration tasks
- 4 integration test tasks
- 3 validation/documentation tasks

**Test Strategy**:
- Contract tests ensure port compliance
- Unit tests for each domain entity and service
- Adapter tests with both real and fake implementations
- Integration tests covering complete user workflows
- Error handling tests for all failure scenarios

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*

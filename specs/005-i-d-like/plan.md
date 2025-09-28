
# Implementation Plan: Preserve Extraneous Text in Binder Operations

**Branch**: `005-i-d-like` | **Date**: 2025-09-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/workspace/specs/005-i-d-like/spec.md`

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
Enhance all binder operations to preserve extraneous text (narrative content outside Markdown lists and UUID7 links) while only modifying structural hierarchy elements. Operations must maintain exact positioning and formatting of non-structural content, treating malformed syntax as preservable text.

## Technical Context
**Language/Version**: Python 3.13 (existing codebase)
**Primary Dependencies**: Textual (TUI), Typer (CLI), Pydantic (data validation), PyYAML (frontmatter), uuid-extension (UUID7)
**Storage**: Plain text files (Markdown + YAML frontmatter, Obsidian-compatible)
**Testing**: pytest with 100% coverage requirement, mypy type checking, ruff linting
**Target Platform**: Cross-platform CLI tool (Linux, macOS, Windows)
**Project Type**: single (hexagonal architecture with ports/adapters)
**Performance Goals**: Real-time text parsing for immediate feedback during writing sessions
**Constraints**: Must preserve exact text formatting, maintain Obsidian compatibility, zero data loss during operations
**Scale/Scope**: Individual writer usage, handling projects with hundreds of documents and binder structures

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**✅ I. Hexagonal Architecture**: Feature enhances existing binder operations through domain services with clear port/adapter separation. Business logic (text preservation) isolated from parsing implementation.

**✅ II. Test-First Development**: All new functionality will follow TDD - tests written first, confirmed to fail, then implementation proceeds. 100% coverage requirement maintained.

**✅ III. Plain Text Storage**: Feature preserves existing Markdown + YAML frontmatter format. Maintains Obsidian compatibility. No storage format changes.

**✅ IV. Code Quality Standards**: All code will achieve 100% mypy, ruff, and test compliance before completion. Quality gates enforced through specialized agents.

**✅ V. CLI-First Interface**: Enhancement integrates with existing CLI commands (`pmk compile`, etc.). No new interface patterns required.

**PASS**: No constitutional violations detected. Feature aligns with existing architecture and quality standards.

**Post-Design Re-evaluation**:
- ✅ **Hexagonal Architecture**: New `PreservedText` and `ParserResult` value objects maintain domain purity. Enhanced parser port interface preserves clean separation.
- ✅ **Test-First Development**: Contract scenarios define clear test requirements. TDD approach maintained with failing contract tests before implementation.
- ✅ **Plain Text Storage**: No changes to storage format. Enhancements preserve existing Markdown + YAML frontmatter compatibility.
- ✅ **Code Quality Standards**: Enhanced interfaces follow existing patterns. All new code will meet 100% quality requirements.
- ✅ **CLI-First Interface**: No new CLI commands. Feature transparently enhances existing binder operations.

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
├── domain/             # Core business logic (existing)
│   ├── binder.py      # Enhanced for text preservation
│   └── models.py      # Domain entities
├── ports/             # Interface definitions (existing)
│   └── binder_repo.py # Enhanced port interface
├── adapters/          # Implementation details (existing)
│   ├── markdown_binder_parser.py  # Enhanced parser
│   └── binder_repo_fs.py          # Enhanced filesystem repo
├── app/               # Use cases/application services (existing)
│   └── [new use cases for enhanced operations]
└── cli/               # Command interface (existing)
    └── [enhanced existing commands]

tests/
├── unit/              # Domain logic tests
├── contract/          # Port/adapter contract tests
└── integration/       # End-to-end feature tests
```

**Structure Decision**: Single project with hexagonal architecture. All enhancements integrate with existing domain, ports, and adapters. No new structural patterns required - feature enhances existing binder parsing and manipulation capabilities.

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
- Contract scenarios → failing contract test tasks [P]
- Enhanced parser value objects → domain model tasks [P]
- Text preservation logic → parser enhancement tasks
- Integration scenarios → end-to-end test tasks

**Specific Task Categories**:
1. **Contract Tests**: 4 failing tests from contract scenarios [P]
2. **Domain Models**: Create `PreservedText`, `ParserResult`, `StructuralElement` [P]
3. **Enhanced Parser**: Enhance `MarkdownBinderParser` with preservation logic
4. **Validation Logic**: UUID7 validation and text classification
5. **Integration Tests**: Quickstart scenarios as automated tests [P]
6. **Round-Trip Tests**: Ensure parse/render integrity

**Ordering Strategy**:
- TDD order: Contract tests → Domain models → Parser implementation
- Dependency order: Value objects → Parser logic → Integration
- Parallel tasks: Independent value objects, separate test files
- Sequential: Parser enhancement depends on domain models

**Estimated Output**: 18-22 numbered, ordered tasks in tasks.md

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
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*

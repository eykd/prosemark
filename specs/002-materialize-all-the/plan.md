
# Implementation Plan: Materialize All Command Option

**Branch**: `002-materialize-all-the` | **Date**: 2025-09-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/workspace/specs/002-materialize-all-the/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
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
Add `--all` option to the `pmk materialize` command that enables bulk materialization of all unmaterialized placeholders in the current binder. This improves developer workflow by eliminating the need to run individual materialize commands for each placeholder.

## Technical Context
**Language/Version**: Python 3.11 (existing PMK project)
**Primary Dependencies**: Click CLI framework, existing PMK core libraries
**Storage**: Plain text files (Markdown + YAML frontmatter) - binder and placeholder files
**Testing**: pytest (following existing PMK patterns)
**Target Platform**: CLI tool - cross-platform (Linux, macOS, Windows)
**Project Type**: single - CLI extension to existing PMK project
**Performance Goals**: Process placeholders efficiently, provide progress feedback for large binders
**Constraints**: Must maintain compatibility with existing `pmk materialize` command, follow PMK's plain text storage principles
**Scale/Scope**: Handle binders with 1-1000+ placeholders efficiently, maintain responsiveness

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Hexagonal Architecture**: ✅ PASS - Feature extends existing CLI interface through adapter pattern, business logic will be separated from CLI concerns through proper ports/adapters

**Test-First Development**: ✅ PASS - Will follow TDD for all new functionality, write tests before implementation

**Plain Text Storage**: ✅ PASS - Uses existing PMK plain text storage (Markdown + YAML), no new storage requirements

**Code Quality Standards**: ✅ PASS - All code will achieve 100% compliance with mypy, ruff, and pytest requirements before commit

**CLI-First Interface**: ✅ PASS - Feature is purely a CLI extension adding `--all` flag to existing `pmk materialize` command

## Post-Design Constitution Re-Check
*After Phase 1 design completion*

**Hexagonal Architecture**: ✅ PASS - Design maintains clear separation between CLI, use case, and domain layers. New batch materialization logic will be properly isolated in application layer.

**Test-First Development**: ✅ PASS - Contract specifications include comprehensive test scenarios. TDD approach confirmed with failing tests to be written before implementation.

**Plain Text Storage**: ✅ PASS - No changes to storage format. Uses existing _binder.md structure and node file patterns.

**Code Quality Standards**: ✅ PASS - All new code will follow existing quality standards. Type contracts specified for all new interfaces.

**CLI-First Interface**: ✅ PASS - CLI contracts maintain stdin/args → stdout pattern. JSON and human-readable output formats specified.

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
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 1 (Single project) - CLI extension to existing PMK project

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
   - Run `.specify/scripts/bash/update-agent-context.sh claude` for your AI assistant
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
- Each CLI contract scenario → contract test task [P]
- Each use case contract → use case test task [P]
- Each data model entity → domain model task [P]
- Each quickstart scenario → integration test task
- Implementation tasks to make all tests pass

**Specific Task Categories**:

1. **Contract Tests** (Phase 2A - Tests First):
   - CLI contract test for `--all` flag validation [P]
   - CLI contract test for batch materialization flow [P]
   - Use case contract test for MaterializeAllPlaceholders [P]
   - Error scenario contract tests [P]

2. **Domain Models** (Phase 2B - Data Structures):
   - BatchMaterializeResult value object [P]
   - MaterializeResult value object [P]
   - MaterializeFailure value object [P]
   - PlaceholderSummary value object [P]

3. **Use Case Layer** (Phase 2C - Business Logic):
   - MaterializeAllPlaceholders use case implementation
   - Placeholder discovery service integration
   - Progress reporting callback system
   - Error aggregation and reporting logic

4. **CLI Adapter** (Phase 2D - Interface Layer):
   - Extend materialize command with --all flag
   - Add mutual exclusion validation
   - Implement batch progress reporting
   - Add comprehensive error handling

5. **Integration Tests** (Phase 2E - End-to-End):
   - Basic bulk materialization scenario
   - Empty binder handling scenario
   - Partial failure scenario
   - Command validation scenarios
   - Performance test with 100+ placeholders

**Ordering Strategy**:
- TDD order: All tests before any implementation
- Dependency order: Domain models → Use cases → CLI adapters
- Parallel execution: Contract tests and domain models can be developed concurrently
- Sequential dependencies: Use cases depend on domain models, CLI depends on use cases

**Task Dependencies**:
- Contract tests → Independent [P]
- Domain models → Independent [P]
- Use case implementation → Requires domain models
- CLI adapter → Requires use case implementation
- Integration tests → Requires CLI adapter

**Estimated Output**: 18-22 numbered, ordered tasks in tasks.md

**Quality Gates per Phase**:
- Phase 2A: All contract tests written and failing
- Phase 2B: All domain models implemented with 100% test coverage
- Phase 2C: Use case implemented with all contract tests passing
- Phase 2D: CLI adapter implemented with all tests passing
- Phase 2E: All integration tests passing, quickstart scenarios validated

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
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (None required)

---
*Based on Constitution v1.1.0 - See `.specify/memory/constitution.md`*


# Implementation Plan: Structure Command Subtree Display

**Branch**: `006-structure-command-subtree` | **Date**: 2025-09-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-structure-command-subtree/spec.md`

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
Extend the `structure` CLI command to accept an optional Node ID parameter (UUID format), enabling users to display only the subtree starting from the specified node and its descendants. This provides focused navigation in large document trees while maintaining backward compatibility with the existing full-tree display.

## Technical Context
**Language/Version**: Python 3.13
**Primary Dependencies**: Typer (CLI), Pydantic (validation), UUID-extension (UUIDv7)
**Storage**: File system (Markdown + YAML frontmatter)
**Testing**: pytest with 100% coverage requirement
**Target Platform**: Cross-platform CLI (Linux/macOS/Windows)
**Project Type**: single - CLI application with hexagonal architecture
**Performance Goals**: Best-effort performance (no specific requirements per clarification)
**Constraints**: Must maintain backward compatibility with existing command
**Scale/Scope**: Tree structures up to 1000+ nodes

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Architecture**: Feature extends existing use case, maintains ports/adapters separation
- [x] **Test-First Development**: Tests will be written before implementation changes
- [x] **Plain Text Storage**: No changes to storage format, reads existing Markdown/YAML
- [x] **Code Quality Standards**: Will achieve 100% mypy, ruff, and test compliance
- [x] **CLI-First Interface**: Extends existing CLI command with backward compatibility

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
├── domain/
│   └── models.py          # NodeId value object (existing)
├── app/
│   └── use_cases.py       # ShowStructure use case (existing, already supports node_id)
├── ports/
│   └── binder_repo.py     # BinderRepoPort interface (existing)
├── adapters/
│   └── binder_repo_fs.py  # File system adapter (existing)
└── cli/
    ├── main.py            # Main Typer CLI (needs node_id argument)
    └── structure.py       # Legacy Click CLI (already has node_id)

tests/
├── unit/
│   └── cli/
│       └── test_structure.py  # Unit tests for structure command (needs extension)
├── integration/
│   └── cli/
│       └── test_structure_integration.py  # Integration tests (new)
└── contract/
    └── cli/
        └── test_structure_contract.py  # Contract tests (new)
```

**Structure Decision**: Single project with hexagonal architecture. The feature only requires modification to the CLI layer (main.py) and addition of comprehensive tests. All domain and application logic already exists and supports the node_id parameter.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - ✅ No NEEDS CLARIFICATION items found (all clarified in spec)
   - ✅ Research existing implementation status
   - ✅ Investigate current architecture patterns

2. **Generate and dispatch research agents**:
   - ✅ Researched existing ShowStructure use case implementation
   - ✅ Investigated CLI integration patterns (Typer vs Click)
   - ✅ Analyzed current error handling approach

3. **Consolidate findings** in `research.md`:
   - ✅ Feature partially implemented (domain/app layers complete)
   - ✅ Only CLI integration needed in main.py
   - ✅ Test coverage required per constitution

**Output**: ✅ research.md completed with implementation gap analysis

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - ✅ NodeId, Binder, BinderItem entities documented
   - ✅ UUID validation rules specified
   - ✅ No state transitions (read-only operation)

2. **Generate API contracts** from functional requirements:
   - ✅ CLI interface contract created
   - ✅ Command signature: `pmk structure [OPTIONS] [NODE_ID]`
   - ✅ Error responses documented in `/contracts/cli-interface.md`

3. **Generate contract tests** from contracts:
   - 🔄 Deferred to Phase 2 (tests will be created with implementation)
   - Tests will cover: valid node_id, invalid format, not found, empty tree
   - TDD approach: write failing tests first

4. **Extract test scenarios** from user stories:
   - ✅ 5 test scenarios documented in quickstart.md
   - ✅ Covers all acceptance criteria from spec
   - ✅ Includes error cases and edge conditions

5. **Update agent file incrementally**:
   - ✅ Ran `.specify/scripts/bash/update-agent-context.sh claude`
   - ✅ Updated CLAUDE.md with Python 3.13, Typer, feature info
   - ✅ Preserved existing content and structure

**Output**: ✅ data-model.md, ✅ /contracts/cli-interface.md, ✅ quickstart.md, ✅ CLAUDE.md updated

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
Since most functionality exists, tasks focus on CLI integration and testing:
1. Write failing unit tests for structure command with node_id
2. Write failing integration tests for subtree scenarios
3. Add node_id argument to Typer CLI in main.py
4. Update command to parse and validate node_id
5. Pass node_id to existing ShowStructure.execute()
6. Ensure all tests pass with 100% coverage
7. Run quality gates (mypy, ruff, pytest)

**Ordering Strategy**:
- TDD order: Write all tests first (failing)
- Implementation: Minimal change to main.py
- Validation: Quality gates must pass 100%
- Tests can be written in parallel [P]

**Estimated Output**: 8-10 focused tasks (mostly testing)

**Key Implementation Points**:
- Leverage existing ShowStructure.execute(node_id) method
- Maintain backward compatibility (optional argument)
- Follow existing error handling patterns
- Use NodeId value object for validation

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
- [x] Complexity deviations documented (none - simple feature)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*

# Implementation Plan: Subtree Word Count

**Branch**: `009-subtree-word-count` | **Date**: 2025-10-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/workspace/specs/009-subtree-word-count/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ No NEEDS CLARIFICATION in spec (resolved via /clarify)
   → ✅ Project Type: single (hexagonal architecture)
3. Fill the Constitution Check section
   → ✅ Based on constitution v1.1.0
4. Evaluate Constitution Check section
   → ✅ No violations - aligns with hexagonal architecture
   → ✅ Progress updated: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → ✅ Research complete
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Design artifacts generated
7. Re-evaluate Constitution Check
   → ✅ Post-Design Constitution Check PASS
8. Plan Phase 2 → Task generation approach described
9. STOP - Ready for /tasks command
```

## Summary

Add a `wc` subcommand to count words in compiled node subtrees using the same mechanics as the `compile` command. The command accepts an optional node ID parameter - if provided, it counts words in that node's subtree; if omitted, it counts words across all root nodes. Word counting uses a nuanced algorithm handling contractions, hyphens, em-dashes, en-dashes, numbers, URLs, and email addresses per US English conventions, producing output compatible with standard `wc -w` behavior.

**Technical Approach**: Reuse existing compile infrastructure (CompileSubtreeUseCase) to get compiled text, then apply a new word-counting domain service that implements US English word-splitting rules. Output is a plain number to stdout for scriptable integration.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: Click 8.1.8+, Typer 0.12.0+ (CLI), PyYAML 6.0.2+ (storage), Pydantic 2.11.4+ (validation)
**Storage**: File system (Markdown + YAML frontmatter)
**Testing**: pytest 8.3.5+ with coverage, mypy 1.15.0+ strict mode, ruff 0.11.8+ linting
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single project (hexagonal architecture)
**Performance Goals**: Handle typical novel-length compilations (100K+ words) in <1 second
**Constraints**: 100% test coverage, 100% mypy compliance, 100% ruff compliance (constitutional requirements)
**Scale/Scope**: Single new CLI command, reuse existing compile infrastructure, add word-counting domain service

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Hexagonal Architecture ✅
- **Status**: PASS - Design follows existing hexagonal pattern
- **Domain**: Word-counting logic in `domain/wordcount/` (pure, no I/O)
- **Ports**: `WordCounterPort` protocol in `ports/wordcount/`
- **Adapters**: CLI command in `cli/wc.py`, reuse existing NodeRepoFs
- **Separation**: CLI → Use Case → Domain Service (clean dependency flow)

### II. Test-First Development ✅
- **Status**: PASS - TDD workflow planned
- **Approach**: Write failing tests first, implement to pass
- **Coverage**: Contract tests, unit tests, integration tests planned
- **Order**: Tests written before implementation in all phases

### III. Plain Text Storage ✅
- **Status**: PASS - No new storage requirements
- **Note**: Reuses existing Markdown + YAML node storage

### IV. Code Quality Standards ✅
- **Status**: PASS - All quality gates planned
- **Mypy**: 100% strict compliance required
- **Ruff**: 100% linting compliance required
- **Tests**: 100% coverage required
- **Enforcement**: python-linter-fixer, python-mypy-error-fixer, python-test-runner agents

### V. CLI-First Interface ✅
- **Status**: PASS - CLI command design specified
- **Command**: `pmk wc [NODE_ID] [--path PATH]`
- **Output**: Plain number to stdout, errors to stderr
- **Protocol**: Follows text in/out pattern

## Project Structure

### Documentation (this feature)
```
specs/009-subtree-word-count/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   └── wordcount_port.py
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (hexagonal architecture)
```
src/prosemark/
├── domain/
│   └── wordcount/
│       ├── __init__.py
│       ├── models.py        # WordCountRequest, WordCountResult
│       └── service.py       # WordCountService (pure business logic)
├── ports/
│   └── wordcount/
│       ├── __init__.py
│       └── counter.py       # WordCounterPort protocol
├── adapters/
│   └── wordcount/
│       ├── __init__.py
│       └── counter_standard.py  # StandardWordCounter implementation
├── app/
│   └── wordcount/
│       ├── __init__.py
│       └── use_cases.py     # WordCountUseCase orchestration
└── cli/
    └── wc.py                # CLI command entry point

tests/
├── contract/
│   └── wordcount/
│       └── test_wordcount_port.py
├── unit/
│   └── wordcount/
│       ├── test_models.py
│       ├── test_service.py
│       └── test_counter.py
└── integration/
    └── wordcount/
        └── test_wc_command.py
```

**Structure Decision**: Single project using existing hexagonal architecture. Word counting follows the same pattern as compilation: domain logic separated from I/O, ports define interfaces, adapters implement word-splitting algorithm, use case orchestrates, CLI provides user interface.

## Phase 0: Outline & Research

### Research Completed

**Decision 1: Word-Splitting Algorithm**
- **Decision**: Use regex-based tokenization compatible with `wc -w` behavior
- **Rationale**: Standard `wc -w` splits on whitespace but needs special handling for US English conventions (contractions, hyphens, URLs)
- **Approach**:
  - Primary split on whitespace (`\s+`)
  - Preserve contractions (don't split on apostrophes within words)
  - Preserve hyphens in compound words
  - Treat URLs and emails as single tokens
  - Count numbers as words
- **Alternatives Considered**:
  - NLTK tokenizer (rejected: too heavyweight, requires ML models)
  - Simple `split()` (rejected: doesn't handle punctuation correctly)

**Decision 2: Reuse Compile Infrastructure**
- **Decision**: Leverage existing CompileSubtreeUseCase to get compiled text
- **Rationale**: Word counting operates on compiled text, same as user workflow (`pmk compile | wc -w`)
- **Benefits**:
  - Consistent subtree traversal logic
  - Reuses node selection (specific ID vs all roots)
  - Respects existing binder ordering
  - No code duplication
- **Approach**: Inject CompileSubtreeUseCase into WordCountUseCase

**Decision 3: Error Handling Strategy**
- **Decision**: Match compile command error handling patterns
- **Rationale**: Consistency with existing CLI commands
- **Behaviors**:
  - Invalid node ID: Exit code 1, error to stderr, `0` to stdout
  - Empty content: Exit code 0, `0` to stdout
  - Missing nodes: Exit code 1, error to stderr, `0` to stdout
- **Reference**: See compile.py:69-78 for error handling pattern

**Decision 4: Domain Model Design**
- **Decision**: Simple request/result pattern like CompileRequest/CompileResult
- **Models**:
  - `WordCountRequest(node_id: NodeId | None, include_empty: bool)`
  - `WordCountResult(count: int, content: str)` - includes content for debugging/testing
- **Rationale**: Follows existing domain conventions, keeps models pure and testable

## Phase 1: Design & Contracts

### Data Model (see data-model.md)

**Core Entities**:

1. **WordCountRequest** (domain/wordcount/models.py)
   - `node_id`: Optional[NodeId] - target node or None for all roots
   - `include_empty`: bool - whether to include empty nodes in compilation
   - Validation: Inherits from CompileRequest pattern

2. **WordCountResult** (domain/wordcount/models.py)
   - `count`: int - total word count
   - `content`: str - compiled content (for testing/debugging)
   - Validation: count >= 0

3. **WordToken** (internal to service)
   - Represents individual words after tokenization
   - Used internally by WordCountService, not exposed in public API

### Contracts (see contracts/)

**Port Interface**: `WordCounterPort` (ports/wordcount/counter.py)

```python
from typing import Protocol

class WordCounterPort(Protocol):
    """Port for word counting implementations."""

    def count_words(self, text: str) -> int:
        """Count words in text using US English conventions.

        Args:
            text: Input text to count words in

        Returns:
            Number of words found

        Rules:
            - Split on whitespace
            - Contractions count as one word (don't, it's)
            - Hyphenated compounds count as one word (well-known)
            - Numbers count as words (123, 3.14)
            - URLs and emails count as one word
            - Em-dashes and en-dashes handled per US English rules
        """
        ...
```

**Contract Tests**: tests/contract/wordcount/test_wordcount_port.py
- Test contractions: "don't" → 1 word
- Test hyphens: "well-known" → 1 word
- Test numbers: "There are 123 items" → 4 words
- Test URLs: "Visit https://example.com" → 2 words
- Test emails: "email user@example.com" → 2 words
- Test empty: "" → 0 words
- Test whitespace normalization: "word  \n\n  word" → 2 words

### Integration Points

1. **Compile Integration**: WordCountUseCase depends on CompileSubtreeUseCase
2. **CLI Integration**: New wc.py command follows compile.py pattern
3. **Repository Integration**: Reuses NodeRepoFs and BinderRepoFs

### Quickstart Validation (see quickstart.md)

User acceptance test workflow:
1. Create test project with nodes
2. Add content with various word types (contractions, numbers, URLs)
3. Run `pmk wc <node-id>` → verify count matches manual count
4. Run `pmk wc` (no args) → verify counts all roots
5. Test error cases (invalid ID, empty content)

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base template
2. Generate from Phase 1 artifacts:
   - Contract tests from contracts/wordcount_port.py [P]
   - Domain models from data-model.md [P]
   - WordCountService unit tests [P]
   - StandardWordCounter adapter tests [P]
   - WordCountUseCase unit tests (depends on service + compile use case)
   - Integration tests from quickstart.md scenarios
   - CLI command implementation
   - CLAUDE.md updates

**Ordering Strategy**:
- **TDD Order**: All tests written before implementation
- **Dependency Order**:
  1. Models (no dependencies) [P]
  2. Port contracts [P]
  3. Domain service (depends on models)
  4. Adapter (depends on port)
  5. Use case (depends on service, compile use case)
  6. CLI command (depends on use case)
  7. Integration tests (depends on all)
- **Parallel Markers**: [P] for independent files (models, contracts, unit tests)

**Estimated Output**: 15-20 tasks in dependency order with TDD approach

**Task Categories**:
- Contract tests: 1 task
- Domain layer: 3 tasks (models test, models impl, service test, service impl)
- Adapter layer: 2 tasks (adapter test, adapter impl)
- Use case layer: 2 tasks (use case test, use case impl)
- CLI layer: 2 tasks (CLI test, CLI impl)
- Integration: 2 tasks (integration test, integration impl)
- Quality gates: 3 tasks (mypy, ruff, coverage verification)
- Documentation: 1 task (CLAUDE.md update)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md with ordered task list)
**Phase 4**: Implementation (execute tasks.md following TDD and constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, verify 100% coverage/mypy/ruff)

## Complexity Tracking

*No constitutional violations - table not needed*

## Progress Tracking

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
- [x] Complexity deviations documented (N/A - no deviations)

---
*Based on Constitution v1.1.0 - See `.specify/memory/constitution.md`*

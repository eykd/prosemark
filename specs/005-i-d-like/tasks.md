# Tasks: Preserve Extraneous Text in Binder Operations

**Input**: Design documents from `/workspace/specs/005-i-d-like/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.13, Textual (TUI), Typer (CLI), Pydantic (data validation)
   → Project structure: hexagonal architecture with ports/adapters
2. Load design documents:
   → data-model.md: PreservedText, StructuralElement, ParserResult, PositionAnchor entities
   → contracts/: EnhancedBinderParserPort interface with 4 test scenarios
   → quickstart.md: 5 integration test scenarios
3. Generate tasks by category:
   → Setup: project structure validation
   → Tests: contract tests [P], integration tests [P]
   → Core: domain models [P], enhanced parser implementation
   → Integration: parser enhancement, validation logic
   → Polish: unit tests [P], round-trip tests
4. Task rules applied:
   → Different files = marked [P] for parallel execution
   → Same file = sequential (no [P])
   → Tests before implementation (TDD approach)
5. Tasks numbered sequentially (T001-T020)
6. Ready for execution following TDD principles
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [x] **T001** Validate existing project structure supports text preservation enhancement
- [x] **T002** [P] Install/verify Python dependencies for text preservation (no new deps required)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

### Contract Tests (Different test files = parallel)
- [x] **T003** [P] Create contract test for `preserve_narrative_text` scenario in `tests/contract/test_enhanced_parser_preserve_narrative.py`
- [x] **T004** [P] Create contract test for `handle_malformed_syntax` scenario in `tests/contract/test_enhanced_parser_malformed.py`
- [x] **T005** [P] Create contract test for `validate_uuid7_links` scenario in `tests/contract/test_enhanced_parser_uuid7.py`
- [x] **T006** [P] Create contract test for `round_trip_integrity` scenario in `tests/contract/test_enhanced_parser_roundtrip.py`

### Domain Model Tests
- [x] **T007** [P] Create test for `PreservedText` value object in `tests/unit/test_preserved_text.py`
- [x] **T008** [P] Create test for `StructuralElement` value object in `tests/unit/test_structural_element.py`
- [x] **T009** [P] Create test for `ParserResult` value object in `tests/unit/test_parser_result.py`
- [x] **T010** [P] Create test for `PositionAnchor` enum in `tests/unit/test_position_anchor.py`

### Integration Tests (from quickstart scenarios)
- [x] **T011** [P] Create integration test for basic text preservation in `tests/integration/test_basic_text_preservation.py`
- [x] **T012** [P] Create integration test for formatting preservation in `tests/integration/test_formatting_preservation.py`
- [x] **T013** [P] Create integration test for end-to-end workflow in `tests/integration/test_end_to_end_workflow.py`

## Phase 3.3: Domain Models

### Value Objects (Different files = parallel)
- [x] **T014** [P] Implement `PositionAnchor` enum in `src/prosemark/domain/position_anchor.py`
- [x] **T015** [P] Implement `PreservedText` value object in `src/prosemark/domain/preserved_text.py`
- [x] **T016** [P] Implement `StructuralElement` value object in `src/prosemark/domain/structural_element.py`
- [x] **T017** [P] Implement `ParserResult` value object in `src/prosemark/domain/parser_result.py`

## Phase 3.4: Core Implementation

### Parser Enhancement (Sequential - same file)
- [ ] **T018** Enhance `MarkdownBinderParser` with text preservation logic in `src/prosemark/adapters/markdown_binder_parser.py` - add `parse_with_preservation()` method
- [ ] **T019** Enhance `MarkdownBinderParser` with text rendering logic in `src/prosemark/adapters/markdown_binder_parser.py` - add `render_with_preservation()` method

### Port Interface
- [ ] **T020** [P] Create enhanced parser port interface in `src/prosemark/ports/enhanced_binder_parser.py`

## Dependencies & Execution Order

### Sequential Dependencies
```
T001 → T002 → All Test Tasks (T003-T013)
Test Tasks → Domain Models (T014-T017)
Domain Models → Core Implementation (T018-T020)
```

### Parallel Execution Groups

**Group 1: Contract Tests (after T002)**
```bash
# Can run simultaneously - different test files
Task(description="Create contract test for preserve_narrative_text", file_path="tests/contract/test_enhanced_parser_preserve_narrative.py")
Task(description="Create contract test for handle_malformed_syntax", file_path="tests/contract/test_enhanced_parser_malformed.py")
Task(description="Create contract test for validate_uuid7_links", file_path="tests/contract/test_enhanced_parser_uuid7.py")
Task(description="Create contract test for round_trip_integrity", file_path="tests/contract/test_enhanced_parser_roundtrip.py")
```

**Group 2: Domain Model Tests (after T002)**
```bash
# Can run simultaneously - different test files
Task(description="Create test for PreservedText value object", file_path="tests/unit/test_preserved_text.py")
Task(description="Create test for StructuralElement value object", file_path="tests/unit/test_structural_element.py")
Task(description="Create test for ParserResult value object", file_path="tests/unit/test_parser_result.py")
Task(description="Create test for PositionAnchor enum", file_path="tests/unit/test_position_anchor.py")
```

**Group 3: Integration Tests (after T002)**
```bash
# Can run simultaneously - different test files
Task(description="Create integration test for basic text preservation", file_path="tests/integration/test_basic_text_preservation.py")
Task(description="Create integration test for formatting preservation", file_path="tests/integration/test_formatting_preservation.py")
Task(description="Create integration test for end-to-end workflow", file_path="tests/integration/test_end_to_end_workflow.py")
```

**Group 4: Domain Models (after all tests)**
```bash
# Can run simultaneously - different implementation files
Task(description="Implement PositionAnchor enum", file_path="src/prosemark/domain/position_anchor.py")
Task(description="Implement PreservedText value object", file_path="src/prosemark/domain/preserved_text.py")
Task(description="Implement StructuralElement value object", file_path="src/prosemark/domain/structural_element.py")
Task(description="Implement ParserResult value object", file_path="src/prosemark/domain/parser_result.py")
```

## Validation Checklist
- [x] All contract scenarios have tests (4/4)
- [x] All entities have model implementations (4/4)
- [x] All integration scenarios have tests (3/3)
- [x] Parser enhancement split into logical steps
- [x] TDD approach maintained (tests before implementation)
- [x] Parallel opportunities identified ([P] marked)
- [x] File paths specified for all tasks
- [x] Dependencies clearly documented

## Quality Gates
Each task must pass before proceeding:
- **Linting**: `uv run ruff check src/ tests/`
- **Type checking**: `uv run mypy src/`
- **Tests**: `pytest tests/ --cov=src --cov-report=term:skip-covered`
- **Coverage**: 100% required for all new code

**Total Tasks**: 20
**Parallel Groups**: 4 groups with 13 parallel tasks total
**Estimated Completion**: Following TDD principles with immediate feedback

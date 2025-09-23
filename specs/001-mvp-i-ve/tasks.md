# Tasks: Prosemark CLI Writing Project Manager MVP

**Input**: Design documents from `/specs/001-mvp-i-ve/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.9+, Typer, PyYAML, pytest
   → Structure: Single project with src/prosemark hexagonal architecture
2. Load design documents:
   → data-model.md: Extract 6 entities → model tasks
   → contracts/: CLI commands & domain interfaces → contract test tasks
   → quickstart.md: Extract 8 user scenarios → integration tests
3. Generate tasks by category:
   → Setup: Python project, dependencies, linting
   → Tests: CLI contract tests, domain contract tests, integration tests
   → Core: domain models, adapters, use cases, CLI commands
   → Integration: file system, editor, console integration
   → Polish: unit tests, performance, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → TDD order: Tests before implementation
   → Hexagonal architecture: Domain → Adapters → CLI
5. Number tasks sequentially (T001-T040)
6. Generate dependency graph for execution order
7. SUCCESS: 40 tasks ready for MVP implementation
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Paths assume src/prosemark/ structure per plan.md

## Phase 3.1: Setup & Dependencies

- [X] **T001** Initialize Python project structure with src/prosemark/, tests/, pyproject.toml
- [X] **T002** Configure dependencies: Typer, PyYAML, pytest, ruff, mypy in pyproject.toml
- [X] **T003** [P] Configure ruff formatting and linting in pyproject.toml
- [X] **T004** [P] Configure mypy type checking in pyproject.toml
- [X] **T005** [P] Set up pytest configuration in pyproject.toml

## Phase 3.2: Domain Models & Core Tests (TDD)
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Domain Entity Tests
- [X] **T006** [P] Contract test for NodeId value object in tests/contract/test_node_id.py
- [X] **T007** [P] Contract test for Binder entity in tests/contract/test_binder.py
- [X] **T008** [P] Contract test for BinderItem entity in tests/contract/test_binder_item.py
- [X] **T009** [P] Contract test for Node entity in tests/contract/test_node.py
- [X] **T010** [P] Contract test for FreeformContent entity in tests/contract/test_freeform_content.py

### Port Interface Tests
- [X] **T011** [P] Contract test for BinderRepo protocol in tests/contract/test_binder_repo.py
- [X] **T012** [P] Contract test for NodeRepo protocol in tests/contract/test_node_repo.py
- [X] **T013** [P] Contract test for DailyRepo protocol in tests/contract/test_daily_repo.py
- [X] **T014** [P] Contract test for IdGenerator protocol in tests/contract/test_id_generator.py
- [X] **T015** [P] Contract test for Clock protocol in tests/contract/test_clock.py
- [X] **T016** [P] Contract test for EditorPort protocol in tests/contract/test_editor_port.py
- [X] **T017** [P] Contract test for ConsolePort protocol in tests/contract/test_console_port.py
- [X] **T018** [P] Contract test for Logger protocol in tests/contract/test_logger.py

### CLI Command Tests
- [X] **T019** [P] Contract test for `pmk init` command in tests/contract/test_cli_init.py
- [X] **T020** [P] Contract test for `pmk add` command in tests/contract/test_cli_add.py
- [X] **T021** [P] Contract test for `pmk edit` command in tests/contract/test_cli_edit.py
- [X] **T022** [P] Contract test for `pmk structure` command in tests/contract/test_cli_structure.py
- [X] **T023** [P] Contract test for `pmk write` command in tests/contract/test_cli_write.py
- [X] **T024** [P] Contract test for `pmk materialize` command in tests/contract/test_cli_materialize.py
- [X] **T025** [P] Contract test for `pmk move` command in tests/contract/test_cli_move.py
- [X] **T026** [P] Contract test for `pmk remove` command in tests/contract/test_cli_remove.py
- [X] **T027** [P] Contract test for `pmk audit` command in tests/contract/test_cli_audit.py

## Phase 3.3: Core Domain Implementation (ONLY after tests fail)

### Domain Models
- [X] **T028** [P] NodeId value object in src/prosemark/domain/node_id.py
- [X] **T029** [P] Binder entity in src/prosemark/domain/binder.py
- [X] **T030** [P] BinderItem entity in src/prosemark/domain/binder_item.py
- [X] **T031** [P] Node entity in src/prosemark/domain/node.py
- [X] **T032** [P] FreeformContent entity in src/prosemark/domain/freeform_content.py
- [X] **T033** [P] Domain exceptions in src/prosemark/domain/exceptions.py

### Port Interfaces
- [X] **T034** [P] All port protocols in src/prosemark/ports/

## Phase 3.4: Adapter Implementation

### File System Adapters
- [x] **T035** [P] BinderRepoFs adapter in src/prosemark/adapters/binder_repo_fs.py
- [x] **T036** [P] NodeRepoFs adapter in src/prosemark/adapters/node_repo_fs.py
- [x] **T037** [P] DailyRepoFs adapter in src/prosemark/adapters/daily_repo_fs.py

### System Adapters
- [x] **T038** [P] EditorLauncherSystem in src/prosemark/adapters/editor_launcher_system.py
- [x] **T039** [P] FrontmatterCodec in src/prosemark/adapters/frontmatter_codec.py
- [x] **T040** [P] MarkdownBinderParser in src/prosemark/adapters/markdown_binder_parser.py
- [x] **T041** [P] IdGeneratorUuid7 in src/prosemark/adapters/id_generator_uuid7.py
- [x] **T042** [P] ClockSystem in src/prosemark/adapters/clock_system.py
- [x] **T043** [P] ConsolePretty in src/prosemark/adapters/console_pretty.py
- [x] **T044** [P] LoggerStdout in src/prosemark/adapters/logger_stdout.py

## Phase 3.5: Use Cases & CLI

### Use Case Implementation
- [X] **T045** InitProject use case in src/prosemark/app/init_project.py
- [X] **T046** AddNode use case in src/prosemark/app/add_node.py
- [X] **T047** MaterializeNode use case in src/prosemark/app/materialize_node.py
- [X] **T048** MoveNode use case in src/prosemark/app/move_node.py
- [X] **T049** RemoveNode use case in src/prosemark/app/remove_node.py
- [X] **T050** AuditProject use case in src/prosemark/app/audit_project.py

### CLI Commands
- [X] **T051** CLI main entry point in src/prosemark/cli/main.py
- [X] **T052** `pmk init` command in src/prosemark/cli/init.py
- [X] **T053** `pmk add` command in src/prosemark/cli/add.py
- [X] **T054** `pmk edit` command in src/prosemark/cli/edit.py
- [X] **T055** `pmk structure` command in src/prosemark/cli/structure.py
- [X] **T056** `pmk write` command in src/prosemark/cli/write.py
- [X] **T057** `pmk materialize` command in src/prosemark/cli/materialize.py
- [X] **T058** `pmk move` command in src/prosemark/cli/move.py
- [X] **T059** `pmk remove` command in src/prosemark/cli/remove.py
- [X] **T060** `pmk audit` command in src/prosemark/cli/audit.py

## Phase 3.6: Integration Tests
**Based on quickstart.md scenarios**

- [X] **T061** [P] Integration test: Complete project lifecycle in tests/integration/test_project_lifecycle.py
- [X] **T062** [P] Integration test: Node content editing workflow in tests/integration/test_editing_workflow.py
- [X] **T063** [P] Integration test: Binder structure management in tests/integration/test_structure_management.py
- [X] **T064** [P] Integration test: Placeholder materialization in tests/integration/test_placeholder_workflow.py
- [X] **T065** [P] Integration test: Freeform writing in tests/integration/test_freeform_writing.py
- [X] **T066** [P] Integration test: Project audit and integrity in tests/integration/test_audit_integrity.py
- [X] **T067** [P] Integration test: File system safety in tests/integration/test_file_safety.py
- [X] **T068** [P] Integration test: Cross-platform compatibility in tests/integration/test_cross_platform.py

## Phase 3.7: Polish & Validation

### Unit Tests
- [X] **T069** [P] Unit tests for NodeId validation in tests/unit/test_node_id_validation.py
- [X] **T070** [P] Unit tests for YAML frontmatter parsing in tests/unit/test_frontmatter_parsing.py
- [X] **T071** [P] Unit tests for markdown parsing in tests/unit/test_markdown_parsing.py
- [X] **T072** [P] Unit tests for UUIDv7 generation in tests/unit/test_uuid7_generation.py

### Performance & Quality
- [X] **T073** Performance tests: Large binder parsing (<1s) in tests/performance/test_large_binder.py
- [X] **T074** Performance tests: File I/O operations (<100ms) in tests/performance/test_file_operations.py
- [X] **T075** [P] Documentation: Update README.md with installation and usage
- [X] **T076** [P] Documentation: Create API documentation from docstrings
- [X] **T077** Code quality: Remove duplication and optimize imports
- [X] **T078** Execute quickstart.md scenarios as final validation

## Dependencies

### Phase Dependencies
- Setup (T001-T005) must complete before all other phases
- All test tasks (T006-T027) must complete and FAIL before implementation (T028+)
- Domain models (T028-T034) must complete before adapters (T035-T044)
- Adapters must complete before use cases (T045-T050) and CLI (T051-T060)
- Core implementation must complete before integration tests (T061-T068)
- Everything must complete before polish (T069-T078)

### Specific Dependencies
- T034 (ports) blocks T035-T044 (adapters)
- T035-T044 (adapters) block T045-T050 (use cases)
- T045-T050 (use cases) block T051-T060 (CLI)
- T028-T033 (domain) required by all subsequent tasks

## Parallel Execution Examples

### Contract Tests (can run simultaneously)
```bash
# Launch T006-T027 together (22 parallel contract tests):
Task: "Contract test for NodeId value object in tests/contract/test_node_id.py"
Task: "Contract test for Binder entity in tests/contract/test_binder.py"
Task: "Contract test for BinderItem entity in tests/contract/test_binder_item.py"
# ... all contract tests can run in parallel
```

### Domain Models (can run simultaneously after tests fail)
```bash
# Launch T028-T033 together (6 parallel domain models):
Task: "NodeId value object in src/prosemark/domain/node_id.py"
Task: "Binder entity in src/prosemark/domain/binder.py"
Task: "BinderItem entity in src/prosemark/domain/binder_item.py"
# ... all domain models can run in parallel
```

### File System Adapters (can run simultaneously)
```bash
# Launch T035-T037 together (3 parallel FS adapters):
Task: "BinderRepoFs adapter in src/prosemark/adapters/fs_binder_repo.py"
Task: "NodeRepoFs adapter in src/prosemark/adapters/fs_node_repo.py"
Task: "DailyRepoFs adapter in src/prosemark/adapters/fs_daily_repo.py"
```

## Notes
- [P] tasks target different files with no dependencies
- All tests must fail before implementing corresponding functionality (TDD)
- Each task includes specific file path for clear execution
- Hexagonal architecture enforced: Domain → Ports → Adapters → Use Cases → CLI
- Constitutional compliance: TDD, type annotations, docstrings, 100% coverage

## Validation Checklist
*GATE: Checked before task execution*

- [x] All contracts have corresponding tests (T006-T027)
- [x] All entities have model tasks (T028-T033)
- [x] All tests come before implementation (Phase 3.2 before 3.3+)
- [x] Parallel tasks truly independent ([P] tasks target different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD order enforced (tests first, then implementation)
- [x] Hexagonal architecture dependencies respected

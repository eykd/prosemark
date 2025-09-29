# Tasks: Node Templates

**Input**: Design documents from `/workspace/specs/007-node-templates-i/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 3.1: Setup
- [x] T001 Create template feature directory structure per implementation plan
- [x] T002 Create __init__.py files for all new Python packages
- [x] T003 [P] Configure mypy and ruff for new template modules

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [x] T004 [P] Contract test for TemplateRepositoryPort in tests/contract/templates/test_template_repository_contract.py
- [x] T005 [P] Contract test for TemplateValidatorPort in tests/contract/templates/test_template_validator_contract.py
- [x] T006 [P] Contract test for UserPrompterPort in tests/contract/templates/test_user_prompter_contract.py

### Integration Tests
- [x] T007 [P] Integration test for listing templates in tests/integration/templates/test_list_templates.py
- [x] T008 [P] Integration test for creating node from simple template in tests/integration/templates/test_simple_template.py
- [x] T009 [P] Integration test for creating nodes from directory template in tests/integration/templates/test_directory_template.py
- [x] T010 [P] Integration test for template validation errors in tests/integration/templates/test_template_errors.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Domain Entities
- [ ] T011 [P] Template entity in src/prosemark/templates/domain/entities/template.py
- [ ] T012 [P] Placeholder entity in src/prosemark/templates/domain/entities/placeholder.py
- [ ] T013 [P] TemplateDirectory entity in src/prosemark/templates/domain/entities/template_directory.py
- [ ] T014 [P] PlaceholderValue entity in src/prosemark/templates/domain/entities/placeholder_value.py

### Value Objects
- [ ] T015 [P] TemplatePath value object in src/prosemark/templates/domain/values/template_path.py
- [ ] T016 [P] PlaceholderPattern value object in src/prosemark/templates/domain/values/placeholder_pattern.py
- [ ] T017 [P] DirectoryPath value object in src/prosemark/templates/domain/values/directory_path.py

### Domain Exceptions
- [ ] T018 [P] Template exceptions in src/prosemark/templates/domain/exceptions/template_exceptions.py

### Port Interfaces
- [ ] T019 [P] TemplateRepositoryPort interface in src/prosemark/templates/ports/template_repository_port.py
- [ ] T020 [P] TemplateValidatorPort interface in src/prosemark/templates/ports/template_validator_port.py
- [ ] T021 [P] UserPrompterPort interface in src/prosemark/templates/ports/user_prompter_port.py

### Domain Services
- [ ] T022 Template service implementation in src/prosemark/templates/domain/services/template_service.py
- [ ] T023 Placeholder service implementation in src/prosemark/templates/domain/services/placeholder_service.py

### Adapters
- [ ] T024 File template repository adapter in src/prosemark/templates/adapters/file_template_repository.py
- [ ] T025 Prosemark template validator adapter in src/prosemark/templates/adapters/prosemark_template_validator.py
- [ ] T026 CLI user prompter adapter in src/prosemark/templates/adapters/cli_user_prompter.py

### Use Cases
- [ ] T027 Create from template use case in src/prosemark/app/use_cases/create_from_template.py
- [ ] T028 List templates use case in src/prosemark/app/use_cases/list_templates.py

## Phase 3.4: Integration

### CLI Integration
- [ ] T029 Extend add command with --template parameter in src/prosemark/cli/commands/add.py
- [ ] T030 Add --list-templates flag to add command in src/prosemark/cli/commands/add.py

### Dependency Injection
- [ ] T031 Wire template dependencies into DI container
- [ ] T032 Configure template adapters in application startup

## Phase 3.5: Polish

### Unit Tests
- [ ] T033 [P] Unit tests for Template entity in tests/unit/prosemark/templates/domain/entities/test_template.py
- [ ] T034 [P] Unit tests for Placeholder entity in tests/unit/prosemark/templates/domain/entities/test_placeholder.py
- [ ] T035 [P] Unit tests for template service in tests/unit/prosemark/templates/domain/services/test_template_service.py
- [ ] T036 [P] Unit tests for placeholder service in tests/unit/prosemark/templates/domain/services/test_placeholder_service.py

### Adapter Tests
- [ ] T037 [P] Tests for file template repository in tests/unit/prosemark/templates/adapters/test_file_template_repository.py
- [ ] T038 [P] Tests for prosemark validator in tests/unit/prosemark/templates/adapters/test_prosemark_template_validator.py
- [ ] T039 [P] Tests for CLI prompter in tests/unit/prosemark/templates/adapters/test_cli_user_prompter.py

### Quality Validation
- [ ] T040 Run mypy type checking on all template modules
- [ ] T041 Run ruff linting on all template modules
- [ ] T042 Achieve 100% test coverage for template feature
- [ ] T043 Execute quickstart.md scenarios manually
- [ ] T044 [P] Update CLAUDE.md with template feature documentation

## Dependencies
- Setup (T001-T003) before all other tasks
- Contract and integration tests (T004-T010) before implementation (T011-T028)
- Domain entities (T011-T018) before services (T022-T023)
- Port interfaces (T019-T021) before adapters (T024-T026)
- Services and adapters before use cases (T027-T028)
- Use cases before CLI integration (T029-T030)
- All implementation before unit tests (T033-T039)
- All tests passing before quality validation (T040-T044)

## Parallel Execution Examples

### Phase 3.2: All contract and integration tests together
```bash
# Launch T004-T010 in parallel (all different files):
Task agent: "Contract test for TemplateRepositoryPort in tests/contract/templates/test_template_repository_contract.py"
Task agent: "Contract test for TemplateValidatorPort in tests/contract/templates/test_template_validator_contract.py"
Task agent: "Contract test for UserPrompterPort in tests/contract/templates/test_user_prompter_contract.py"
Task agent: "Integration test for listing templates in tests/integration/templates/test_list_templates.py"
Task agent: "Integration test for creating node from simple template in tests/integration/templates/test_simple_template.py"
Task agent: "Integration test for creating nodes from directory template in tests/integration/templates/test_directory_template.py"
Task agent: "Integration test for template validation errors in tests/integration/templates/test_template_errors.py"
```

### Phase 3.3: All domain entities and value objects together
```bash
# Launch T011-T018 in parallel (all different files):
Task agent: "Create Template entity in src/prosemark/templates/domain/entities/template.py"
Task agent: "Create Placeholder entity in src/prosemark/templates/domain/entities/placeholder.py"
Task agent: "Create TemplateDirectory entity in src/prosemark/templates/domain/entities/template_directory.py"
Task agent: "Create PlaceholderValue entity in src/prosemark/templates/domain/entities/placeholder_value.py"
Task agent: "Create TemplatePath value object in src/prosemark/templates/domain/values/template_path.py"
Task agent: "Create PlaceholderPattern value object in src/prosemark/templates/domain/values/placeholder_pattern.py"
Task agent: "Create DirectoryPath value object in src/prosemark/templates/domain/values/directory_path.py"
Task agent: "Create template exceptions in src/prosemark/templates/domain/exceptions/template_exceptions.py"
```

### Phase 3.3: All port interfaces together
```bash
# Launch T019-T021 in parallel (all different files):
Task agent: "Create TemplateRepositoryPort interface in src/prosemark/templates/ports/template_repository_port.py"
Task agent: "Create TemplateValidatorPort interface in src/prosemark/templates/ports/template_validator_port.py"
Task agent: "Create UserPrompterPort interface in src/prosemark/templates/ports/user_prompter_port.py"
```

### Phase 3.5: All unit tests together
```bash
# Launch T033-T039 in parallel (all different files):
Task agent: "Unit tests for Template entity in tests/unit/prosemark/templates/domain/entities/test_template.py"
Task agent: "Unit tests for Placeholder entity in tests/unit/prosemark/templates/domain/entities/test_placeholder.py"
Task agent: "Unit tests for template service in tests/unit/prosemark/templates/domain/services/test_template_service.py"
Task agent: "Unit tests for placeholder service in tests/unit/prosemark/templates/domain/services/test_placeholder_service.py"
Task agent: "Tests for file template repository in tests/unit/prosemark/templates/adapters/test_file_template_repository.py"
Task agent: "Tests for prosemark validator in tests/unit/prosemark/templates/adapters/test_prosemark_template_validator.py"
Task agent: "Tests for CLI prompter in tests/unit/prosemark/templates/adapters/test_cli_user_prompter.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing (TDD requirement)
- Commit after each task completion
- Run quality checks (mypy, ruff, coverage) after each phase
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each port interface → implementation task

2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks

3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Adapters → Use Cases → Integration → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T004-T006)
- [x] All entities have model tasks (T011-T014)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Quality validation includes 100% coverage requirement (T042)
- [x] Constitutional requirements enforced (TDD, mypy, ruff)

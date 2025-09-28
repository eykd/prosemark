# Research: Structure Command Subtree Display

## Investigation Summary

### Current Implementation Status

**Decision**: Feature partially implemented
**Finding**: The subtree display functionality is already implemented in the domain and application layers, with partial CLI integration.

The investigation revealed:
1. `ShowStructure` use case already accepts optional `node_id: NodeId | None` parameter
2. Full subtree filtering logic is implemented in the use case layer
3. Click-based CLI (`src/prosemark/cli/structure.py`) has the node_id argument defined
4. Main Typer CLI (`src/prosemark/cli/main.py`) lacks the node_id argument
5. Both JSON and tree output formats are supported

### Technology Stack

**Decision**: Python 3.13 with existing Prosemark architecture
**Rationale**: Project uses Python 3.13 as specified in pyproject.toml
**Dependencies**:
- Typer for CLI framework (main entry point)
- Click for legacy CLI commands
- Pydantic for data validation
- UUID-extension for UUID v7 support

### Architecture Pattern

**Decision**: Hexagonal architecture (already implemented)
**Rationale**: Project follows strict hexagonal architecture per constitution
**Structure**:
- Domain layer: Pure business logic (`src/prosemark/domain/`)
- Application layer: Use cases (`src/prosemark/app/use_cases.py`)
- Ports: Interface definitions (`src/prosemark/ports/`)
- Adapters: External integrations (`src/prosemark/adapters/`)
- CLI: Command interfaces (`src/prosemark/cli/`)

### Node ID Format

**Decision**: UUID format using NodeId value object
**Rationale**: Project uses UUIDv7 for all node identifiers as per constitution
**Implementation**: `NodeId` class in `src/prosemark/domain/models.py` handles validation

### Error Handling

**Decision**: Use existing error hierarchy
**Rationale**: Project has established exception patterns
**Exceptions**:
- `NodeNotFoundError`: When specified node doesn't exist
- `NodeIdentityError`: When node ID format is invalid
- `FileSystemError`: For I/O operations

### Testing Strategy

**Decision**: Follow TDD with 100% coverage requirement
**Rationale**: Constitution mandates test-first development
**Structure**:
- Unit tests: `tests/unit/`
- Contract tests: `tests/contract/`
- Integration tests: `tests/integration/`

### Implementation Gap Analysis

**What exists**:
- Complete domain logic for subtree filtering
- ShowStructure use case with node_id parameter support
- Error handling for invalid/missing nodes
- Tree formatting with ASCII art
- JSON output format support

**What's missing**:
- NODE_ID argument in main Typer CLI command
- Tests for the CLI with node_id parameter
- Integration tests for subtree display

### Quality Requirements

**Decision**: 100% compliance with all quality gates
**Tools**:
- mypy for type checking (100% required)
- ruff for linting (100% required)
- pytest for testing (100% coverage required)
**Enforcement**: No code can be committed without passing all quality checks

### Performance Considerations

**Decision**: Best-effort performance (no hard constraints)
**Rationale**: Clarification confirmed no specific performance requirements
**Approach**: Existing tree traversal algorithm is sufficient

## Alternatives Considered

1. **Rewrite entire feature**: Rejected - Most functionality already exists
2. **Create new command**: Rejected - Better to extend existing command
3. **Path-based navigation**: Rejected - UUID-based system already established

## Implementation Strategy

The implementation only requires:
1. Add node_id argument to Typer CLI command in main.py
2. Parse and validate the node_id if provided
3. Pass node_id to existing ShowStructure.execute()
4. Add comprehensive tests for the CLI integration

## Risk Assessment

**Low Risk**:
- Feature mostly implemented
- Clear integration point
- Existing error handling covers edge cases
- No breaking changes to existing functionality

## Conclusion

This feature requires minimal implementation work since the core functionality already exists. The main task is to complete the Typer CLI integration by adding the missing node_id argument and ensuring proper test coverage.

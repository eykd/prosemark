# Research: Materialize All Command Option

## Overview
Research findings for implementing the `--all` option for PMK's `materialize` command to enable bulk placeholder materialization.

## Technology Stack Decisions

### CLI Framework
**Decision**: Continue using Typer framework
**Rationale**: PMK already uses Typer (not Click) for CLI implementation in `/workspace/src/prosemark/cli/main.py`
**Alternatives considered**: Click framework - rejected because project already standardized on Typer

### Integration Approach
**Decision**: Extend existing `materialize` command in main.py:310-352
**Rationale**: Leverages existing dependency injection, error handling, and CLI patterns
**Alternatives considered**: Separate command - rejected because functionality is closely related

## Current Implementation Analysis

### Existing Materialize Command Structure
- **Location**: `/workspace/src/prosemark/cli/main.py` lines 310-352
- **Framework**: Typer with typed annotations and dependency injection
- **Current options**: `title` (argument), `--parent` (not implemented), `--path`
- **Pattern**: CLI → Use Case → Domain Services → Repositories

### Placeholder Discovery Mechanism
- **Definition**: BinderItem with `node_id = None` but has `display_title`
- **Storage**: `_binder.md` in managed blocks as `- [Title]()` (empty links)
- **Detection**: `BinderItem.is_placeholder()` method returns `True` for `node_id is None`
- **Audit integration**: `AuditBinder` already identifies all placeholders

### Materialization Process
1. Load binder from `BinderRepoFs`
2. Find placeholder by display title (exact match, depth-first)
3. Generate NodeId using `IdGeneratorUuid7`
4. Create node files (`{id}.md` and `{id}.notes.md`)
5. Update placeholder with `node_id`
6. Save updated binder structure

## Implementation Patterns

### Error Handling
- **Specific exceptions**: `PlaceholderNotFoundError`, `AlreadyMaterializedError`
- **CLI pattern**: `typer.echo()` to stderr + `typer.Exit(1)`
- **Graceful failures**: Individual placeholder failures shouldn't stop batch process

### Success Reporting
- **Format**: Consistent success messages with specific details
- **Progress**: Simple `typer.echo()` for status updates during batch operations
- **Results**: Summary of successful vs failed materializations

### Testing Infrastructure
- **Contract tests**: CLI command behavior verification
- **Integration tests**: End-to-end placeholder workflows
- **Test runner**: Uses `typer.testing.CliRunner`

## Architecture Decisions

### Use Case Layer
**Decision**: Extend existing `MaterializeNode` use case with batch capability
**Rationale**: Reuses existing domain logic, maintains transaction boundaries
**Alternatives considered**: New `MaterializeAllNodes` use case - may be needed for complex batch logic

### Placeholder Discovery
**Decision**: Leverage existing `AuditBinder` logic for placeholder identification
**Rationale**: Already traverses binder tree and identifies placeholders accurately
**Alternatives considered**: Separate discovery logic - would duplicate existing functionality

### Progress Reporting
**Decision**: Simple text-based progress updates using `typer.echo()`
**Rationale**: Consistent with existing CLI patterns, sufficient for expected use cases
**Alternatives considered**: Progress bars - unnecessary complexity for typical usage

### Error Recovery
**Decision**: Continue processing remaining placeholders on individual failures
**Rationale**: Maximizes user productivity, provides complete failure report
**Alternatives considered**: Stop on first failure - less user-friendly for batch operations

## Dependencies and Integration Points

### Existing Components to Leverage
- **BinderRepoFs**: Binder persistence and loading
- **MaterializeNode**: Core materialization logic
- **AuditBinder**: Placeholder discovery patterns
- **IdGeneratorUuid7**: Node ID generation
- **NodeRepo**: File creation and management

### New Components Needed
- **Batch progress tracking**: Simple counter and status reporting
- **Partial failure handling**: Error collection and reporting
- **Enhanced CLI validation**: `--all` flag validation and user feedback

## Performance Considerations

### Expected Scale
- **Typical usage**: 5-50 placeholders per binder
- **Large projects**: Up to 1000+ placeholders
- **Response time**: Acceptable if under 30 seconds for 100 placeholders

### Optimization Strategies
- **Sequential processing**: Sufficient for expected volumes
- **Transaction boundaries**: One save operation per materialization (existing pattern)
- **Memory efficiency**: Process placeholders iteratively, not bulk-loaded

## Quality Assurance Requirements

### Test Coverage Requirements
- **Contract tests**: CLI option parsing and validation
- **Integration tests**: End-to-end batch materialization workflows
- **Unit tests**: Batch logic, error handling, progress reporting
- **Edge cases**: Empty binders, already materialized items, filesystem errors

### Compliance Standards
- **Type checking**: 100% mypy compliance with strict configuration
- **Linting**: 100% ruff compliance
- **Testing**: 100% pytest pass rate
- **Documentation**: Google Style docstrings for all new public APIs

## Next Phase Dependencies

### Phase 1 Requirements
- **Data model**: Batch operation result structures
- **API contracts**: Enhanced use case interfaces
- **Test scaffolding**: Failing tests for TDD approach
- **Quickstart validation**: End-to-end success scenarios

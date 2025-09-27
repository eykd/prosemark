# Research & Technical Decisions

## Phase 0: Research Findings

### 1. Existing Node/Binder Architecture
**Decision**: Reuse existing domain models and ports
**Rationale**: The codebase already has well-defined Node and Binder entities in `domain/models.py` and `domain/entities.py`, with repository ports in `ports/node_repo.py` and `ports/binder_repo.py`
**Alternatives considered**: Creating new models specifically for compilation - rejected to maintain consistency

### 2. Tree Traversal Implementation
**Decision**: Implement depth-first pre-order traversal using recursive algorithm
**Rationale**: Natural fit for hierarchical node structures, simple to implement and understand
**Alternatives considered**:
- Iterative with stack - more complex for no performance benefit at expected scale
- Breadth-first - explicitly rejected by requirements

### 3. Memory Management for Large Subtrees
**Decision**: Use generator-based streaming for content aggregation
**Rationale**: Prevents memory issues with large subtrees while maintaining simple API
**Alternatives considered**:
- Load all content into memory - simple but risky for large trees
- Write to temporary file - unnecessary I/O overhead for most cases

### 4. Integration with CLI Framework
**Decision**: Add new Typer command in existing CLI structure
**Rationale**: Follows established pattern in `cli/commands/`, maintains consistency
**Alternatives considered**: Standalone script - would break existing CLI architecture

### 5. Port/Adapter Design
**Decision**: Create CompileServicePort with implementation delegating to existing NodeRepo
**Rationale**: Follows hexagonal architecture, allows testing without file system
**Alternatives considered**: Direct file system access - violates architecture principles

### 6. Error Handling Strategy
**Decision**: Use existing exception patterns from domain layer
**Rationale**: Consistent error handling across the application
**Alternatives considered**: New exception hierarchy - unnecessary complexity

### 7. Testing Approach
**Decision**: Three-layer testing (unit, contract, integration) following TDD
**Rationale**: Constitutional requirement, ensures quality and reliability
**Alternatives considered**: None - constitution mandates this approach

### 8. Content Formatting
**Decision**: Plain text with \n\n separation, preserve internal formatting
**Rationale**: Specified in requirements after clarification
**Alternatives considered**: None - requirement is explicit

## Technical Stack Confirmation
- **Python 3.13**: Already in use
- **Typer**: Existing CLI framework
- **pytest**: Test framework with 100% coverage requirement
- **mypy**: Type checking (strict mode)
- **ruff**: Linting with all rules enabled

## Integration Points
1. **NodeRepo Port**: Access node content and relationships
2. **BinderRepo Port**: Navigate binder structure
3. **CLI Registry**: Register new compile command
4. **Domain Models**: Use existing Node, Binder entities

## Performance Considerations
- Target: Compile 1000 nodes in <1 second
- Strategy: Efficient tree traversal, minimal I/O operations
- Monitoring: Add timing metrics in debug mode

## No Remaining Clarifications
All technical decisions have been made based on:
- Feature specification with clarifications
- Existing codebase patterns
- Constitutional requirements
- Performance targets

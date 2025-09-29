# Research: Node Templates

## Template Pattern Research

### Decision: Template Entity Design
**Chosen**: Pydantic-based Template entity with strict validation
**Rationale**: Ensures type safety and validation consistency with existing prosemark codebase
**Alternatives considered**:
- Plain dataclasses: Less validation support
- Custom validation classes: Reinventing Pydantic features

### Decision: Placeholder Syntax
**Chosen**: `{{variable_name}}` syntax for placeholders
**Rationale**:
- Common templating convention (Mustache, Handlebars)
- Easy to parse with regex
- Visually distinct from Markdown syntax
**Alternatives considered**:
- `<<variable>>`: Less common, could conflict with HTML
- `$variable`: Could conflict with shell syntax in code blocks
- `{variable}`: Too similar to existing Markdown/YAML syntax

### Decision: Template Discovery Strategy
**Chosen**: Recursive directory scanning with .md extension filtering
**Rationale**:
- Supports nested template organization
- Consistent with prosemark file patterns
- Efficient for small to medium template collections
**Alternatives considered**:
- Index file approach: Adds complexity, maintenance overhead
- Database/cache: Overkill for local file operations

### Decision: Template Validation Approach
**Chosen**: Two-phase validation (structure + content)
**Rationale**:
- Structure validation: YAML frontmatter parsing, required fields
- Content validation: Prosemark format compliance, placeholder syntax
- Allows clear error messages for different failure types
**Alternatives considered**:
- Single-phase validation: Less precise error reporting
- Runtime validation only: Poor user experience for invalid templates

## CLI Integration Research

### Decision: Command Extension Strategy
**Chosen**: Extend existing `pmk add` command with optional parameters
**Rationale**:
- Maintains consistent CLI interface
- Natural workflow extension (add regular node vs add from template)
- Follows established CLI patterns in prosemark
**Alternatives considered**:
- Separate `pmk template` command: Creates workflow fragmentation
- New `pmk create` command: Duplicates existing add functionality

### Decision: User Interaction Pattern
**Chosen**: Sequential prompting for placeholders using prompt-toolkit
**Rationale**:
- Consistent with existing CLI interaction patterns
- prompt-toolkit already in dependencies
- Supports rich input features (validation, autocomplete)
**Alternatives considered**:
- Batch input (all at once): Poor UX for many placeholders
- Configuration file: Adds complexity for simple use case

## File System Integration Research

### Decision: Template Repository Pattern
**Chosen**: Port-based repository with file system adapter
**Rationale**:
- Follows hexagonal architecture principles
- Enables testing with fake implementations
- Future extensibility (remote templates, different storage)
**Alternatives considered**:
- Direct file system access: Violates architecture boundaries
- Generic repository: Over-engineering for specific domain

### Decision: Template Directory Structure Support
**Chosen**: Preserve relative paths in template directories
**Rationale**:
- Maintains template organization intent
- Supports complex template hierarchies
- Enables template relationships through relative references
**Alternatives considered**:
- Flatten directory structure: Loses organizational information
- Require flat structure: Limits template complexity

## Error Handling Research

### Decision: Fail-Fast Error Strategy
**Chosen**: Immediate halt with detailed error messages
**Rationale**:
- Prevents partial template instantiation
- Clear feedback for template authors
- Consistent with clarification requirement
**Alternatives considered**:
- Best-effort processing: Could leave system in inconsistent state
- Warning-only approach: Unclear user expectations

### Decision: Error Message Design
**Chosen**: Structured error messages with context and suggestions
**Rationale**:
- Template path and line number for location
- Specific issue description
- Actionable suggestions for fixes
**Alternatives considered**:
- Simple error messages: Poor developer experience
- Verbose stack traces: Overwhelming for end users

## Performance Considerations

### Decision: Template Caching Strategy
**Chosen**: No caching for initial implementation
**Rationale**:
- Local file operations are sufficiently fast
- Simplifies implementation and testing
- Cache invalidation complexity not justified
**Alternatives considered**:
- In-memory template cache: Premature optimization
- File system watcher: Added complexity for minimal benefit

### Decision: Validation Performance
**Chosen**: Validation on demand, not at startup
**Rationale**:
- Faster CLI startup time
- Only validates templates being used
- Allows iterative template development
**Alternatives considered**:
- Validate all templates at startup: Slow startup, unnecessary work
- Background validation: Complexity without clear benefit

## Integration Points

### Decision: Node Creation Integration
**Chosen**: Delegate to existing node creation services
**Rationale**:
- Reuses established node creation logic
- Maintains consistency with manual node creation
- Leverages existing validation and storage
**Alternatives considered**:
- Direct node creation: Duplicates existing functionality
- Template-specific node creation: Inconsistent behavior

### Decision: Placeholder Processing Integration
**Chosen**: Process placeholders before node creation
**Rationale**:
- Clean separation of concerns
- Template processing isolated from node logic
- Easier testing and validation
**Alternatives considered**:
- Runtime placeholder resolution: Complicates node model
- Post-creation processing: Risk of inconsistent state

# Data Model: Materialize All Command Option

## Core Entities

### BatchMaterializeResult
Represents the outcome of materializing all placeholders in a binder.

**Fields**:
- `total_placeholders: int` - Total number of placeholders found
- `successful_materializations: List[MaterializeResult]` - Successfully materialized items
- `failed_materializations: List[MaterializeFailure]` - Failed materialization attempts
- `execution_time: float` - Total time taken for batch operation

**Relationships**:
- Contains multiple `MaterializeResult` instances
- Contains multiple `MaterializeFailure` instances

### MaterializeResult
Represents a successful individual placeholder materialization.

**Fields**:
- `display_title: str` - Title of the materialized placeholder
- `node_id: NodeId` - Generated UUIDv7 identifier for the new node
- `file_paths: List[str]` - Created file paths (`{id}.md`, `{id}.notes.md`)
- `position: str` - Position in binder hierarchy (e.g., "[0][1]")

**Relationships**:
- References existing `NodeId` value object
- Part of `BatchMaterializeResult`

### MaterializeFailure
Represents a failed placeholder materialization attempt.

**Fields**:
- `display_title: str` - Title of the placeholder that failed to materialize
- `error_type: str` - Type of error (filesystem, validation, etc.)
- `error_message: str` - Human-readable error description
- `position: str` - Position in binder hierarchy where failure occurred

**Relationships**:
- Part of `BatchMaterializeResult`

### PlaceholderSummary
Represents discovered placeholder information before materialization.

**Fields**:
- `display_title: str` - Title of the placeholder
- `position: str` - Position in binder hierarchy (e.g., "[0][1]")
- `parent_title: str | None` - Parent item title if applicable
- `depth: int` - Nesting level in binder hierarchy

**Relationships**:
- Collected into lists for batch processing
- Transformed into `MaterializeResult` or `MaterializeFailure`

## State Transitions

### Placeholder Discovery Flow
```
Binder → Scan for placeholders → List[PlaceholderSummary]
```

### Batch Materialization Flow
```
List[PlaceholderSummary] → Process individually → BatchMaterializeResult
  ├→ Individual success → MaterializeResult
  └→ Individual failure → MaterializeFailure
```

### Individual Materialization State
```
PlaceholderSummary → Validate → Generate NodeId → Create Files → Update Binder
  ├→ Success: MaterializeResult
  └→ Failure: MaterializeFailure
```

## Validation Rules

### BatchMaterializeResult Validation
- `total_placeholders` must equal `len(successful_materializations) + len(failed_materializations)`
- `execution_time` must be non-negative
- Either `successful_materializations` or `failed_materializations` must be non-empty if `total_placeholders > 0`

### MaterializeResult Validation
- `display_title` must be non-empty string
- `node_id` must be valid UUIDv7
- `file_paths` must contain exactly 2 paths (main and notes files)
- `position` must follow format "[n][m]..." pattern

### MaterializeFailure Validation
- `display_title` must be non-empty string
- `error_type` must be from predefined set (filesystem, validation, already_materialized, etc.)
- `error_message` must be non-empty and human-readable

### PlaceholderSummary Validation
- `display_title` must be non-empty string
- `position` must follow hierarchical format
- `depth` must be non-negative integer
- `parent_title` can be None only if `depth == 0`

## Data Flow Patterns

### Input Processing
1. CLI receives `--all` flag
2. Load binder from filesystem
3. Scan binder for placeholders → `List[PlaceholderSummary]`
4. Validate placeholder list is non-empty

### Batch Processing
1. Initialize `BatchMaterializeResult` with placeholder count
2. For each `PlaceholderSummary`:
   - Attempt materialization
   - Record success as `MaterializeResult`
   - Record failure as `MaterializeFailure`
3. Update `execution_time` and return result

### Output Generation
1. Success case: Report materialized count and details
2. Partial failure: Report successes and failures separately
3. Complete failure: Report error summary and suggestions
4. Empty case: Report no placeholders found message

## Error Handling Data

### Error Type Classification
- **`filesystem`**: File creation, permission, disk space issues
- **`validation`**: Invalid placeholder state, corrupted binder
- **`already_materialized`**: Placeholder already has node_id
- **`binder_integrity`**: Binder structure violations
- **`id_generation`**: UUID generation failures

### Error Recovery Context
- **Continue processing**: Most error types allow batch operation to continue
- **Stop processing**: Critical binder integrity errors should halt operation
- **Retry candidates**: Filesystem errors may be retryable by user

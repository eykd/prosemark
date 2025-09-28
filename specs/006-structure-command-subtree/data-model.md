# Data Model: Structure Command Subtree Display

## Entity Overview

This feature leverages existing entities without modification. All entities are already implemented and validated in the codebase.

## Core Entities

### NodeId (Existing)
**Location**: `src/prosemark/domain/models.py`
**Purpose**: Value object representing a unique node identifier

**Attributes**:
- `value: str` - UUID v7 string representation

**Validation Rules**:
- Must be valid UUID format
- Immutable after creation
- Raises `NodeIdentityError` for invalid format

**Usage in Feature**:
- Optional parameter to filter tree display
- Used to locate subtree root in binder hierarchy

### Binder (Existing)
**Location**: `src/prosemark/domain/binder.py`
**Purpose**: Container for hierarchical document structure

**Key Methods**:
- `find_by_id(node_id: NodeId) -> BinderItem | None` - Locate node in hierarchy
- `roots: list[Item]` - Top-level items in binder

**Usage in Feature**:
- Source of tree structure data
- Provides node lookup capability

### BinderItem (Existing)
**Location**: `src/prosemark/domain/binder.py`
**Purpose**: Node in the document hierarchy

**Attributes**:
- `node_id: NodeId | None` - Unique identifier (None for placeholders)
- `display_title: str` - Human-readable title
- `children: list[BinderItem]` - Child nodes

**Usage in Feature**:
- Represents nodes in displayed tree
- Provides recursive structure for subtree traversal

## Data Flow

### Input Processing
1. **CLI receives optional node_id string**
   - Empty/None → Display full tree
   - UUID string → Parse and validate

2. **NodeId validation**
   - Valid UUID → Create NodeId instance
   - Invalid format → Raise NodeIdentityError

### Tree Filtering
1. **Full tree display (node_id is None)**
   - Load complete binder
   - Format all roots and descendants

2. **Subtree display (node_id provided)**
   - Load binder
   - Find node by NodeId
   - If not found → Raise NodeNotFoundError
   - Format node and its descendants only

### Output Formatting
- Tree format: ASCII art with indentation
- JSON format: Nested dictionary structure
- Both formats preserve hierarchy relationships

## State Management

This feature is **stateless** - no persistent state changes occur:
- Read-only operation on existing binder
- No modifications to node data
- No cache or session state required

## Error States

### Invalid Node ID Format
**Trigger**: Non-UUID string provided
**Response**: NodeIdentityError with clear message
**Example**: "abc123" → "Invalid UUID format"

### Node Not Found
**Trigger**: Valid UUID but node doesn't exist
**Response**: NodeNotFoundError with node ID
**Example**: "550e8400-e29b-41d4-a716-446655440000" → "Node not found in binder"

### Empty Binder
**Trigger**: No nodes in binder
**Response**: Display empty tree message
**Handling**: Graceful message, no error

## Performance Considerations

### Tree Traversal
- **Algorithm**: Depth-first traversal (existing)
- **Complexity**: O(n) where n = nodes in subtree
- **Memory**: O(h) where h = tree height (recursion stack)

### Node Lookup
- **Algorithm**: Linear search through binder (existing)
- **Complexity**: O(n) where n = total nodes
- **Optimization**: Not needed per requirements (best-effort performance)

## Compatibility

### Backward Compatibility
- No changes to existing data structures
- No changes to storage format
- No changes to existing method signatures
- Optional parameter ensures existing usage unaffected

### Forward Compatibility
- NodeId format allows future extensions
- Tree structure supports arbitrary depth
- Output formats extensible (tree, JSON)

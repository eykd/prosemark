# Research: Preserve Extraneous Text in Binder Operations

## Current State Analysis

### Existing Binder Parser Implementation

**Decision**: Enhance `MarkdownBinderParser` to preserve non-structural text
**Rationale**: Current parser only processes Markdown list items with links, discarding everything else
**Current Behavior**:
- Uses regex `LIST_ITEM_PATTERN` to extract only `- [title](link)` patterns
- Validates markdown format strictly, raising errors for malformed content
- Builds pure `Binder` domain objects with hierarchy
- Renders clean markdown lists without any extraneous content

### Text Preservation Requirements

**Decision**: Two-phase parsing approach: structural extraction + text preservation
**Rationale**: Must maintain existing domain model purity while preserving formatting
**Alternatives considered**:
- Modify domain models to include text → Rejected: violates domain separation
- Store text in separate data structure → Chosen: maintains clean architecture
- Parse to different domain model → Rejected: breaks existing contracts

### UUID7 Validation Strategy

**Decision**: Use existing `NODE_ID_PATTERN` for UUID validation
**Rationale**: Pattern already handles 36-character UUID format correctly
**Current Pattern**: `([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`
**Alternatives considered**:
- Full UUID7 semantic validation → Rejected: overkill for text preservation
- No validation → Rejected: could treat non-UUID text as structural
- Format-only validation → Chosen: sufficient for structural/extraneous distinction

### Text Storage and Round-Trip Preservation

**Decision**: Enhanced parser maintains original text with positional markers
**Rationale**: Must preserve exact formatting and positioning for user content
**Implementation Strategy**:
- Parse original markdown into lines with metadata
- Mark structural vs extraneous text by line/position
- Store extraneous text with positional anchors
- Reconstruct during rendering with preserved formatting

### Integration with Existing Operations

**Decision**: Enhance existing binder operations transparently
**Rationale**: All operations (compile, add, remove, restructure) must preserve text
**Current Operations**: `BinderRepoFS` handles file I/O, parser handles format conversion
**Enhancement Points**:
- `parse_to_binder()` - extract and store extraneous text
- `render_from_binder()` - restore extraneous text in original positions
- Domain operations remain unchanged - pure business logic

### Error Handling Strategy

**Decision**: Treat malformed syntax as extraneous text
**Rationale**: User content should never be lost, even if not perfectly structured
**Current Behavior**: Raises `BinderFormatError` for malformed lists
**Enhanced Behavior**: Preserve malformed content as extraneous text, continue processing valid elements

## Technical Approach

### Enhanced Parser Architecture

```
MarkdownBinderParser (enhanced)
├── parse_to_binder()
│   ├── extract_structural_elements()  # existing logic
│   ├── identify_extraneous_text()     # new: preserve non-structural
│   └── build_combined_representation() # new: text + structure
└── render_from_binder()
    ├── render_structural_hierarchy()   # existing logic
    ├── merge_extraneous_text()         # new: restore preserved text
    └── maintain_original_formatting()  # new: exact positioning
```

### Data Structure Enhancement

**Decision**: Add `PreservedText` value object for text storage
**Rationale**: Clean separation between structural and extraneous content
**Structure**:
```python
@dataclass
class PreservedText:
    content: str
    line_number: int
    position_marker: str  # before/after structural element
```

### Backward Compatibility

**Decision**: Maintain existing parser interface contracts
**Rationale**: Feature enhances behavior without breaking existing functionality
**Guarantee**: All existing tests pass, domain models unchanged, CLI interfaces preserved

## Research Findings Summary

- Current parser is well-architected for enhancement
- Hexagonal architecture supports clean text preservation layer
- UUID7 validation logic already exists and is sufficient
- No constitutional violations - enhancement aligns with existing patterns
- Clear separation between structural parsing and text preservation concerns

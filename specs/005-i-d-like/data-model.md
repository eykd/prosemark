# Data Model: Preserve Extraneous Text in Binder Operations

## Domain Entities

### Enhanced Binder Parser (Value Object)
**Purpose**: Parse and render markdown with text preservation
**Fields**:
- `structural_elements: list[StructuralElement]` - Parsed list items and links
- `preserved_text: list[PreservedText]` - Non-structural content with positioning
- `original_content: str` - Complete original markdown for reference

**Validation Rules**:
- Structural elements must have valid indentation hierarchy
- UUID7 links must match 36-character format: `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`
- Preserved text must maintain original line numbers and positions

### StructuralElement (Value Object)
**Purpose**: Represents valid markdown list items with links
**Fields**:
- `indent_level: int` - Indentation depth (0 = root)
- `title: str` - Display title text
- `node_id: NodeId | None` - UUID7 if valid link found
- `line_number: int` - Original line position

**Validation Rules**:
- `indent_level >= 0`
- `title` must not be empty string
- `node_id` validated by existing `NODE_ID_PATTERN` regex
- `line_number > 0`

### PreservedText (Value Object)
**Purpose**: Store extraneous text with positioning information
**Fields**:
- `content: str` - Original text content with formatting
- `line_number: int` - Original line position in markdown
- `position_anchor: PositionAnchor` - Where text appears relative to structure
- `formatting_preserved: bool` - Whether original formatting maintained

**Validation Rules**:
- `content` must not be empty string
- `line_number > 0`
- `position_anchor` must be valid enum value

### PositionAnchor (Enum)
**Purpose**: Define where preserved text appears in relation to structural elements
**Values**:
- `BEFORE_STRUCTURE` - Text appears before any structural elements
- `BETWEEN_ELEMENTS` - Text appears between structural elements
- `AFTER_STRUCTURE` - Text appears after all structural elements
- `INLINE_WITH_ELEMENT` - Text on same line as structural element

## Enhanced Parser State

### ParserResult (Value Object)
**Purpose**: Complete parsing result with both structure and preserved content
**Fields**:
- `binder: Binder` - Standard domain object (unchanged)
- `preserved_text: list[PreservedText]` - All non-structural content
- `parsing_metadata: ParsingMetadata` - Processing information

### ParsingMetadata (Value Object)
**Purpose**: Track parsing decisions and validation results
**Fields**:
- `malformed_elements_count: int` - Number of malformed items treated as text
- `uuid_validation_failures: int` - Non-UUID7 links treated as extraneous
- `original_line_count: int` - Total lines processed
- `structural_line_count: int` - Lines containing valid structure

## State Transitions

### Parsing Flow
```
Raw Markdown Input
├─→ Line-by-line analysis
├─→ Extract structural elements (existing logic)
├─→ Identify extraneous text (new logic)
├─→ Validate UUID7 links (enhanced logic)
├─→ Build combined result
└─→ Return ParserResult
```

### Rendering Flow
```
Enhanced Parser State
├─→ Render structural elements (existing logic)
├─→ Merge preserved text by position anchors
├─→ Maintain original formatting
└─→ Output complete markdown
```

## Integration Points

### Existing Domain Models (Unchanged)
- `Binder` - maintains current structure and contracts
- `BinderItem` - no changes to hierarchy representation
- `NodeId` - continues UUID7 type safety

### Port Interface Enhancement
```python
class EnhancedBinderParser(Protocol):
    def parse_with_preservation(self, markdown: str) -> ParserResult: ...
    def render_with_preservation(self, result: ParserResult) -> str: ...
    # Existing methods maintained for backward compatibility
    def parse_to_binder(self, markdown: str) -> Binder: ...
    def render_from_binder(self, binder: Binder) -> str: ...
```

### Error Handling
- `PreservationError` - Issues with text preservation logic
- `MalformedTextError` - Enhanced error with preserved content context
- Existing `BinderFormatError` enhanced with preservation context

## Validation Business Rules

### UUID7 Link Validation
- Must match exact 36-character format
- Case-insensitive hexadecimal characters
- Links not matching UUID7 format treated as extraneous text
- No semantic validation beyond format

### Structural Element Rules
- Must start with `- [` pattern
- Must have balanced brackets `[title]`
- Indentation must be consistent (2-space increments)
- Malformed structural elements become preserved text

### Text Preservation Rules
- All non-structural text preserved exactly as written
- Formatting (bold, italic, headers) maintained character-for-character
- Line endings and whitespace preserved
- Empty lines maintained in original positions

### Round-Trip Integrity
- `render(parse(markdown)) === markdown` for all content
- Structural operations only modify list items and UUID7 links
- Extraneous text remains unchanged through any operation

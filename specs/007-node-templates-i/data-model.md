# Data Model: Node Templates

## Core Entities

### Template
Represents a template file that can be used to create nodes.

**Fields**:
- `name: str` - Template identifier (filename without .md extension)
- `path: Path` - Absolute path to template file
- `content: str` - Raw template content (markdown with YAML frontmatter)
- `frontmatter: dict[str, Any]` - Parsed YAML frontmatter
- `body: str` - Markdown content after frontmatter
- `placeholders: list[Placeholder]` - Extracted placeholder definitions
- `is_directory_template: bool` - True if template is part of a directory structure

**Validation Rules**:
- Path must exist and be readable
- Content must be valid UTF-8
- Must have valid YAML frontmatter
- Body must be valid Markdown
- Placeholders must use valid syntax (`{{variable_name}}`)
- Template name must match file naming conventions

**State Transitions**:
- Raw file → Parsed template (validation)
- Parsed template → Instantiated nodes (placeholder replacement)

### Placeholder
Represents a variable placeholder within a template.

**Fields**:
- `name: str` - Variable name (alphanumeric + underscore)
- `pattern: str` - Full placeholder pattern (`{{name}}`)
- `required: bool` - Whether placeholder must have a value
- `default_value: str | None` - Default value if not required
- `description: str | None` - Human-readable description for prompting

**Validation Rules**:
- Name must be valid Python identifier
- Pattern must match `{{[a-zA-Z_][a-zA-Z0-9_]*}}`
- Default value must be provided if not required

### TemplateDirectory
Represents a collection of related templates organized as a directory.

**Fields**:
- `name: str` - Directory name
- `path: Path` - Absolute path to template directory
- `templates: list[Template]` - Templates within directory
- `structure: dict[str, Any]` - Directory structure representation

**Validation Rules**:
- Path must exist and be a directory
- Must contain at least one .md file
- All contained files must be valid templates

### PlaceholderValue
Represents a user-provided value for a placeholder during template instantiation.

**Fields**:
- `placeholder_name: str` - Name of the placeholder
- `value: str` - User-provided value
- `source: str` - How value was obtained (user_input, default, config)

**Validation Rules**:
- Placeholder name must match existing placeholder
- Value must be non-empty string for required placeholders
- Source must be valid enumeration value

## Relationships

### Template ↔ Placeholder
- **Type**: One-to-Many composition
- **Description**: A template contains zero or more placeholders
- **Constraints**: Placeholders are owned by template, lifecycle tied together

### TemplateDirectory ↔ Template
- **Type**: One-to-Many aggregation
- **Description**: A directory contains one or more templates
- **Constraints**: Templates can exist independently, directory provides organization

### Placeholder ↔ PlaceholderValue
- **Type**: One-to-One association
- **Description**: Each placeholder gets exactly one value during instantiation
- **Constraints**: Temporary relationship during template processing

## Domain Invariants

### Template Consistency
- All placeholders in template content must be extractable from body
- Frontmatter placeholders must also exist in metadata fields
- Template name must be unique within same directory

### Placeholder Validity
- Placeholder names must be consistent across template references
- Required placeholders cannot have default values
- Default values must be valid for placeholder context

### Directory Structure Integrity
- All templates in directory must be valid individually
- Relative references between templates must be resolvable
- Directory must not contain non-template files (except subdirectories)

## Aggregates

### TemplateInstance
Root aggregate for template instantiation operations.

**Aggregate Root**: Template
**Entities**: Placeholder, PlaceholderValue
**Value Objects**: TemplatePath, PlaceholderPattern

**Operations**:
- Validate template structure
- Extract placeholders
- Prompt for values
- Replace placeholders with values
- Generate final node content

### TemplateCollection
Root aggregate for template discovery and management.

**Aggregate Root**: TemplateDirectory
**Entities**: Template list
**Value Objects**: DirectoryPath, TemplateFilter

**Operations**:
- Scan directory for templates
- Validate all templates
- Filter by criteria
- Provide template metadata

## Value Objects

### TemplatePath
Immutable path representation with validation.

**Properties**:
- `value: Path` - Absolute path
- `exists: bool` - Whether path exists
- `is_template: bool` - Whether path points to valid template

### PlaceholderPattern
Immutable placeholder pattern with parsing capabilities.

**Properties**:
- `raw: str` - Original pattern string
- `name: str` - Extracted variable name
- `is_valid: bool` - Whether pattern is well-formed

### DirectoryPath
Immutable directory path with template scanning capabilities.

**Properties**:
- `value: Path` - Absolute directory path
- `template_count: int` - Number of templates found
- `is_valid_template_directory: bool` - Whether directory contains valid templates

## Error Handling

### Template Errors
- `TemplateNotFoundError` - Template file does not exist
- `TemplateParseError` - Invalid YAML frontmatter or markdown
- `TemplateValidationError` - Content violates prosemark format
- `InvalidPlaceholderError` - Malformed placeholder syntax

### Directory Errors
- `TemplateDirectoryNotFoundError` - Directory does not exist
- `EmptyTemplateDirectoryError` - No templates found in directory
- `InvalidTemplateDirectoryError` - Contains invalid templates

### Instantiation Errors
- `MissingPlaceholderValueError` - Required placeholder not provided
- `InvalidPlaceholderValueError` - Value fails validation
- `PlaceholderProcessingError` - Error during replacement operation

# Feature Specification: Prosemark CLI Writing Project Manager MVP

**Feature Branch**: `001-mvp-i-ve`
**Created**: 2025-09-20
**Status**: Draft
**Input**: User description: "MVP: I've assembled a series of issues in sol/sol-NN.md. The issues are roughly in implementation order and should bring us close to MVP. Please examine the issues and develop your specification accordingly. Think hard."

## Execution Flow (main)
```
1. Parse user description from Input
   ’ Feature request: Complete MVP implementation based on sol/sol-NN.md issues
2. Extract key concepts from description
   ’ Actors: Writers, developers; Actions: project management, content creation, structure organization
   ’ Data: hierarchical binder structure, node content files, metadata, freeform writing
   ’ Constraints: file-based storage, CLI interface, cross-platform compatibility
3. For each unclear aspect:
   ’ All major aspects clearly defined in detailed sol files
4. Fill User Scenarios & Testing section
   ’ Clear user flows identified from TDD requirements in sol files
5. Generate Functional Requirements
   ’ All requirements testable and well-specified in sol files
6. Identify Key Entities
   ’ Binder, Node, Placeholder, Freeform content clearly defined
7. Run Review Checklist
   ’ No [NEEDS CLARIFICATION] markers needed - sol files provide comprehensive detail
   ’ Implementation details avoided - focus on user value and business requirements
8. Return: SUCCESS (spec ready for planning)
```

---

## ¡ Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
Writers and content creators need a hierarchical project management system that organizes complex writing projects (novels, documentation, research) through a command-line interface while preserving content safety and enabling integration with their preferred editors.

### Acceptance Scenarios
1. **Given** empty directory, **When** user runs `pmk init --title "My Novel"`, **Then** creates new prosemark project with binder structure ready for content
2. **Given** initialized project, **When** user runs `pmk add "Chapter 1: Beginning"`, **Then** creates new content node and updates project hierarchy
3. **Given** project with nodes, **When** user runs `pmk edit <node-id> --part draft`, **Then** launches user's preferred editor to write content
4. **Given** project with multiple nodes, **When** user runs `pmk structure`, **Then** displays hierarchical tree view of entire project structure
5. **Given** any time during writing, **When** user runs `pmk write "Character ideas"`, **Then** creates timestamped freeform writing file for quick thoughts
6. **Given** project with placeholders, **When** user runs `pmk materialize "Chapter 2"`, **Then** converts placeholder to actual content node
7. **Given** existing project, **When** user runs `pmk audit`, **Then** reports any structural inconsistencies or missing files
8. **Given** project needs reorganization, **When** user runs `pmk move <node-id> --position 2`, **Then** restructures hierarchy maintaining content integrity

### Edge Cases
- What happens when binder file is manually edited outside prosemark?
- How does system handle missing node files or corrupted metadata?
- What occurs when user content contains prosemark's special markers?
- How does system behave when multiple prosemark processes run simultaneously?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST preserve user content outside managed sections byte-for-byte during all operations
- **FR-002**: System MUST create unique node identifiers using UUIDv7 format for temporal ordering and sortability
- **FR-003**: System MUST maintain hierarchical project structure in human-readable markdown format
- **FR-004**: System MUST support placeholder items that can be materialized into content nodes
- **FR-005**: System MUST create timestamped freeform writing files independent of project structure
- **FR-006**: System MUST integrate with user's preferred text editor across Windows, macOS, and Linux
- **FR-007**: System MUST perform atomic file operations to prevent data corruption during updates
- **FR-008**: System MUST audit project integrity and report structural inconsistencies
- **FR-009**: System MUST provide tree visualization of project hierarchy through CLI
- **FR-010**: System MUST support content reorganization while preserving relationships
- **FR-011**: System MUST store content metadata (title, synopsis, timestamps) in YAML frontmatter
- **FR-012**: System MUST enable safe node removal with optional file deletion

### Key Entities *(include if feature involves data)*
- **Project**: Root container with hierarchical binder structure stored in _binder.md with managed content sections
- **Node**: Individual content item with unique identifier, stored as {id}.md (main content) and {id}.notes.md (notes)
- **Placeholder**: Structural item in hierarchy without associated content files, materializable into nodes
- **Binder**: Hierarchical project structure maintaining parent-child relationships and ordering
- **Freeform Content**: Timestamped writing files independent of project structure for capturing ideas

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---

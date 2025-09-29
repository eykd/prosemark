# Feature Specification: Node Templates

**Feature Branch**: `007-node-templates-i`
**Created**: 2025-09-29
**Status**: Draft
**Input**: User description: "node templates: I'd like to be able to define node templates in `./templates` and use them w/ the `add` command. We should be able to create trees of nodes from a template (directory with node templates inside of it)"

## Clarifications

### Session 2025-09-29
- Q: When a template contains placeholder content, how should the system handle these during node creation? → A: Replace interactively - prompt user for each placeholder value
- Q: When the system encounters an invalid template (malformed structure, missing required fields, or syntax errors), what should be the behavior? → A: Halt execution - stop immediately with error message
- Q: What format should template files use for their content structure? → A: Prosemark format - existing prosemark node format with all features
- Q: How should users list available templates? → A: Flag on add command - `pmk add --list-templates`
- Q: What naming conventions and file extension requirements should templates follow? → A: .md extension required - all templates must be .md files

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a knowledge worker, I want to create predefined node structures from templates so that I can quickly scaffold common patterns without manually creating each node and relationship.

### Acceptance Scenarios
1. **Given** I have a template directory `./templates/project-setup/` containing multiple template files, **When** I run `pmk add --template project-setup`, **Then** the system creates all nodes from the template structure in my knowledge base
2. **Given** I have a single template file `./templates/meeting-notes.md`, **When** I run `pmk add --template meeting-notes`, **Then** the system creates a new node based on that template with pre-filled content structure
3. **Given** I want to see available templates, **When** I run `pmk add --list-templates`, **Then** the system displays all available templates from the `./templates` directory
4. **Given** a template contains placeholder content, **When** I create a node from that template, **Then** the system prompts the user interactively for each placeholder value

### Edge Cases
- What happens when the `./templates` directory doesn't exist?
- How does the system handle template name conflicts or duplicate template names?
- What happens when a template references files that don't exist?
- How does the system handle templates with invalid node content or malformed structure?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST recognize and use a `./templates` directory for storing node templates
- **FR-002**: System MUST extend the `add` command to accept a `--template` parameter for specifying template names
- **FR-003**: System MUST be able to create individual nodes from single template files
- **FR-004**: System MUST be able to create node trees from template directories containing multiple template files
- **FR-005**: System MUST provide a `--list-templates` flag on the `add` command to display all available templates from the `./templates` directory
- **FR-006**: System MUST handle template directory structures and preserve relationships between template files when creating node trees
- **FR-007**: System MUST halt execution immediately with a clear error message when encountering invalid templates (malformed structure, missing required fields, or syntax errors)
- **FR-008**: Templates MUST use the existing prosemark node format with all its features (markdown content with YAML frontmatter, node relationships, etc.)
- **FR-009**: System MUST require all template files to use the `.md` file extension

### Key Entities *(include if feature involves data)*
- **Template**: A predefined node structure or content pattern stored in the `./templates` directory as a `.md` file using prosemark format, can be either a single file or part of a directory structure
- **Template Directory**: A collection of related templates organized as a directory structure that creates multiple interconnected nodes
- **Node Tree**: The resulting structure of multiple nodes created from a template directory, preserving the hierarchical relationships defined in the template

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---

# Feature Specification: Write-Only Freewriting Interface

**Feature Branch**: `003-write-only-freewriting`
**Created**: 2025-09-24
**Status**: Draft
**Input**: User description: "write-only-freewriting: interface for freewriting, either on a specified node, or if no node specified, a daily freewrite file with its own naming convention."

## Execution Flow (main)
```
1. Parse user description from Input
   � If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   � Identify: actors, actions, data, constraints
3. For each unclear aspect:
   � Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   � If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   � Each requirement must be testable
   � Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   � If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   � If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## � Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

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
As a user who wants to practice freewriting, I need a distraction-free write-only interface where I can capture my thoughts quickly without the ability to edit or review what I've written. I can either write to a specific node in my system or, if I don't specify a destination, my writing will be saved to a daily freewrite file with a consistent naming convention.

### Acceptance Scenarios
1. **Given** the user runs `pmk write` without specifying a node, **When** they type text and hit ENTER, **Then** their content is appended to a new timestamped file in the format YYYY-MM-DD-HHmm.md in the current directory
2. **Given** the user runs `pmk write <uuid>` with a valid UUID, **When** they type text and hit ENTER, **Then** their content is appended to the specified node (creating it if necessary)
3. **Given** the user is typing in the input box, **When** they use readline-style text motions, **Then** they can edit within the input box only, not the already-saved content
4. **Given** multiple freewriting sessions on the same day without node specification, **When** the user starts each new session, **Then** each session creates its own timestamped file

### Edge Cases
- What happens when a specified node doesn't exist or is inaccessible?
- How does system handle when the user tries to save empty content?
- What happens if the daily file already exists when starting a new session?
- How does the system handle interruptions or crashes during a writing session?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST provide a textual UI with top 80% showing the bottom of the current file and bottom 20% showing an input box
- **FR-002**: System MUST allow users to optionally specify a target node via `pmk write <uuid>` command
- **FR-003**: System MUST automatically create timestamped freewrite files (YYYY-MM-DD-HHmm.md format) when no node is specified
- **FR-004**: Each freewriting session MUST create a new timestamped file (not append to existing daily files)
- **FR-005**: System MUST append and save content to the file when user hits ENTER in the input box
- **FR-006**: Interface MUST allow readline-style text editing within the input box only, not in already-saved content
- **FR-007**: System MUST accept valid UUID nodes and automatically create non-existent nodes, adding them to the binder
- **FR-008**: System MUST provide feedback when content is successfully saved
- **FR-009**: System MUST display errors in the UI and continue the session when save failures occur (disk full, permissions, etc.)
- **FR-010**: Freewriting sessions MUST be unlimited by default with optional time limit (with countdown display) and/or word count goal
- **FR-011**: System MUST store daily freewrite files in the current working directory
- **FR-012**: System MUST track and display word count in the UI at all times
- **FR-013**: System MUST support `--title` flag for providing titles when using the command

### Key Entities *(include if feature involves data)*
- **Freewrite Session**: Represents a single writing session, containing the raw text content and metadata about when it was created
- **Node**: A destination location in the system where freewriting content can be directed
- **Daily Freewrite File**: A file created automatically for each day's freewriting sessions when no specific node is provided

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

# Feature Specification: Optional Node ID for Compile Command

**Feature Branch**: `008-default-compile-all`
**Created**: 2025-10-01
**Status**: Ready for Planning
**Input**: User description: "default compile all nodes: Let's make the node ID argument optional to the `compile` command. If no node ID is provided, then it should select all the root nodes in the binder."

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature request is clear: make node_id optional for compile command
2. Extract key concepts from description
   → Actors: CLI users compiling content
   → Actions: compile without specifying node ID, select all root nodes
   → Data: binder structure, root nodes, compiled output
   → Constraints: must compile all root nodes when no ID provided
3. For each unclear aspect:
   → All major ambiguities resolved through clarification session
4. Fill User Scenarios & Testing section
   → User scenarios defined below
5. Generate Functional Requirements
   → Requirements are testable and defined below
6. Identify Key Entities (if data involved)
   → Entities identified below
7. Run Review Checklist
   → WARN "Spec has uncertainties" - marked with [NEEDS CLARIFICATION]
8. Return: SUCCESS (spec ready for planning after clarifications)
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
As a Prosemark user working on a project with multiple independent document sections, I want to compile all my content at once without having to specify each root node individually, so that I can quickly generate a complete export of my entire project hierarchy.

### Acceptance Scenarios
1. **Given** a binder with 3 root nodes (each representing a separate document section), **When** I run the compile command without providing a node ID, **Then** the system compiles all 3 root nodes and their subtrees into a single concatenated output with double-newline separators between each root's compilation
2. **Given** a binder with no materialized root nodes (empty project or only placeholders), **When** I run the compile command without providing a node ID, **Then** the system produces empty output and exits successfully (no error)
3. **Given** a binder with 2 root nodes and I provide a specific node ID, **When** I run the compile command with that node ID, **Then** the system compiles only that specific node and its subtree (existing behavior preserved)
4. **Given** a binder with root nodes containing empty content, **When** I run the compile command without a node ID, **Then** empty nodes are handled according to the --include-empty flag (excluded by default, included when flag is set)

### Edge Cases
- When the binder contains only placeholder root items (no materialized nodes), system produces empty output and exits successfully
- How does the system handle very large binders with many root nodes (performance considerations)?
- What happens if a root node exists in the binder but its corresponding file is missing? (existing compile behavior applies - skips missing files)
- Root nodes must be processed in binder order (as they appear top-to-bottom in the roots list)

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST allow the compile command to be invoked without a node ID argument
- **FR-002**: System MUST identify all root nodes in the binder when no node ID is provided
- **FR-003**: System MUST compile each root node and its entire subtree when compiling all roots
- **FR-004**: System MUST preserve the existing behavior when a specific node ID is provided
- **FR-005**: System MUST concatenate all root node compilations into a single output stream, separated by double newlines (same format as child nodes within a subtree)
- **FR-006**: System MUST handle empty binders (no materialized root nodes) by producing empty output with statistics showing 0 nodes compiled (exit successfully)
- **FR-007**: System MUST skip placeholder root items (items with no node_id) when compiling all roots
- **FR-008**: System MUST apply the --include-empty flag behavior consistently to all root nodes (same behavior as single-node compilation)
- **FR-009**: System MUST report combined statistics across all compiled roots (total node count, total nodes processed, skipped empty count) in the same format as single-node compilation
- **FR-010**: System MUST process root nodes in binder order (top to bottom as they appear in the roots list)

### Key Entities *(include if feature involves data)*
- **Root Node**: A BinderItem in the binder hierarchy that has no parent (is_root() returns true). May or may not be materialized (have a node_id).
- **Binder**: The hierarchical structure containing all document organization information, with a collection of root-level items
- **Compile Request**: The request to compile content, which now has an optional node_id field instead of required
- **Compile Result**: The output of compilation, containing concatenated content and statistics about the compilation process

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

## Clarifications

### Session 2025-10-01

- Q: How should multiple root nodes be concatenated in the output? → A: Concatenate with double newlines only (same as child nodes, no visual distinction between roots)
- Q: In what order should root nodes be processed when compiling all roots? → A: Binder order (top to bottom as they appear in the binder hierarchy)
- Q: How should the --include-empty flag behavior apply when compiling all roots? → A: Honor the existing --include-empty flag for all roots (consistent with single-node compilation)
- Q: What should happen when the binder has no materialized root nodes? → A: Produce empty output with statistics showing 0 nodes compiled (silent success)
- Q: How should compilation statistics be reported when compiling all roots? → A: Combined statistics only (total nodes across all roots, matching single-node format)

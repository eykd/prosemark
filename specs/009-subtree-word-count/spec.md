# Feature Specification: Subtree Word Count

**Feature Branch**: `009-subtree-word-count`
**Created**: 2025-10-03
**Status**: Draft
**Input**: User description: "subtree word count: Let's add a `wc` subcommand that will count the words in the compiled text of a node subtree, using the same mechanics as the `compile` command: if a node ID is specified, count all the words in that node's subtree. If no node ID is specified, then select all the root nodes in the tree. For reference, I've been getting word counts so far using the shell command `pmk compile | wc -w`. Be user to use a nuanced method for splitting words, being sure to handle contractions and different sorts of dashes and other joining punctuation correctly in each context using standard US English heuristics. Whatever algorithm `wc -w` uses is probably a good standard."

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

## Clarifications

### Session 2025-10-03
- Q: What output format should `pmk wc` use for displaying word count results? → A: Just the number (minimal, scriptable)
- Q: When a user specifies a node ID that doesn't exist, what should happen? → A: Exit with error code, print error message to stderr, output 0 to stdout
- Q: When a node or subtree has no text content (completely empty), what should the command output? → A: Output `0` with exit code 0 (success)
- Q: How should standalone numbers be counted (e.g., "123", "3.14", "2025")? → A: Each number counts as one word
- Q: How should URLs and email addresses be counted? → A: Each URL/email counts as one word (single token)

---

## User Scenarios & Testing

### Primary User Story
As a Prosemark user, I want to count the words in one or more nodes' compiled content so that I can track my writing progress and measure the length of my work. When I compile nodes for reading or export, I often need to know the word count, which I've been doing manually by piping compile output to `wc -w`. Having a dedicated word count command will provide this information more conveniently and with proper word-splitting that handles contractions, dashes, and other punctuation correctly.

### Acceptance Scenarios
1. **Given** a tree with a single node containing "Hello world", **When** I run `pmk wc` with that node's ID, **Then** the system outputs `2`
2. **Given** a tree with a parent node and two child nodes, **When** I run `pmk wc` with the parent node's ID, **Then** the system counts words across all compiled content in the subtree (parent + children) and outputs the count as a plain number
3. **Given** a tree with multiple root nodes, **When** I run `pmk wc` without specifying a node ID, **Then** the system counts words across all root nodes and their subtrees and outputs the count as a plain number
4. **Given** a node containing text with contractions like "don't" and "it's", **When** I count words, **Then** each contraction counts as one word (not split at apostrophe)
5. **Given** a node containing text with em-dashes like "word—word" or en-dashes like "word–word", **When** I count words, **Then** the dashes are handled according to US English conventions (treating joined words appropriately based on context)
6. **Given** a node containing text with hyphens like "well-known", **When** I count words, **Then** hyphenated compounds count as single words per US English standards
7. **Given** a node containing "There are 123 items", **When** I count words, **Then** the system outputs `4` (numbers count as words)
8. **Given** a node containing "Visit https://example.com or email user@example.com", **When** I count words, **Then** the system outputs `5` (URL and email each count as one word)
9. **Given** an empty node, **When** I run `pmk wc` with that node's ID, **Then** the system outputs `0` with exit code 0
10. **Given** a non-existent node ID, **When** I run `pmk wc` with that ID, **Then** the system outputs `0` to stdout, prints error to stderr, and exits with non-zero code

### Edge Cases
- When a specified node ID doesn't exist: System exits with error code, prints error to stderr, outputs `0` to stdout
- When a node or subtree has no text content (empty): System outputs `0` with exit code 0 (normal success)
- Numbers (e.g., "123", "3.14") count as individual words
- URLs (e.g., "https://example.com") and email addresses (e.g., "user@example.com") each count as one word
- How is punctuation-only content handled?
- What happens with multiple consecutive spaces or newlines?
- How are special symbols and unicode characters handled?

## Requirements

### Functional Requirements
- **FR-001**: System MUST provide a `wc` subcommand that counts words in compiled node content
- **FR-002**: System MUST accept an optional node ID parameter to specify which subtree to count
- **FR-003**: System MUST count words across all root nodes when no node ID is specified (matching `compile` behavior)
- **FR-004**: System MUST count words in the entire subtree when a node ID is specified (parent node + all descendants)
- **FR-005**: System MUST use word-splitting algorithm compatible with standard US English conventions
- **FR-006**: System MUST treat contractions (e.g., "don't", "it's", "can't") as single words
- **FR-007**: System MUST handle hyphens in compound words (e.g., "well-known", "state-of-the-art") as single words per US English conventions
- **FR-008**: System MUST handle em-dashes and en-dashes according to US English usage patterns
- **FR-009**: System MUST handle various types of joining punctuation correctly in context
- **FR-010**: System MUST produce word counts comparable to standard `wc -w` command behavior
- **FR-014**: System MUST count standalone numbers (e.g., "123", "3.14", "2025") as individual words
- **FR-015**: System MUST count URLs (e.g., "https://example.com") and email addresses (e.g., "user@example.com") as single words without splitting at punctuation
- **FR-011**: System MUST display the word count result as a plain number with no labels or formatting (e.g., `1234`), enabling scriptable integration
- **FR-012**: System MUST exit with non-zero error code when specified node ID does not exist, printing an error message to stderr while outputting `0` to stdout
- **FR-013**: System MUST output `0` with exit code 0 (success) when a node or subtree contains no text content

### Key Entities
- **Node Subtree**: A node and all its descendant nodes, compiled in tree order to produce continuous text for word counting
- **Root Nodes**: Top-level nodes in the tree with no parent, used as default counting targets when no specific node is specified
- **Word**: A unit of text separated by whitespace, with special handling for contractions, hyphens, dashes, and other punctuation per US English conventions

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---

# Research: Subtree Word Count

## Word-Splitting Algorithm

### Decision
Use regex-based tokenization compatible with `wc -w` behavior, enhanced with US English conventions.

### Rationale
The standard `wc -w` command splits on whitespace, but the specification requires nuanced handling of:
- Contractions (don't, it's) → single words
- Hyphens in compounds (well-known) → single words
- Numbers (123, 3.14) → count as words
- URLs (https://example.com) → single words
- Email addresses (user@example.com) → single words
- Em-dashes and en-dashes → US English rules

### Implementation Approach
1. **Primary tokenization**: Split on whitespace (`\s+`)
2. **Token preservation rules**:
   - URLs: Match pattern `https?://[^\s]+` as single token
   - Emails: Match pattern `[^\s@]+@[^\s@]+` as single token
   - Contractions: Keep apostrophes within word boundaries
   - Hyphens: Keep hyphens connecting alphanumeric characters
   - Numbers: Match numeric patterns including decimals
3. **Punctuation stripping**: Remove leading/trailing punctuation from tokens
4. **Empty token filtering**: Discard tokens that become empty after processing

### Alternatives Considered

**NLTK Tokenizer**
- Pros: Sophisticated linguistic rules, handles edge cases
- Cons: Heavyweight dependency (>1MB), requires training models, overkill for word counting
- Rejected: Violates simplicity principle, adds unnecessary complexity

**Simple `split()`**
- Pros: Built-in, fast, simple
- Cons: Doesn't handle punctuation correctly, splits contractions incorrectly
- Rejected: Fails acceptance criteria (contractions, hyphens, URLs)

**Spacy Tokenizer**
- Pros: Production-grade NLP, excellent tokenization
- Cons: Heavy dependency (100MB+), requires model downloads
- Rejected: Massive overhead for simple word counting task

### Reference Implementation
Python regex pattern approach:
```python
import re

def count_words_us_english(text: str) -> int:
    # Preserve URLs and emails as single tokens
    # Split on whitespace
    # Filter empty tokens
    # Count results
```

Complexity: O(n) where n = text length
Memory: O(n) for token list

### Testing Strategy
Contract tests verify all acceptance scenarios:
- "don't it's" → 2 words (contractions)
- "well-known state-of-the-art" → 2 words (hyphens)
- "There are 123 items" → 4 words (numbers)
- "Visit https://example.com" → 2 words (URLs)
- "email user@example.com" → 2 words (emails)
- "" → 0 words (empty)
- "word  \n\n  word" → 2 words (whitespace normalization)

## Compile Infrastructure Reuse

### Decision
Inject `CompileSubtreeUseCase` into `WordCountUseCase` to obtain compiled text.

### Rationale
Word counting operates on compiled node content, matching user workflow:
```bash
# Current user workflow
pmk compile | wc -w

# New workflow
pmk wc  # equivalent behavior, integrated
```

### Benefits
1. **Consistency**: Uses same subtree traversal logic as compile
2. **Reuse**: No duplication of node selection (specific ID vs all roots)
3. **Ordering**: Respects binder ordering automatically
4. **Testing**: Leverages existing compile test coverage
5. **Maintainability**: Single source of truth for compilation

### Architecture
```
CLI (wc.py)
  ↓
WordCountUseCase
  ↓ compile_subtree()
  CompileSubtreeUseCase → CompileResult(content)
  ↓ count_words()
  WordCountService → int
  ↓
WordCountResult(count, content)
```

### Implementation Notes
- `CompileRequest(node_id, include_empty)` passed to compile use case
- `CompileResult.content` passed to word counter
- Error handling propagates from compile layer
- Empty content → count = 0 (natural fallthrough)

## Error Handling Strategy

### Decision
Match `compile` command error handling patterns for consistency.

### Error Cases

**1. Invalid Node ID Format**
```python
# Input: pmk wc "not-a-uuid"
# Behavior:
#   stderr: "Error: Invalid node ID format: not-a-uuid"
#   stdout: "0"
#   exit code: 1
```
Reference: compile.py:58-59

**2. Node Not Found**
```python
# Input: pmk wc "01JXXXXXXXXXXXXXXXXXXXXX" (valid format, doesn't exist)
# Behavior:
#   stderr: "Error: Node not found: 01JXXXXXXXXXXXXXXXXXXXXX"
#   stdout: "0"
#   exit code: 1
```
Reference: compile.py:69-74

**3. Empty Content**
```python
# Input: pmk wc <node-with-no-content>
# Behavior:
#   stdout: "0"
#   exit code: 0
```
Natural behavior: WordCountService returns 0 for empty string

**4. Compilation Failure**
```python
# Input: pmk wc (when no roots exist)
# Behavior:
#   stderr: "Error: Compilation failed: <error details>"
#   stdout: "0"
#   exit code: 1
```
Reference: compile.py:76-78

### Rationale
- **User expectation**: Consistent CLI behavior across commands
- **Scriptability**: Predictable error codes and output streams
- **Debugging**: Errors to stderr, data to stdout (Unix philosophy)

## Domain Model Design

### Decision
Use request/result pattern matching `CompileRequest`/`CompileResult`.

### Models

**WordCountRequest** (domain/wordcount/models.py)
```python
from dataclasses import dataclass
from prosemark.domain.models import NodeId

@dataclass(frozen=True)
class WordCountRequest:
    """Request to count words in a node subtree."""
    node_id: NodeId | None  # None = all root nodes
    include_empty: bool = False  # include empty nodes in compilation
```

**WordCountResult** (domain/wordcount/models.py)
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class WordCountResult:
    """Result of word count operation."""
    count: int  # total words found (>= 0)
    content: str  # compiled content (for testing/debugging)
```

### Rationale
- **Consistency**: Mirrors existing domain patterns
- **Immutability**: Frozen dataclasses prevent accidental mutation
- **Validation**: Type hints + Pydantic integration (if needed)
- **Testability**: Pure data structures, easy to construct in tests
- **Debugging**: Includes content field for test assertions

### Alternative Considered
Simple int return instead of `WordCountResult`:
- Rejected: Less testable (can't verify content was compiled correctly)
- Rejected: Breaks pattern established by compile use case

## Performance Considerations

### Requirements
Handle typical novel-length compilations (100K+ words) in <1 second.

### Analysis
**Compilation**: Already optimized in existing CompileSubtreeUseCase
**Word Counting**: O(n) single-pass regex tokenization
- 100K words ≈ 600K characters (avg 6 chars/word)
- Regex processing: ~10-20 microseconds per 1K characters
- Expected: <12ms for 600K characters
- Well under 1-second budget

### Optimization Strategy
Not needed for initial implementation. If needed later:
1. Compiled regex patterns (pre-compile at module load)
2. Generator-based processing for large texts
3. Streaming word count (don't store all tokens)

Current approach is sufficient for stated performance goals.

## Testing Strategy

### Contract Tests (ports/wordcount/)
Verify `WordCounterPort` implementations handle all acceptance scenarios:
- Contractions, hyphens, numbers, URLs, emails
- Empty strings, whitespace normalization
- Edge cases from specification

### Unit Tests
- **Models**: Request/result validation, immutability
- **Service**: WordCountService logic, dependency injection
- **Adapter**: StandardWordCounter regex patterns

### Integration Tests
- **CLI**: End-to-end command execution
- **Use Case**: Compile + count workflow
- **Error Handling**: All error paths verified

### Test Data
From specification acceptance scenarios (spec.md:71-81):
1. "Hello world" → 2
2. Subtree compilation → sum of all nodes
3. Multiple roots → sum of all roots
4. "don't it's" → 2
5. "word—word word–word" → varies (em-dash/en-dash rules)
6. "well-known" → 1
7. "There are 123 items" → 4
8. "Visit https://example.com or email user@example.com" → 5
9. Empty node → 0
10. Non-existent node → error + 0

## Dependencies

### Existing (Reuse)
- `prosemark.domain.models.NodeId` - node identification
- `prosemark.app.compile.use_cases.CompileSubtreeUseCase` - text compilation
- `prosemark.domain.compile.models.CompileRequest/CompileResult` - compilation contracts
- `prosemark.adapters.node_repo_fs.NodeRepoFs` - file system repository
- `prosemark.adapters.binder_repo_fs.BinderRepoFs` - binder repository

### New (Create)
- `prosemark.domain.wordcount.models` - request/result models
- `prosemark.domain.wordcount.service` - word counting logic
- `prosemark.ports.wordcount.counter` - word counter port
- `prosemark.adapters.wordcount.counter_standard` - regex-based counter
- `prosemark.app.wordcount.use_cases` - word count orchestration
- `prosemark.cli.wc` - CLI command

### Standard Library Only
- `re` - regex for tokenization
- `typing` - type hints
- `dataclasses` - model definitions

No external dependencies required beyond existing project dependencies.

## Risks & Mitigations

### Risk: Em-dash/en-dash edge cases
- **Impact**: Incorrect word counts for dashed text
- **Mitigation**: Detailed contract tests, reference `wc -w` behavior
- **Status**: Low risk - clear specification

### Risk: Unicode character handling
- **Impact**: Non-ASCII characters may not tokenize correctly
- **Mitigation**: Unicode-aware regex patterns, test with international text
- **Status**: Medium risk - defer to implementation if needed

### Risk: Regex performance on very large texts
- **Impact**: Slow word counts for massive documents (1M+ words)
- **Mitigation**: Performance testing, optimize if needed
- **Status**: Low risk - within performance budget

### Risk: Breaking changes to CompileSubtreeUseCase
- **Impact**: Word count breaks if compile API changes
- **Mitigation**: Contract tests, integration tests catch breakage early
- **Status**: Low risk - stable compile API

## Conclusion

All research questions resolved. Design decisions documented. Ready for Phase 1 (contracts, data model, quickstart).

# Data Model: Subtree Word Count

## Overview

The word count feature introduces minimal new domain models, following the request/result pattern established by the compile feature. The core entities are pure data structures with no business logic, supporting immutability and testability.

## Core Entities

### WordCountRequest

**Location**: `src/prosemark/domain/wordcount/models.py`

**Purpose**: Encapsulates parameters for word count operations.

**Structure**:
```python
from dataclasses import dataclass
from prosemark.domain.models import NodeId

@dataclass(frozen=True)
class WordCountRequest:
    """Request to count words in a node subtree.

    Attributes:
        node_id: Target node ID to count, or None to count all root nodes
        include_empty: Whether to include nodes with empty content in compilation
    """
    node_id: NodeId | None
    include_empty: bool = False
```

**Attributes**:
- `node_id`: `NodeId | None`
  - Optional node identifier
  - `None` indicates "all root nodes" (same as compile command)
  - Must be valid UUIDv7 if provided

- `include_empty`: `bool`
  - Whether to include empty nodes during compilation
  - Default: `False` (exclude empty nodes)
  - Passed through to `CompileRequest`

**Validation**:
- Immutable (frozen dataclass)
- Type safety via type hints
- NodeId validation handled by domain.models.NodeId

**Relationships**:
- Maps 1:1 to `CompileRequest` for text retrieval
- Used by `WordCountUseCase` to construct compile request

---

### WordCountResult

**Location**: `src/prosemark/domain/wordcount/models.py`

**Purpose**: Contains word count output and compiled content for verification.

**Structure**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class WordCountResult:
    """Result of a word count operation.

    Attributes:
        count: Number of words found in the compiled content
        content: The compiled text that was counted (for debugging/testing)
    """
    count: int
    content: str
```

**Attributes**:
- `count`: `int`
  - Total number of words found
  - Must be >= 0
  - Calculated by `WordCounterPort.count_words()`

- `content`: `str`
  - The compiled text that was word-counted
  - Included for testing and debugging purposes
  - Allows verification that correct text was compiled

**Validation**:
- Immutable (frozen dataclass)
- Count must be non-negative (enforced by business logic, not model)

**Relationships**:
- Produced by `WordCountUseCase.count_words()`
- Consumed by CLI layer for output formatting

---

## Internal Types

### WordToken (Internal)

**Location**: Internal to `StandardWordCounter` implementation

**Purpose**: Represents individual tokenized words during counting (if needed).

**Structure**: Not exposed in public API. Implementation detail of word-splitting algorithm.

**Usage**: May be used internally by `StandardWordCounter` for:
- Token extraction
- Pattern matching
- Debugging

**Note**: Not part of the domain model - purely an implementation detail.

---

## Port Interfaces

### WordCounterPort

**Location**: `src/prosemark/ports/wordcount/counter.py`

**Purpose**: Protocol defining word counting behavior.

**Structure**:
```python
from typing import Protocol

class WordCounterPort(Protocol):
    """Port for word counting implementations.

    Implementations must count words according to US English conventions:
    - Contractions count as one word (don't, it's)
    - Hyphenated compounds count as one word (well-known)
    - Numbers count as words (123, 3.14)
    - URLs count as one word (https://example.com)
    - Email addresses count as one word (user@example.com)
    - Em-dashes and en-dashes follow US English usage rules
    """

    def count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Input text to analyze

        Returns:
            Number of words found (>= 0)

        Rules:
            - Split on whitespace
            - Preserve contractions as single words
            - Preserve hyphenated compounds as single words
            - Count numbers as words
            - Treat URLs and emails as single words
            - Handle em-dashes and en-dashes per US English conventions
            - Return 0 for empty strings
        """
        ...
```

**Contract Requirements**:
- Pure function (no side effects)
- Deterministic (same input → same output)
- Fast (O(n) complexity where n = text length)
- Returns non-negative integers

**Implementations**:
- `StandardWordCounter`: Regex-based implementation in `adapters/wordcount/counter_standard.py`

---

## Domain Services

### WordCountService

**Location**: `src/prosemark/domain/wordcount/service.py`

**Purpose**: Orchestrates word counting with injected counter implementation.

**Structure**:
```python
from prosemark.ports.wordcount.counter import WordCounterPort
from prosemark.domain.wordcount.models import WordCountResult

class WordCountService:
    """Domain service for word counting operations."""

    def __init__(self, counter: WordCounterPort) -> None:
        """Initialize with a word counter implementation.

        Args:
            counter: Word counting implementation
        """
        self._counter = counter

    def count_text(self, text: str) -> WordCountResult:
        """Count words in text.

        Args:
            text: Compiled content to count

        Returns:
            Word count result with count and content
        """
        count = self._counter.count_words(text)
        return WordCountResult(count=count, content=text)
```

**Responsibilities**:
- Inject `WordCounterPort` dependency
- Delegate word counting to port implementation
- Construct `WordCountResult` with count and content

**Dependencies**:
- `WordCounterPort` (injected)
- `WordCountResult` (constructs)

**Relationships**:
- Used by `WordCountUseCase` to count compiled text
- Pure domain logic (no I/O)

---

## Data Flow

```
1. CLI Layer
   └─> WordCountRequest(node_id, include_empty)

2. Use Case Layer
   ├─> CompileSubtreeUseCase.compile_subtree(CompileRequest)
   │   └─> CompileResult(content)
   │
   └─> WordCountService.count_text(content)
       └─> WordCountResult(count, content)

3. CLI Layer
   └─> Output: count to stdout
```

---

## Validation Rules

### WordCountRequest
- `node_id`: Must be None or valid NodeId (UUIDv7)
- `include_empty`: Must be boolean

### WordCountResult
- `count`: Must be >= 0
- `content`: Any string (including empty)

### WordCounterPort
- Input: Any string (including empty, None handled as empty)
- Output: Non-negative integer

---

## State Transitions

No state transitions - all models are immutable value objects.

---

## Relationships Diagram

```
WordCountRequest
  ├── maps_to → CompileRequest (for text retrieval)
  └── used_by → WordCountUseCase

CompileResult
  └── provides → content → WordCountService

WordCountService
  ├── depends_on → WordCounterPort
  └── produces → WordCountResult

WordCountResult
  └── consumed_by → CLI (wc.py)

WordCounterPort (interface)
  └── implemented_by → StandardWordCounter
```

---

## Testing Strategy

### Model Tests (unit/wordcount/test_models.py)
- WordCountRequest creation
- WordCountRequest immutability
- WordCountResult creation
- WordCountResult immutability
- Type validation

### Service Tests (unit/wordcount/test_service.py)
- Dependency injection (mock WordCounterPort)
- Result construction
- Count delegation to port

### Port Contract Tests (contract/wordcount/test_wordcount_port.py)
- All acceptance scenarios from spec
- Contractions, hyphens, numbers, URLs, emails
- Edge cases (empty, whitespace)

---

## Future Considerations

### Potential Extensions (Not in Scope)
- Character count (in addition to word count)
- Line count
- Paragraph count
- Reading time estimation
- Word frequency analysis

These would follow the same pattern: new domain services, possibly new ports if complex logic is needed.

---

## Conclusion

The data model is minimal and focused:
- Two domain models (request/result)
- One port interface (word counter)
- One domain service (orchestration)
- All immutable, testable, pure

Ready for implementation following TDD approach.

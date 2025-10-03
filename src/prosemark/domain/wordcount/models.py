"""Domain models for word count feature."""

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


@dataclass(frozen=True)
class WordCountResult:
    """Result of a word count operation.

    Attributes:
        count: Number of words found in the compiled content (must be >= 0)
        content: The compiled text that was counted (for debugging/testing)

    """

    count: int
    content: str

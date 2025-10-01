"""Domain models for compile functionality.

This module contains the core data structures used in the compilation process,
following the domain-driven design principles.
"""

from dataclasses import dataclass

from prosemark.domain.models import NodeId


@dataclass(frozen=True)
class CompileRequest:
    """Request to compile a node subtree or all root nodes.

    Attributes:
        node_id: The root node to start compilation from. If None, compile all
            materialized root nodes from the binder.
        include_empty: Whether to include empty nodes (default: False)

    """

    node_id: NodeId | None
    include_empty: bool = False


@dataclass(frozen=True)
class CompileResult:
    """Result of compiling a subtree.

    Attributes:
        content: The concatenated plain text content
        node_count: Number of nodes included in compilation
        total_nodes: Total nodes traversed (including skipped)
        skipped_empty: Number of empty nodes skipped

    """

    content: str
    node_count: int
    total_nodes: int
    skipped_empty: int

    def __post_init__(self) -> None:
        """Validate the result data."""
        if self.node_count < 0:
            raise ValueError('node_count must be non-negative')
        if self.total_nodes < self.node_count:
            raise ValueError('total_nodes must be >= node_count')
        if self.skipped_empty < 0:
            raise ValueError('skipped_empty must be non-negative')
        if self.skipped_empty > self.total_nodes - self.node_count:
            raise ValueError('skipped_empty cannot exceed traversed - included nodes')


@dataclass(frozen=True)
class NodeContent:
    """Represents the content of a single node during traversal.

    Attributes:
        id: Node identifier
        content: The text content of the node
        children: List of child node IDs

    """

    id: NodeId
    content: str
    children: list[NodeId]

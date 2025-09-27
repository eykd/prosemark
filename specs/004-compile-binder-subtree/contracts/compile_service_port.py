"""Contract definition for CompileServicePort.

This module defines the port interface for the compile service,
following hexagonal architecture principles.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from prosemark.domain.models import NodeId


@dataclass(frozen=True)
class CompileRequest:
    """Request to compile a node and its subtree.

    Attributes:
        node_id: The root node to start compilation from
        include_empty: Whether to include empty nodes (default: False)

    """

    node_id: NodeId
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


class CompileServicePort(ABC):
    """Port interface for compile operations.

    This port defines the contract for compiling node subtrees
    into concatenated text output.
    """

    @abstractmethod
    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        """Compile a node and all its descendants into plain text.

        Args:
            request: The compile request with target node and options

        Returns:
            CompileResult containing the concatenated content and statistics

        Raises:
            NodeNotFoundError: If the specified node_id doesn't exist
            CompileError: If compilation fails for any other reason

        """
        ...


class NodeNotFoundError(Exception):
    """Raised when the specified node cannot be found."""

    def __init__(self, node_id: NodeId) -> None:
        self.node_id = node_id
        super().__init__(f'Node not found: {node_id}')


class CompileError(Exception):
    """Base exception for compilation errors."""

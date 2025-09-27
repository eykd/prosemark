"""Use cases for compile functionality.

This module contains the application layer use cases that orchestrate
domain services and handle user interactions.
"""

from prosemark.domain.compile.models import CompileRequest, CompileResult
from prosemark.domain.compile.service import CompileService
from prosemark.ports.compile.service import CompileServicePort, NodeNotFoundError
from prosemark.ports.node_repo import NodeRepo


class CompileSubtreeUseCase(CompileServicePort):
    """Use case for compiling node subtrees.

    This use case orchestrates the domain service and provides
    a clean interface for the adapter layer.
    """

    def __init__(self, node_repo: NodeRepo) -> None:
        """Initialize the use case.

        Args:
            node_repo: Repository for accessing node metadata

        """
        self._compile_service = CompileService(node_repo)

    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        """Compile a node and all its descendants into plain text.

        Args:
            request: The compile request with target node and options

        Returns:
            CompileResult containing the concatenated content and statistics

        Raises:
            NodeNotFoundError: If the specified node_id doesn't exist

        """
        try:
            return self._compile_service.compile_subtree(request)
        except Exception as e:
            # Re-raise as the appropriate port exception
            if 'not found' in str(e).lower():
                raise NodeNotFoundError(request.node_id) from e
            raise

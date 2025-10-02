"""Use cases for compile functionality.

This module contains the application layer use cases that orchestrate
domain services and handle user interactions.
"""

from prosemark.domain.compile.models import CompileRequest, CompileResult
from prosemark.domain.compile.service import CompileService
from prosemark.ports.binder_repo import BinderRepo
from prosemark.ports.compile.service import CompileServicePort, NodeNotFoundError
from prosemark.ports.node_repo import NodeRepo


class CompileSubtreeUseCase(CompileServicePort):
    """Use case for compiling node subtrees or all root nodes.

    This use case orchestrates the domain service and provides
    a clean interface for the adapter layer.
    """

    def __init__(self, node_repo: NodeRepo, binder_repo: BinderRepo) -> None:
        """Initialize the use case.

        Args:
            node_repo: Repository for accessing node metadata
            binder_repo: Repository for accessing binder hierarchy

        """
        self._compile_service = CompileService(node_repo, binder_repo)
        self._binder_repo = binder_repo

    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        """Compile a node subtree or all root nodes.

        Args:
            request: The compile request with target node and options

        Returns:
            CompileResult containing the concatenated content and statistics

        Raises:
            NodeNotFoundError: If the specified node_id doesn't exist

        """
        # Handle None node_id: compile all materialized root nodes
        if request.node_id is None:
            return self._compile_all_roots(request)

        # Existing: Single-node compilation
        try:
            return self._compile_service.compile_subtree(request)
        except Exception as e:
            # Re-raise as the appropriate port exception
            if 'not found' in str(e).lower():
                raise NodeNotFoundError(request.node_id) from e
            raise

    def _compile_all_roots(self, request: CompileRequest) -> CompileResult:
        """Compile all materialized root nodes in binder order.

        Args:
            request: The compile request (node_id must be None)

        Returns:
            CompileResult with aggregated content and statistics

        """
        # Load binder to get root nodes
        binder = self._binder_repo.load()

        # Get materialized root node IDs (filter out placeholders)
        root_node_ids = [item.node_id for item in binder.roots if item.node_id is not None]

        # Handle empty binder (no materialized roots)
        if not root_node_ids:
            return CompileResult(content='', node_count=0, total_nodes=0, skipped_empty=0)

        # Compile each root and accumulate results
        all_content_parts = []
        total_node_count = 0
        total_nodes_all = 0
        total_skipped = 0

        for root_id in root_node_ids:
            # Compile this root subtree
            root_request = CompileRequest(node_id=root_id, include_empty=request.include_empty)
            result = self._compile_service.compile_subtree(root_request)

            # Accumulate results
            all_content_parts.append(result.content)
            total_node_count += result.node_count
            total_nodes_all += result.total_nodes
            total_skipped += result.skipped_empty

        # Combine content with double newlines between roots
        combined_content = '\n\n'.join(all_content_parts)

        return CompileResult(
            content=combined_content,
            node_count=total_node_count,
            total_nodes=total_nodes_all,
            skipped_empty=total_skipped,
        )

"""Core domain service for compiling node subtrees.

This module implements the business logic for traversing
and compiling prosemark node hierarchies.
"""

from collections.abc import Generator
from pathlib import Path

from prosemark.domain.compile.models import CompileRequest, CompileResult, NodeContent
from prosemark.domain.models import NodeId
from prosemark.ports.binder_repo import BinderRepo
from prosemark.ports.node_repo import NodeRepo


class CompileService:
    """Domain service for compiling node subtrees into concatenated text.

    This service implements the core business logic for:
    - Depth-first traversal of node hierarchies
    - Content concatenation with proper formatting
    - Statistics tracking (node counts, empty handling)
    - Memory-efficient streaming processing
    """

    def __init__(self, node_repo: NodeRepo, binder_repo: BinderRepo) -> None:
        """Initialize the compile service.

        Args:
            node_repo: Repository for accessing node data and relationships
            binder_repo: Repository for accessing binder hierarchy

        """
        self._node_repo = node_repo
        self._binder_repo = binder_repo
        # Get project path from node_repo if it has one (for file-based implementations)
        self._project_path = getattr(node_repo, 'project_path', Path.cwd())

    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        """Compile a node and all its descendants into plain text.

        This method traverses the node subtree in depth-first pre-order,
        concatenates content with double newlines, and tracks statistics.

        Args:
            request: The compile request with target node and options

        Returns:
            CompileResult containing the concatenated content and statistics

        Raises:
            NodeNotFoundError: If the specified node_id doesn't exist

        """
        # Handle None node_id case
        if request.node_id is None:
            from prosemark.ports.compile.service import CompileError

            raise CompileError('node_id cannot be None for single-node compilation')

        try:
            # Verify the root node exists by checking if it has frontmatter
            self._node_repo.read_frontmatter(request.node_id)
        except Exception as e:
            from prosemark.ports.compile.service import NodeNotFoundError

            raise NodeNotFoundError(request.node_id) from e

        # Collect content using depth-first traversal
        content_parts = []
        node_count = 0
        total_nodes = 0
        skipped_empty = 0

        for node_content in self._traverse_depth_first(request.node_id):
            total_nodes += 1

            # Apply empty content filtering based on request
            if not node_content.content.strip() and not request.include_empty:
                skipped_empty += 1
                continue

            # Include this node's content
            content_parts.append(node_content.content)
            node_count += 1

        # Join with double newlines
        final_content = '\n\n'.join(content_parts)

        return CompileResult(
            content=final_content, node_count=node_count, total_nodes=total_nodes, skipped_empty=skipped_empty
        )

    def _traverse_depth_first(self, node_id: NodeId) -> Generator[NodeContent, None, None]:
        """Traverse nodes in depth-first pre-order.

        Args:
            node_id: The root node to start traversal from

        Yields:
            NodeContent objects in depth-first pre-order

        Raises:
            NodeNotFoundError: If any required node doesn't exist

        """
        # Verify node exists by reading frontmatter
        try:
            self._node_repo.read_frontmatter(node_id)
        except Exception as e:
            from prosemark.ports.compile.service import NodeNotFoundError

            raise NodeNotFoundError(node_id) from e

        # Read the node content from the draft file
        content = self._read_node_content(node_id)

        # Get children from binder
        children_ids = self._get_children_from_binder(node_id)

        # Yield current node first (pre-order)
        yield NodeContent(id=node_id, content=content, children=children_ids)

        # Recursively traverse children
        for child_id in children_ids:
            try:
                yield from self._traverse_depth_first(child_id)
            except (FileNotFoundError, PermissionError, OSError):  # pragma: no cover
                # Skip missing child nodes rather than failing the entire compilation
                continue
            except Exception as e:  # pragma: no cover
                # Also skip NodeNotFoundError and other exceptions for missing children
                if 'not found' in str(e).lower():
                    continue
                raise

    def _read_node_content(self, node_id: NodeId) -> str:
        """Read the content of a node from its draft file.

        Args:
            node_id: The node to read content from

        Returns:
            The content with frontmatter stripped, empty string if file doesn't exist

        """
        # Construct the draft file path using actual project structure: {node_id}.md
        file_path = self._project_path / f'{node_id}.md'

        try:
            content = file_path.read_text(encoding='utf-8')

            # Remove frontmatter if present
            if content.startswith('---\n'):
                # Find the end of frontmatter
                end_marker = content.find('\n---\n')
                if end_marker != -1:
                    content = content[end_marker + 5 :]  # Skip past the closing ---\n
                else:
                    # Malformed frontmatter, return as-is
                    pass

            return content.strip()

        except (FileNotFoundError, PermissionError, OSError):
            # File doesn't exist or can't be read - return empty content
            return ''

    def _get_children_from_binder(self, node_id: NodeId) -> list[NodeId]:
        """Get the list of child node IDs from the binder hierarchy.

        Args:
            node_id: The parent node to get children for

        Returns:
            List of child node IDs in binder order, empty list if node not found or no children

        """
        try:
            # Load the binder and find the item
            binder = self._binder_repo.load()
            item = binder.find_by_id(node_id)

            if item is None:
                return []

            # Extract NodeIds from children, filtering out placeholders
            return [child.node_id for child in item.children if child.node_id is not None]

        except Exception:  # pragma: no cover  # noqa: BLE001
            # Any error in binder loading or traversal - return empty list
            return []

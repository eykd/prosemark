"""Core domain service for compiling node subtrees.

This module implements the business logic for traversing
and compiling prosemark node hierarchies.
"""

import re
from collections.abc import Generator
from pathlib import Path

from prosemark.domain.compile.models import CompileRequest, CompileResult, NodeContent
from prosemark.domain.models import NodeId
from prosemark.ports.node_repo import NodeRepo


class CompileService:
    """Domain service for compiling node subtrees into concatenated text.

    This service implements the core business logic for:
    - Depth-first traversal of node hierarchies
    - Content concatenation with proper formatting
    - Statistics tracking (node counts, empty handling)
    - Memory-efficient streaming processing
    """

    def __init__(self, node_repo: NodeRepo) -> None:
        """Initialize the compile service.

        Args:
            node_repo: Repository for accessing node data and relationships

        """
        self._node_repo = node_repo

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

    def _read_node_content(self, node_id: NodeId) -> str:  # pragma: no cover
        """Read the content of a node from its draft file.

        Args:
            node_id: The node to read content from

        Returns:
            The content with frontmatter stripped, empty string if file doesn't exist

        """
        # Construct the draft file path
        file_path = Path(f'nodes/{node_id}/draft.md')

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

    def _get_children_from_binder(self, node_id: NodeId) -> list[NodeId]:  # pragma: no cover
        """Get the list of child node IDs from the binder file.

        Args:
            node_id: The parent node to get children for

        Returns:
            List of child node IDs in binder order, empty list if no binder or errors

        """
        # Construct the binder file path
        binder_path = Path(f'nodes/{node_id}/binder.yaml')

        try:
            binder_content = binder_path.read_text(encoding='utf-8')

            # Extract node IDs using regex pattern
            # Look for entries like "- 01923456-789a-7123-8abc-def012345678"
            uuid_pattern = r'- ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
            matches = re.findall(uuid_pattern, binder_content)

            return [NodeId(match) for match in matches]

        except (FileNotFoundError, PermissionError, OSError):
            # Binder file doesn't exist or can't be read - return empty list
            return []

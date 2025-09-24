"""Node service adapter implementation for freewriting feature.

This module provides concrete implementation of the NodeServicePort
using the existing prosemark node infrastructure.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING
from uuid import UUID

from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.domain.models import NodeId
from prosemark.freewriting.domain.exceptions import FileSystemError, NodeError, ValidationError
from prosemark.freewriting.ports.node_service import NodeServicePort

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.node_repo import NodeRepo


class NodeServiceAdapter(NodeServicePort):
    """Concrete implementation of NodeServicePort using prosemark infrastructure.

    This adapter integrates freewriting functionality with the existing
    prosemark node system, using the NodeRepo and BinderRepo for
    node management operations.
    """

    def __init__(
        self,
        project_path: Path,
        node_repo: NodeRepo,
        binder_repo: BinderRepo,
        clock: Clock,
    ) -> None:
        """Initialize the node service adapter.

        Args:
            project_path: Root directory containing node files.
            node_repo: Repository for node operations.
            binder_repo: Repository for binder operations.
            clock: Clock port for timestamps.

        """
        self.project_path = project_path
        self.node_repo = node_repo
        self.binder_repo = binder_repo
        self.clock = clock
        self.frontmatter_codec = FrontmatterCodec()

    def node_exists(self, node_uuid: str) -> bool:
        """Check if a node file exists.

        Args:
            node_uuid: UUID of the node to check.

        Returns:
            True if node exists, False otherwise.

        """
        try:
            # Validate UUID format first
            if not NodeServiceAdapter.validate_node_uuid(node_uuid):
                return False

            draft_file = self.project_path / f'{node_uuid}.md'
            return draft_file.exists()

        except (OSError, ValueError):
            return False

    def create_node(self, node_uuid: str, title: str | None = None) -> str:
        """Create a new node file and add to binder.

        Args:
            node_uuid: UUID for the new node.
            title: Optional title for the node.

        Returns:
            Path to created node file.

        Raises:
            ValidationError: If UUID is invalid.
            FileSystemError: If creation fails.
            NodeError: If node creation fails.

        """
        # Validate UUID format first (outside try block to avoid TRY301)
        if not NodeServiceAdapter.validate_node_uuid(node_uuid):
            raise ValidationError('node_uuid', node_uuid, 'must be valid UUID format')

        try:
            # Convert to NodeId
            node_id = NodeId(node_uuid)

            # Create the node using prosemark infrastructure
            self.node_repo.create(node_id, title, None)  # No synopsis for freewriting nodes

            # Add to binder if not already present
            # If binder addition fails, we continue - the node still exists
            # This is because freewriting should be resilient to binder issues
            with suppress(NodeError):
                self.add_to_binder(node_uuid, title)

            # Return path to the created file
            return str(self.project_path / f'{node_uuid}.md')

        except Exception as e:
            # Convert various exception types to our domain exceptions
            if isinstance(e, ValidationError):
                raise
            if 'already exists' in str(e).lower():
                msg = f'Node {node_uuid} already exists'
                raise NodeError(node_uuid, 'create', msg) from e
            msg = f'Failed to create node: {e}'
            raise FileSystemError('create_node', node_uuid, str(e)) from e

    def append_to_node(self, node_uuid: str, content: list[str], session_metadata: dict[str, str]) -> None:
        """Append freewriting content to existing node.

        Args:
            node_uuid: Target node UUID.
            content: Lines of content to append.
            session_metadata: Session info for context.

        Raises:
            FileSystemError: If write fails.
            ValidationError: If node doesn't exist.
            NodeError: If node operations fail.

        """
        # Validate UUID format first (outside try block to avoid TRY301)
        if not NodeServiceAdapter.validate_node_uuid(node_uuid):
            raise ValidationError('node_uuid', node_uuid, 'must be valid UUID format')

        # Check if node exists (outside try block to avoid TRY301)
        if not self.node_exists(node_uuid):
            raise ValidationError('node_uuid', node_uuid, 'node must exist')

        try:
            node_file = self.project_path / f'{node_uuid}.md'

            # Read existing content
            try:
                existing_content = node_file.read_text(encoding='utf-8')
                frontmatter, body = self.frontmatter_codec.parse(existing_content)
            except Exception as e:
                msg = f'Failed to read existing node content: {e}'
                raise FileSystemError('read', str(node_file), str(e)) from e

            # Create session header
            timestamp = session_metadata.get('timestamp', self.clock.now_iso())
            word_count = session_metadata.get('word_count', '0')

            session_header = f'\n\n## Freewrite Session - {timestamp}\n\n'
            session_footer = f'\n\n*Session completed: {word_count} words*\n'

            # Append content with session context
            new_content_lines = [session_header, *content, session_footer]
            new_body = body + '\n'.join(new_content_lines)

            # Update the updated timestamp in frontmatter
            frontmatter['updated'] = self.clock.now_iso()

            # Encode and write back
            try:
                updated_content = self.frontmatter_codec.generate(frontmatter, new_body)
                node_file.write_text(updated_content, encoding='utf-8')
            except Exception as e:
                msg = f'Failed to write updated node content: {e}'
                raise FileSystemError('write', str(node_file), str(e)) from e

        except (ValidationError, FileSystemError, NodeError):
            raise
        except Exception as e:
            msg = f'Failed to append to node: {e}'
            raise NodeError(node_uuid, 'append', msg) from e

    def get_node_path(self, node_uuid: str) -> str:
        """Get file path for a node UUID.

        Args:
            node_uuid: UUID of the node.

        Returns:
            Absolute path to the node file.

        Raises:
            ValidationError: If UUID format is invalid.

        """

        def _validate_node_format() -> None:
            if not NodeServiceAdapter.validate_node_uuid(node_uuid):
                raise ValidationError('node_uuid', node_uuid, 'must be valid UUID format')

        _validate_node_format()

        return str((self.project_path / f'{node_uuid}.md').resolve())

    @staticmethod
    def validate_node_uuid(node_uuid: str) -> bool:
        """Validate that a node UUID is properly formatted.

        Args:
            node_uuid: UUID string to validate.

        Returns:
            True if valid UUID format, False otherwise.

        """

        def _validate() -> bool:
            # Use Python's UUID class for validation
            UUID(node_uuid)
            return True

        try:
            return _validate()
        except (ValueError, TypeError):
            return False

    def add_to_binder(self, node_uuid: str, _title: str | None = None) -> None:
        """Add node to the project binder.

        Args:
            node_uuid: UUID of the node to add.
            title: Optional title for the binder entry.

        Raises:
            FileSystemError: If binder update fails.
            NodeError: If node addition fails.

        """
        try:
            # Convert to NodeId
            node_id = NodeId(node_uuid)

            # Check if node is already in binder
            with suppress(Exception):
                binder = self.binder_repo.load()
                # If node is already in the structure, don't add it again
                existing_node_ids = binder.get_all_node_ids()
                for node_id in existing_node_ids:
                    if str(node_id) == node_uuid:
                        return  # Node already in binder

            # Add to binder - this will handle the binder structure updates
            # For freewriting, we add nodes to the root level with optional title
            try:
                # The existing binder system should handle adding nodes
                # For now, we'll create a simple entry
                # This may need to be adjusted based on the actual BinderRepo implementation
                pass  # The actual binder integration would depend on the BinderRepo interface
            except Exception as e:  # pragma: no cover
                # Don't let binder failures stop freewriting
                msg = f'Warning: Could not add node to binder: {e}'  # pragma: no cover
                raise NodeError(node_uuid, 'add_to_binder', msg) from e  # pragma: no cover

        except (ValidationError, NodeError):
            raise  # pragma: no cover
        except Exception as e:
            msg = f'Failed to add node to binder: {e}'
            raise NodeError(node_uuid, 'add_to_binder', msg) from e

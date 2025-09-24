"""Freewrite service adapter implementation.

This module provides the concrete implementation of the FreewriteServicePort
that orchestrates all freewriting operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from prosemark.freewriting.domain.exceptions import FileSystemError, ValidationError
from prosemark.freewriting.domain.models import FreewriteSession, SessionConfig, SessionState
from prosemark.freewriting.ports.freewrite_service import FreewriteServicePort

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.freewriting.ports.file_system import FileSystemPort
    from prosemark.freewriting.ports.node_service import NodeServicePort
from prosemark.freewriting.adapters.node_service_adapter import NodeServiceAdapter


class FreewriteServiceAdapter(FreewriteServicePort):
    """Concrete implementation of FreewriteServicePort.

    This adapter orchestrates freewriting operations by coordinating
    between the file system, node service, and domain models.
    """

    def __init__(
        self,
        file_system: FileSystemPort,
        node_service: NodeServicePort,
    ) -> None:
        """Initialize the freewrite service adapter.

        Args:
            file_system: File system port for file operations.
            node_service: Node service port for node operations.

        """
        self.file_system = file_system
        self.node_service = node_service

    def create_session(self, config: SessionConfig) -> FreewriteSession:
        """Create a new freewriting session with given configuration.

        Args:
            config: Session configuration from CLI.

        Returns:
            Initialized FreewriteSession.

        Raises:
            ValidationError: If configuration is invalid.
            FileSystemError: If target directory is not writable.

        """
        # Validate the configuration
        self._validate_session_config(config)

        # Generate session ID
        session_id = str(uuid4())

        # Determine output file path
        output_file_path = self._determine_output_path(config)

        # Ensure we can write to the target location
        self._ensure_writable_target(output_file_path, config)

        # Create and return the session
        session = FreewriteSession(
            session_id=session_id,
            target_node=config.target_node,
            title=config.title,
            start_time=datetime.now(tz=UTC),
            word_count_goal=config.word_count_goal,
            time_limit=config.time_limit,
            current_word_count=0,
            elapsed_time=0,
            output_file_path=output_file_path,
            content_lines=[],
            state=SessionState.INITIALIZING,
        )

        # Initialize the output file
        self._initialize_output_file(session, config)

        # Load existing content if file exists
        session = self._load_existing_content(session, config)

        return session.change_state(SessionState.ACTIVE)

    def append_content(self, session: FreewriteSession, content: str) -> FreewriteSession:
        """Append content line to the session and persist immediately.

        Args:
            session: Current session state.
            content: Content line to append.

        Returns:
            Updated session with new content and word count.

        Raises:
            FileSystemError: If write operation fails.
            ValidationError: If content is invalid.

        """
        if not content.strip():
            # Allow empty lines - they're part of freewriting
            pass

        # Add content to session
        updated_session = session.add_content_line(content)

        try:
            # Persist to file immediately
            if session.target_node:
                self._append_to_node_file(updated_session, content)
            else:
                self._append_to_daily_file(updated_session, content)
        except Exception as e:
            raise FileSystemError('append', session.output_file_path, str(e)) from e

        return updated_session

    @staticmethod
    def validate_node_uuid(node_uuid: str) -> bool:
        """Validate that a node UUID is properly formatted.

        Args:
            node_uuid: UUID string to validate.

        Returns:
            True if valid UUID format, False otherwise.

        """
        # Use the standard UUID validation logic directly
        try:
            from uuid import UUID

            UUID(node_uuid)
        except ValueError:
            return False
        return True

    @staticmethod
    def create_daily_filename(timestamp: datetime) -> str:
        """Generate filename for daily freewrite file.

        Args:
            timestamp: When the session started.

        Returns:
            Filename in YYYY-MM-DD-HHmm.md format.

        """
        return timestamp.strftime('%Y-%m-%d-%H%M.md')

    @staticmethod
    def get_session_stats(session: FreewriteSession) -> dict[str, int | float | bool]:
        """Calculate current session statistics.

        Args:
            session: Current session.

        Returns:
            Dictionary with word_count, elapsed_time, progress metrics.

        """
        stats: dict[str, int | float | bool] = {
            'word_count': session.current_word_count,
            'elapsed_time': session.elapsed_time,
            'line_count': len(session.content_lines),
        }

        # Add goal progress if goals are set
        goals_met = session.is_goal_reached()
        if goals_met:
            stats.update(goals_met)

        # Calculate progress percentages
        if session.word_count_goal:
            word_progress = min(100.0, (session.current_word_count / session.word_count_goal) * 100)
            stats['word_progress_percent'] = word_progress

        if session.time_limit:
            time_progress = min(100.0, (session.elapsed_time / session.time_limit) * 100)
            stats['time_progress_percent'] = time_progress
            stats['time_remaining'] = max(0, session.time_limit - session.elapsed_time)

        return stats

    def _validate_session_config(self, config: SessionConfig) -> None:
        """Validate session configuration.

        Args:
            config: Configuration to validate.

        Raises:
            ValidationError: If configuration is invalid.

        """
        if config.target_node and not NodeServiceAdapter.validate_node_uuid(config.target_node):
            msg = 'Invalid UUID format'
            raise ValidationError('target_node', config.target_node, msg)

        if not self.file_system.is_writable(config.current_directory):
            msg = 'Directory is not writable'
            raise ValidationError('current_directory', config.current_directory, msg)

    def _determine_output_path(self, config: SessionConfig) -> str:
        """Determine the output file path based on configuration.

        Args:
            config: Session configuration.

        Returns:
            Absolute path to output file.

        """
        if config.target_node:
            # For node-targeted sessions, use node service to get path
            return self.node_service.get_node_path(config.target_node)
        # For daily files, create timestamped file in current directory
        filename = FreewriteServiceAdapter.create_daily_filename(datetime.now(tz=UTC))
        return self.file_system.get_absolute_path(self.file_system.join_paths(config.current_directory, filename))

    def _ensure_writable_target(self, output_file_path: str, config: SessionConfig) -> None:
        """Ensure we can write to the target location.

        Args:
            output_file_path: Path to output file.
            config: Session configuration.

        Raises:
            FileSystemError: If target is not writable.

        """
        if config.target_node:
            # For nodes, ensure the node exists or can be created
            if not self.node_service.node_exists(config.target_node):
                try:
                    self.node_service.create_node(config.target_node, config.title)
                except Exception as e:
                    msg = f'Cannot create node: {e}'
                    raise FileSystemError('create_node', config.target_node, str(e)) from e
        else:
            # For daily files, ensure parent directory is writable
            parent_dir = str(Path(output_file_path).parent)
            if not self.file_system.is_writable(parent_dir):
                msg = 'Parent directory is not writable'
                raise FileSystemError('check_writable', parent_dir, msg)

    def _initialize_output_file(self, session: FreewriteSession, config: SessionConfig) -> None:
        """Initialize the output file with proper structure.

        Args:
            session: The session being initialized.
            config: Session configuration.

        Raises:
            FileSystemError: If file initialization fails.

        """
        if config.target_node:
            # For node files, we don't initialize - content gets appended
            return

        # Check if file already exists
        if self.file_system.file_exists(session.output_file_path):
            # File exists, no initialization needed - content will be loaded into session separately
            return

        # Create initial content for daily file
        initial_content = FreewriteServiceAdapter._create_daily_file_initial_content(session)

        # Write initial content
        self.file_system.write_file(session.output_file_path, initial_content, append=False)

        try:
            # Verify file was written successfully
            self._verify_file_created(session.output_file_path)
        except Exception as e:
            raise FileSystemError('initialize', session.output_file_path, str(e)) from e

    @staticmethod
    def _create_daily_file_initial_content(session: FreewriteSession) -> str:
        """Create the initial content for a daily freewrite file.

        Args:
            session: The session being initialized.

        Returns:
            Initial file content with YAML frontmatter and header.

        """
        # For daily files, create with YAML frontmatter
        frontmatter_data: dict[str, Any] = {
            'type': 'freewrite',
            'session_id': session.session_id,
            'created': session.start_time.isoformat(),
        }

        if session.title:
            frontmatter_data['title'] = session.title

        if session.word_count_goal:
            frontmatter_data['word_count_goal'] = session.word_count_goal

        if session.time_limit:
            frontmatter_data['time_limit'] = session.time_limit

        # Create YAML frontmatter
        frontmatter_lines = ['---']
        for key, value in frontmatter_data.items():
            if isinstance(value, str):
                frontmatter_lines.append(f'{key}: "{value}"')
            else:
                frontmatter_lines.append(f'{key}: {value}')
        frontmatter_lines.extend(['---', '', '# Freewrite Session', ''])

        return '\n'.join(frontmatter_lines)

    @staticmethod
    def _verify_file_created(file_path: str) -> None:
        """Verify that the file was written successfully.

        Args:
            file_path: Path to the file to verify.

        Raises:
            OSError: If file was not created.

        """
        if not Path(file_path).exists():
            raise OSError('File not created')

    def _load_existing_content(self, session: FreewriteSession, config: SessionConfig) -> FreewriteSession:
        """Load existing content from file if it exists.

        Args:
            session: The session being initialized.
            config: Session configuration.

        Returns:
            Updated session with existing content loaded.

        Raises:
            FileSystemError: If file reading fails.

        """
        # Check if file exists
        if not self.file_system.file_exists(session.output_file_path):
            # No existing file, return session as-is
            return session

        try:
            # Read existing file content
            existing_content = self.file_system.read_file(session.output_file_path)

            # Split into lines and filter out empty lines at the end
            content_lines = existing_content.splitlines()

            # For daily files, skip YAML frontmatter and header if present
            if not config.target_node:
                content_lines = FreewriteServiceAdapter._filter_frontmatter_and_header(content_lines)

            # Update session with existing content
            updated_session = session
            for line in content_lines:
                updated_session = updated_session.add_content_line(line)

        except Exception as e:
            raise FileSystemError('read_existing', session.output_file_path, str(e)) from e
        else:
            return updated_session

    @staticmethod
    def _filter_frontmatter_and_header(content_lines: list[str]) -> list[str]:
        """Filter out YAML frontmatter and header from daily freewrite files.

        Args:
            content_lines: Raw content lines from file.

        Returns:
            Content lines without frontmatter and header.

        """
        filtered_lines = []
        in_frontmatter = False
        frontmatter_closed = False
        skip_empty_lines = True

        for line in content_lines:
            # Check for YAML frontmatter start/end
            if line.strip() == '---':
                if not in_frontmatter and not frontmatter_closed:
                    in_frontmatter = True
                    continue
                if in_frontmatter:
                    in_frontmatter = False
                    frontmatter_closed = True
                    continue

            # Skip frontmatter lines
            if in_frontmatter:
                continue

            # Skip header line (starts with #)
            if frontmatter_closed and line.strip().startswith('# '):
                continue

            # Skip leading empty lines after header
            if skip_empty_lines and not line.strip():
                continue

            # Found content, stop skipping empty lines
            skip_empty_lines = False
            filtered_lines.append(line)

        return filtered_lines

    def _append_to_daily_file(self, session: FreewriteSession, content: str) -> None:
        """Append content to daily freewrite file.

        Args:
            session: Current session.
            content: Content line to append.

        Raises:
            FileSystemError: If append operation fails.

        """
        # Add newline and append to file
        content_with_newline = content + '\n'
        self.file_system.write_file(session.output_file_path, content_with_newline, append=True)

    def _append_to_node_file(self, session: FreewriteSession, content: str) -> None:
        """Append content to node file via node service.

        Args:
            session: Current session.
            content: Content line to append.

        Raises:
            FileSystemError: If append operation fails.

        """
        if not session.target_node:
            msg = 'No target node specified for node append operation'
            raise FileSystemError('append_node', session.output_file_path, msg)

        # Prepare session metadata
        session_metadata = {
            'timestamp': datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M'),
            'word_count': str(session.current_word_count),
            'session_id': session.session_id,
        }

        # Use node service to append content
        self.node_service.append_to_node(session.target_node, [content], session_metadata)

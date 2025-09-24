"""Domain models for the freewriting feature.

This module contains the core domain models that represent the business entities
and concepts for the write-only freewriting interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from uuid import UUID


class SessionState(Enum):
    """Possible states of a freewriting session."""

    INITIALIZING = 'initializing'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'


@dataclass(frozen=True)
class FreewriteSession:
    """Represents a single freewriting session with metadata and configuration.

    This is the core domain model that tracks all aspects of a user's
    freewriting session, from configuration to real-time progress.
    """

    session_id: str
    target_node: str | None
    title: str | None
    start_time: datetime
    word_count_goal: int | None
    time_limit: int | None
    current_word_count: int
    elapsed_time: int
    output_file_path: str
    content_lines: list[str] = field(default_factory=list)
    state: SessionState = SessionState.INITIALIZING

    def __post_init__(self) -> None:
        """Validate the session data after initialization."""
        self._validate_session_id()
        self._validate_target_node()
        self._validate_start_time()
        self._validate_goals()
        self._validate_counters()
        self._validate_file_path()

    def _validate_session_id(self) -> None:
        """Validate that session_id is a proper UUID."""
        try:
            UUID(self.session_id)
        except ValueError as e:
            msg = f'Invalid session_id format: {self.session_id}'
            raise ValueError(msg) from e

    def _validate_target_node(self) -> None:
        """Validate target_node is a proper UUID format if provided."""
        if self.target_node is not None:
            try:
                UUID(self.target_node)
            except ValueError as e:
                msg = f'Invalid target_node UUID format: {self.target_node}'
                raise ValueError(msg) from e

    def _validate_start_time(self) -> None:
        """Validate start_time is not in the future."""
        now = datetime.now(tz=self.start_time.tzinfo)
        if self.start_time > now:
            msg = f'start_time cannot be in the future: {self.start_time} > {now}'
            raise ValueError(msg)

    def _validate_goals(self) -> None:
        """Validate word_count_goal and time_limit are positive if set."""
        if self.word_count_goal is not None and self.word_count_goal <= 0:
            msg = f'word_count_goal must be positive: {self.word_count_goal}'
            raise ValueError(msg)

        if self.time_limit is not None and self.time_limit <= 0:
            msg = f'time_limit must be positive: {self.time_limit}'
            raise ValueError(msg)

    def _validate_counters(self) -> None:
        """Validate current_word_count and elapsed_time are non-negative."""
        if self.current_word_count < 0:
            msg = f'current_word_count cannot be negative: {self.current_word_count}'
            raise ValueError(msg)

        if self.elapsed_time < 0:
            msg = f'elapsed_time cannot be negative: {self.elapsed_time}'
            raise ValueError(msg)

    def _validate_file_path(self) -> None:
        """Validate output_file_path is a valid file path."""
        try:
            Path(self.output_file_path)
        except (OSError, ValueError) as e:  # pragma: no cover
            msg = f'Invalid output_file_path: {self.output_file_path}'
            raise ValueError(msg) from e  # pragma: no cover

    def calculate_word_count(self) -> int:
        """Calculate total word count from content lines.

        Returns:
            Total number of words across all content lines.

        """
        total_words = 0
        for line in self.content_lines:
            # Use simple whitespace splitting for word counting
            words = line.split()
            total_words += len(words)
        return total_words

    def add_content_line(self, content: str) -> FreewriteSession:
        """Add a new content line and return updated session.

        Args:
            content: The content line to add (preserves exact input).

        Returns:
            New FreewriteSession with the added content line.

        """
        new_content_lines = list(self.content_lines)
        new_content_lines.append(content)

        # Calculate new word count
        line_words = len(content.split())
        new_word_count = self.current_word_count + line_words

        # Return new immutable instance
        return FreewriteSession(
            session_id=self.session_id,
            target_node=self.target_node,
            title=self.title,
            start_time=self.start_time,
            word_count_goal=self.word_count_goal,
            time_limit=self.time_limit,
            current_word_count=new_word_count,
            elapsed_time=self.elapsed_time,
            output_file_path=self.output_file_path,
            content_lines=new_content_lines,
            state=self.state,
        )

    def update_elapsed_time(self, elapsed_seconds: int) -> FreewriteSession:
        """Update elapsed time and return new session.

        Args:
            elapsed_seconds: New elapsed time in seconds.

        Returns:
            New FreewriteSession with updated elapsed time.

        """
        if elapsed_seconds < 0:
            msg = f'elapsed_seconds cannot be negative: {elapsed_seconds}'
            raise ValueError(msg)

        return FreewriteSession(
            session_id=self.session_id,
            target_node=self.target_node,
            title=self.title,
            start_time=self.start_time,
            word_count_goal=self.word_count_goal,
            time_limit=self.time_limit,
            current_word_count=self.current_word_count,
            elapsed_time=elapsed_seconds,
            output_file_path=self.output_file_path,
            content_lines=self.content_lines,
            state=self.state,
        )

    def change_state(self, new_state: SessionState) -> FreewriteSession:
        """Change session state and return new session.

        Args:
            new_state: The new state to transition to.

        Returns:
            New FreewriteSession with updated state.

        """
        return FreewriteSession(
            session_id=self.session_id,
            target_node=self.target_node,
            title=self.title,
            start_time=self.start_time,
            word_count_goal=self.word_count_goal,
            time_limit=self.time_limit,
            current_word_count=self.current_word_count,
            elapsed_time=self.elapsed_time,
            output_file_path=self.output_file_path,
            content_lines=self.content_lines,
            state=new_state,
        )

    def is_goal_reached(self) -> dict[str, bool]:
        """Check if session goals have been reached.

        Returns:
            Dictionary indicating which goals have been reached.

        """
        result = {}

        if self.word_count_goal is not None:
            result['word_count'] = self.current_word_count >= self.word_count_goal

        if self.time_limit is not None:
            result['time_limit'] = self.elapsed_time >= self.time_limit

        return result


@dataclass(frozen=True)
class SessionConfig:
    """Configuration for a freewriting session.

    This model represents the user's configuration choices that
    determine how a freewriting session should behave.
    """

    target_node: str | None = None
    title: str | None = None
    word_count_goal: int | None = None
    time_limit: int | None = None
    theme: str = 'dark'
    current_directory: str = '.'

    def __post_init__(self) -> None:
        """Validate the session configuration."""
        self._validate_target_node()
        self._validate_goals()
        self._validate_directory()

    def _validate_target_node(self) -> None:
        """Validate target_node is a proper UUID format if provided."""
        if self.target_node is not None:
            try:
                UUID(self.target_node)
            except ValueError as e:
                msg = f'Invalid target_node UUID format: {self.target_node}'
                raise ValueError(msg) from e

    def _validate_goals(self) -> None:
        """Validate goals are positive if provided."""
        if self.word_count_goal is not None and self.word_count_goal <= 0:
            msg = f'word_count_goal must be positive: {self.word_count_goal}'
            raise ValueError(msg)

        if self.time_limit is not None and self.time_limit <= 0:
            msg = f'time_limit must be positive: {self.time_limit}'
            raise ValueError(msg)

    def _validate_directory(self) -> None:
        """Validate current_directory is a valid path."""
        try:
            Path(self.current_directory)
        except (OSError, ValueError) as e:  # pragma: no cover
            msg = f'Invalid current_directory: {self.current_directory}'
            raise ValueError(msg) from e  # pragma: no cover

    def has_goals(self) -> bool:
        """Check if this configuration has any goals set.

        Returns:
            True if word count goal or time limit is set.

        """
        return self.word_count_goal is not None or self.time_limit is not None

    def is_node_targeted(self) -> bool:
        """Check if this configuration targets a specific node.

        Returns:
            True if target_node is specified.

        """
        return self.target_node is not None


@dataclass(frozen=True)
class FreewriteContent:
    """Represents a single line of content entered by the user.

    This model tracks individual content entries with their
    metadata for detailed session analysis.
    """

    content: str
    timestamp: datetime
    line_number: int
    word_count: int

    def __post_init__(self) -> None:
        """Validate the content data."""
        self._validate_line_number()
        self._validate_word_count()

    def _validate_line_number(self) -> None:
        """Validate line_number is positive."""
        if self.line_number <= 0:
            msg = f'line_number must be positive: {self.line_number}'
            raise ValueError(msg)

    def _validate_word_count(self) -> None:
        """Validate word_count matches actual content."""
        actual_word_count = len(self.content.split())
        if self.word_count != actual_word_count:
            msg = f'word_count mismatch: expected {actual_word_count}, got {self.word_count}'
            raise ValueError(msg)

    @classmethod
    def from_content(cls, content: str, line_number: int, timestamp: datetime | None = None) -> FreewriteContent:
        """Create FreewriteContent from content string.

        Args:
            content: The actual text content.
            line_number: Sequential line number.
            timestamp: When content was entered (defaults to now).

        Returns:
            New FreewriteContent instance.

        """
        if timestamp is None:
            timestamp = datetime.now(tz=UTC)

        word_count = len(content.split())

        return cls(
            content=content,
            timestamp=timestamp,
            line_number=line_number,
            word_count=word_count,
        )


@dataclass(frozen=True)
class FileTarget:
    """Represents the destination file for freewriting content.

    This model encapsulates the details about where content
    should be written and how it should be formatted.
    """

    file_path: str
    is_node: bool
    node_uuid: str | None
    created_timestamp: datetime
    file_format: str = 'markdown'

    def __post_init__(self) -> None:
        """Validate the file target data."""
        self._validate_file_path()
        self._validate_node_consistency()
        self._validate_file_format()

    def _validate_file_path(self) -> None:
        """Validate file_path is a valid path."""
        try:
            Path(self.file_path)
        except (OSError, ValueError) as e:  # pragma: no cover
            msg = f'Invalid file_path: {self.file_path}'
            raise ValueError(msg) from e  # pragma: no cover

    def _validate_node_consistency(self) -> None:
        """Validate node_uuid is provided if is_node is True."""
        if self.is_node and self.node_uuid is None:
            msg = 'node_uuid is required when is_node is True'
            raise ValueError(msg)

        if self.is_node and self.node_uuid is not None:
            try:
                UUID(self.node_uuid)
            except ValueError as e:
                msg = f'Invalid node_uuid format: {self.node_uuid}'
                raise ValueError(msg) from e

    def _validate_file_format(self) -> None:
        """Validate file_format is supported."""
        if self.file_format != 'markdown':
            msg = f'Unsupported file_format: {self.file_format}'
            raise ValueError(msg)

    @classmethod
    def for_daily_file(cls, file_path: str) -> FileTarget:
        """Create FileTarget for a daily freewrite file.

        Args:
            file_path: Path to the daily file.

        Returns:
            New FileTarget configured for daily file.

        """
        return cls(
            file_path=file_path,
            is_node=False,
            node_uuid=None,
            created_timestamp=datetime.now(tz=UTC),
            file_format='markdown',
        )

    @classmethod
    def for_node(cls, file_path: str, node_uuid: str) -> FileTarget:
        """Create FileTarget for a node file.

        Args:
            file_path: Path to the node file.
            node_uuid: UUID of the target node.

        Returns:
            New FileTarget configured for node file.

        """
        return cls(
            file_path=file_path,
            is_node=True,
            node_uuid=node_uuid,
            created_timestamp=datetime.now(tz=UTC),
            file_format='markdown',
        )

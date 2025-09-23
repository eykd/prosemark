# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Fake storage adapter for testing binder persistence."""

from typing import TYPE_CHECKING

from prosemark.exceptions import BinderNotFoundError
from prosemark.ports.binder_repo import BinderRepo

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder


class FakeBinderRepo(BinderRepo):
    """In-memory fake implementation of BinderRepo for testing.

    Provides minimal binder storage functionality using memory storage
    instead of filesystem. Maintains the same interface contract as
    production implementations but without actual file I/O.

    This fake stores a single binder in memory and tracks whether
    a binder has been saved. The load operation returns the saved
    binder or raises BinderNotFoundError if nothing has been saved.

    Examples:
        >>> from prosemark.domain.models import Binder
        >>> repo = FakeBinderRepo()
        >>> binder = Binder(roots=[])
        >>> repo.save(binder)
        >>> loaded = repo.load()
        >>> loaded.roots == []
        True

    """

    def __init__(self) -> None:
        """Initialize empty fake repository."""
        self._binder: Binder | None = None

    def load(self) -> 'Binder':
        """Load binder from memory storage.

        Returns:
            The previously saved Binder instance.

        Raises:
            BinderNotFoundError: If no binder has been saved yet.

        """
        if self._binder is None:  # pragma: no cover
            msg = 'No binder has been saved'
            raise BinderNotFoundError(msg)  # pragma: no cover
        return self._binder

    def save(self, binder: 'Binder') -> None:
        """Save binder to memory storage.

        Args:
            binder: The Binder instance to store in memory.

        """
        self._binder = binder

    def set_binder(self, binder: 'Binder') -> None:
        """Set binder directly for testing convenience.

        This is a test-specific method that allows direct setup
        of the binder state without going through the save() method.

        Args:
            binder: The Binder instance to store in memory.

        """
        self._binder = binder

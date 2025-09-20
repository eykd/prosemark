"""BinderRepo abstract base class for binder persistence operations."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder


class BinderRepo(ABC):
    """Abstract base class for binder persistence operations.

    Implementations must preserve text outside managed blocks during
    round-trip operations (load -> save -> load). This ensures that any
    content in binder files that is not part of the managed hierarchy
    is maintained through save/load cycles.

    The BinderRepo serves as a critical port in the hexagonal architecture,
    isolating domain logic from storage concerns and enabling different
    storage mechanisms while maintaining consistent behavior.
    """

    @abstractmethod
    def load(self) -> 'Binder':
        """Load binder from storage.

        Returns:
            The loaded Binder aggregate.

        Raises:
            BinderNotFoundError: If binder file doesn't exist.
            FileSystemError: If file cannot be read.
            BinderIntegrityError: If binder data is corrupted.

        """

    @abstractmethod
    def save(self, binder: 'Binder') -> None:
        """Save binder to storage.

        Args:
            binder: The Binder aggregate to persist.

        Raises:
            FileSystemError: If file cannot be written.

        """

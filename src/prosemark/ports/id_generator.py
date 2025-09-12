"""Abstract base class for ID generators."""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IdGeneratorProtocol(Protocol):
    """Protocol defining the interface for ID generators."""

    @abstractmethod
    def new(self) -> Any:  # noqa: ANN401
        """Generate a new unique identifier.

        Returns:
            A unique identifier of any type.

        """
        ...  # pragma: no cover


class IdGenerator(ABC):  # pragma: no cover
    """Abstract base class for ID generators.

    Defines the minimal interface for generating unique identifiers.
    Subclasses must implement the new() method to provide concrete ID generation.
    """

    @abstractmethod
    def new(self) -> Any:  # noqa: ANN401
        """Generate a new unique identifier.

        This method must be implemented by concrete subclasses.

        Returns:
            A unique identifier of any type.

        Raises:
            NotImplementedError: If not implemented by a concrete subclass.

        """
        raise NotImplementedError('Subclasses must implement the new() method')  # pragma: no cover

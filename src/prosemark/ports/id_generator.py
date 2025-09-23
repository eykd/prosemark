"""Abstract base class for ID generators."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import NodeId


class IdGenerator(ABC):
    """Abstract base class for ID generators.

    Defines the minimal interface for generating unique identifiers
    for nodes in the system. All implementations must generate stable,
    unique NodeId values.

    The IdGenerator enables:
    * Stable, unique identifiers for nodes
    * Testable ID generation through dependency injection
    * Support for different ID strategies (UUIDv7 for production, sequential for tests)
    * Hexagonal architecture compliance by isolating system concerns

    Examples:
        >>> class TestIdGenerator(IdGenerator):
        ...     def new(self) -> NodeId:
        ...         return NodeId('0192f0c1-2345-7123-8abc-def012345678')
        >>> generator = TestIdGenerator()
        >>> node_id = generator.new()
        >>> isinstance(node_id, NodeId)
        True

    """

    @abstractmethod
    def new(self) -> 'NodeId':
        """Generate a new unique NodeId.

        This method must be implemented by concrete subclasses to provide
        specific ID generation strategies (UUIDv7, sequential, etc.).

        Returns:
            A new unique NodeId instance

        Raises:
            NotImplementedError: If not implemented by a concrete subclass

        """
        msg = 'Subclasses must implement the new() method'  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

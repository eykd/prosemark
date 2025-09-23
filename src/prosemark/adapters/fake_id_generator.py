# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""In-memory fake implementation of IdGenerator for testing."""

from prosemark.domain.models import NodeId
from prosemark.ports.id_generator import IdGenerator


class FakeIdGenerator(IdGenerator):
    """Deterministic fake implementation of IdGenerator for testing.

    Provides predictable ID generation for testing purposes using a sequence
    of predefined UUIDv7 values. This enables deterministic test behavior
    while maintaining the same interface contract as production implementations.

    The generator cycles through a predefined list of valid UUIDv7 identifiers,
    allowing tests to predict what IDs will be generated and assert on specific
    values.

    Examples:
        >>> generator = FakeIdGenerator()
        >>> node_id1 = generator.new()
        >>> node_id2 = generator.new()
        >>> str(node_id1)
        '0192f0c1-0000-7000-8000-000000000001'
        >>> str(node_id2)
        '0192f0c1-0000-7000-8000-000000000002'

        >>> # Custom sequence
        >>> custom_ids = ['0192f0c1-1111-7000-8000-000000000001']
        >>> generator = FakeIdGenerator(custom_ids)
        >>> str(generator.new())
        '0192f0c1-1111-7000-8000-000000000001'

    """

    def __init__(self, ids: list[str] | None = None) -> None:
        """Initialize fake generator with predefined ID sequence.

        Args:
            ids: Optional list of UUIDv7 strings to use as the sequence.
                 If None, uses a default sequence of test IDs.

        """
        if ids is None:  # pragma: no cover
            # Default sequence of valid UUIDv7 test identifiers
            ids = [
                '0192f0c1-0000-7000-8000-000000000001',
                '0192f0c1-0000-7000-8000-000000000002',
                '0192f0c1-0000-7000-8000-000000000003',
                '0192f0c1-0000-7000-8000-000000000004',
                '0192f0c1-0000-7000-8000-000000000005',
                '0192f0c1-0000-7000-8000-000000000006',
                '0192f0c1-0000-7000-8000-000000000007',
                '0192f0c1-0000-7000-8000-000000000008',
                '0192f0c1-0000-7000-8000-000000000009',
                '0192f0c1-0000-7000-8000-000000000010',
            ]

        self._ids = ids
        self._current_index = 0

    def new(self) -> NodeId:
        """Generate the next NodeId in the sequence.

        Returns:
            The next NodeId from the predefined sequence

        Raises:
            IndexError: If all IDs in the sequence have been used

        """
        if self._current_index >= len(self._ids):
            msg = 'All predefined IDs have been used'  # pragma: no cover
            raise IndexError(msg)  # pragma: no cover

        id_string = self._ids[self._current_index]
        self._current_index += 1
        return NodeId(id_string)

    def reset(self) -> None:  # pragma: no cover
        """Reset the generator to start from the beginning of the sequence.

        Useful for resetting state between test cases.

        """
        self._current_index = 0

    def remaining_count(self) -> int:  # pragma: no cover
        """Get the number of IDs remaining in the sequence.

        Returns:
            Number of IDs that can still be generated

        """
        return len(self._ids) - self._current_index

    def generated_count(self) -> int:
        """Get the number of IDs that have been generated.

        Returns:
            Number of IDs that have been generated from this generator

        """
        return self._current_index

    def peek_next(self) -> str:  # pragma: no cover
        """Peek at the next ID without consuming it.

        Returns:
            The next ID string that would be generated

        Raises:
            IndexError: If no more IDs are available

        """
        if self._current_index >= len(self._ids):
            msg = 'No more IDs available'
            raise IndexError(msg)  # pragma: no cover

        return self._ids[self._current_index]

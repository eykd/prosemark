"""Tests for the Clock abstract base class."""

import inspect
from abc import ABC

import pytest

from prosemark.ports.clock import Clock


class TestClock:
    """Tests for Clock abstract base class."""

    def test_clock_is_abstract_base_class(self) -> None:
        """Test that Clock is an abstract base class."""
        assert issubclass(Clock, ABC)
        assert Clock.__abstractmethods__ == frozenset(['now_iso'])

    def test_clock_now_iso_method_signature(self) -> None:
        """Test that Clock defines now_iso() method with correct signature."""
        # Arrange: Clock abstract base class
        method = Clock.now_iso
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: now_iso() -> str (no parameters except self, returns string)
        assert parameters == ['self'], f"Expected ['self'], got {parameters}"
        assert return_annotation is str, f'Expected str return type, got {return_annotation}'

    def test_clock_returns_string(self) -> None:
        """Test that Clock now_iso method has proper return type annotation."""
        # Arrange: Clock protocol method
        method = Clock.now_iso
        signature = inspect.signature(method)

        # Act: Check return type annotation
        return_annotation = signature.return_annotation

        # Assert: Returns str (ISO8601 formatted timestamp)
        assert return_annotation is str

    def test_clock_abstract_base_class_supports_mocking(self) -> None:
        """Test that Clock abstract base class enables deterministic testing through subclassing."""

        # Arrange: Mock Clock implementation with fixed timestamp
        class MockClock(Clock):
            def now_iso(self) -> str:
                return '2025-09-10T17:00:00Z'

        # Act: Use mock in application layer code
        mock_clock = MockClock()
        timestamp = mock_clock.now_iso()

        # Assert: Abstract base class enables deterministic time for tests
        assert timestamp == '2025-09-10T17:00:00Z'
        assert isinstance(mock_clock, Clock)

    def test_clock_abstract_base_class_runtime_checkable(self) -> None:
        """Test that Clock abstract base class supports runtime type checking."""

        # Arrange: Concrete implementation class
        class SystemClock(Clock):
            def now_iso(self) -> str:
                return '2025-09-10T17:00:00Z'

        instance = SystemClock()

        # Act: Check isinstance() with Clock abstract base class
        result = isinstance(instance, Clock)

        # Assert: Runtime type checking works correctly
        assert result is True

    def test_clock_abstract_base_class_minimal_interface(self) -> None:
        """Test that Clock abstract base class has minimal interface."""
        # Arrange: Clock abstract methods
        abstract_methods = Clock.__abstractmethods__

        # Act: Count number of required methods
        method_count = len(abstract_methods)

        # Assert: Only now_iso() method required (minimal interface)
        assert method_count == 1
        assert 'now_iso' in abstract_methods

    def test_clock_cannot_be_instantiated_directly(self) -> None:
        """Test that Clock abstract base class cannot be instantiated directly."""
        # Act & Assert: Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError, match="Can't instantiate abstract class Clock"):
            Clock()  # type: ignore[abstract]

    def test_clock_requires_now_iso_implementation(self) -> None:
        """Test that Clock subclasses must implement now_iso method."""

        # Arrange: Incomplete implementation missing now_iso
        class IncompleteClock(Clock):
            pass  # Missing now_iso implementation

        # Act & Assert: Should raise TypeError when instantiating
        with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteClock"):
            IncompleteClock()  # type: ignore[abstract]

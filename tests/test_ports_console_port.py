"""Tests for the ConsolePort abstract base class."""

import inspect
from abc import ABC
from typing import TYPE_CHECKING

import pytest

from prosemark.ports.console_port import ConsolePort

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.domain.models import Binder


class TestConsolePort:
    """Tests for ConsolePort abstract base class."""

    def test_console_port_is_abstract_base_class(self) -> None:
        """Test that ConsolePort is an abstract base class."""
        assert issubclass(ConsolePort, ABC)
        assert ConsolePort.__abstractmethods__ == frozenset(['print'])

    def test_console_port_print_method_signature(self) -> None:
        """Test that ConsolePort defines print() method with correct signature."""
        # Arrange: ConsolePort abstract base class
        method = ConsolePort.print
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: print(msg: str) -> None
        assert parameters == ['self', 'msg'], f"Expected ['self', 'msg'], got {parameters}"
        assert return_annotation is None, f'Expected None return type, got {return_annotation}'

    def test_console_port_accepts_string_message(self) -> None:
        """Test that ConsolePort print method accepts string message parameter."""
        # Arrange: ConsolePort protocol method
        method = ConsolePort.print
        signature = inspect.signature(method)

        # Act: Check msg parameter type annotation
        msg_param = signature.parameters['msg']
        param_annotation = msg_param.annotation

        # Assert: Accepts str parameter for formatted content
        assert param_annotation is str

    def test_console_port_abstract_base_class_supports_mocking(self) -> None:
        """Test that ConsolePort abstract base class enables output verification through subclassing."""

        # Arrange: Mock ConsolePort implementation
        class MockConsolePort(ConsolePort):
            def __init__(self) -> None:
                self.messages: list[str] = []

            def print(self, msg: str) -> None:
                self.messages.append(msg)

            def print_tree(self, binder: 'Binder') -> None:
                pass

        # Act: Use mock in application layer code
        mock_console = MockConsolePort()
        mock_console.print('Test message')

        # Assert: Abstract base class enables output verification in tests
        assert mock_console.messages == ['Test message']
        assert isinstance(mock_console, ConsolePort)

    def test_console_port_abstract_base_class_runtime_checkable(self) -> None:
        """Test that ConsolePort abstract base class supports runtime type checking."""

        # Arrange: Concrete implementation class
        class StdoutConsolePort(ConsolePort):
            def print(self, msg: str) -> None:
                pass

            def print_tree(self, binder: 'Binder') -> None:
                pass

        instance = StdoutConsolePort()

        # Act: Check isinstance() with ConsolePort abstract base class
        result = isinstance(instance, ConsolePort)

        # Assert: Runtime type checking works correctly
        assert result is True

    def test_console_port_abstract_base_class_minimal_interface(self) -> None:
        """Test that ConsolePort abstract base class has minimal interface."""
        # Arrange: ConsolePort abstract methods
        abstract_methods = ConsolePort.__abstractmethods__

        # Act: Count number of required methods
        method_count = len(abstract_methods)

        # Assert: Only print() method required (minimal interface)
        assert method_count == 1
        assert 'print' in abstract_methods

    def test_console_port_cannot_be_instantiated_directly(self) -> None:
        """Test that ConsolePort abstract base class cannot be instantiated directly."""
        # Act & Assert: Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError, match="Can't instantiate abstract class ConsolePort"):
            ConsolePort()  # type: ignore[abstract]

    def test_console_port_requires_print_implementation(self) -> None:
        """Test that ConsolePort subclasses must implement print method."""

        # Arrange: Incomplete implementation missing print
        class IncompleteConsolePort(ConsolePort):
            pass  # Missing print implementation

        # Act & Assert: Should raise TypeError when instantiating
        with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteConsolePort"):
            IncompleteConsolePort()  # type: ignore[abstract]

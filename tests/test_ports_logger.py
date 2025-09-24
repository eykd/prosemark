"""Tests for the Logger abstract base class."""
# ruff: noqa: ANN401 - Any types intentional for testing Logger ABC interface

import inspect
from abc import ABC
from typing import Any
from unittest.mock import MagicMock

import pytest

from prosemark.ports.logger import Logger


class TestLogger:
    """Tests for Logger abstract base class."""

    def test_logger_is_abstract_base_class(self) -> None:
        """Test that Logger is an abstract base class."""
        assert issubclass(Logger, ABC)
        assert Logger.__abstractmethods__ == frozenset(['debug', 'info', 'warning', 'error', 'exception'])

    def test_logger_debug_method_signature(self) -> None:
        """Test that Logger defines debug() method with correct signature."""
        # Arrange: Logger abstract base class
        method = Logger.debug
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: debug(self, msg: Any, *args: Any, **kwargs: Any) -> None
        assert parameters == ['self', 'msg', 'args', 'kwargs'], (
            f"Expected ['self', 'msg', 'args', 'kwargs'], got {parameters}"
        )
        assert return_annotation is None, f'Expected None return type, got {return_annotation}'

    def test_logger_info_method_signature(self) -> None:
        """Test that Logger defines info() method with correct signature."""
        # Arrange: Logger abstract base class
        method = Logger.info
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: info(self, msg: Any, *args: Any, **kwargs: Any) -> None
        assert parameters == ['self', 'msg', 'args', 'kwargs'], (
            f"Expected ['self', 'msg', 'args', 'kwargs'], got {parameters}"
        )
        assert return_annotation is None, f'Expected None return type, got {return_annotation}'

    def test_logger_warning_method_signature(self) -> None:
        """Test that Logger defines warning() method with correct signature."""
        # Arrange: Logger abstract base class
        method = Logger.warning
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: warning(self, msg: Any, *args: Any, **kwargs: Any) -> None
        assert parameters == ['self', 'msg', 'args', 'kwargs'], (
            f"Expected ['self', 'msg', 'args', 'kwargs'], got {parameters}"
        )
        assert return_annotation is None, f'Expected None return type, got {return_annotation}'

    def test_logger_error_method_signature(self) -> None:
        """Test that Logger defines error() method with correct signature."""
        # Arrange: Logger abstract base class
        method = Logger.error
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: error(self, msg: Any, *args: Any, **kwargs: Any) -> None
        assert parameters == ['self', 'msg', 'args', 'kwargs'], (
            f"Expected ['self', 'msg', 'args', 'kwargs'], got {parameters}"
        )
        assert return_annotation is None, f'Expected None return type, got {return_annotation}'

    def test_logger_exception_method_signature(self) -> None:
        """Test that Logger defines exception() method with correct signature."""
        # Arrange: Logger abstract base class
        method = Logger.exception
        signature = inspect.signature(method)

        # Act: Check method signature
        parameters = list(signature.parameters.keys())
        return_annotation = signature.return_annotation

        # Assert: exception(self, msg: Any, *args: Any, **kwargs: Any) -> None
        assert parameters == ['self', 'msg', 'args', 'kwargs'], (
            f"Expected ['self', 'msg', 'args', 'kwargs'], got {parameters}"
        )
        assert return_annotation is None, f'Expected None return type, got {return_annotation}'

    def test_logger_method_parameter_type_annotations(self) -> None:
        """Test that Logger methods have correct type annotations for parameters."""
        # Arrange: Logger abstract methods
        debug_sig = inspect.signature(Logger.debug)
        info_sig = inspect.signature(Logger.info)
        warning_sig = inspect.signature(Logger.warning)
        error_sig = inspect.signature(Logger.error)
        exception_sig = inspect.signature(Logger.exception)

        # Act: Check msg parameter type annotations
        debug_msg_annotation = debug_sig.parameters['msg'].annotation
        info_msg_annotation = info_sig.parameters['msg'].annotation
        warning_msg_annotation = warning_sig.parameters['msg'].annotation
        error_msg_annotation = error_sig.parameters['msg'].annotation
        exception_msg_annotation = exception_sig.parameters['msg'].annotation

        # Assert: All methods accept object for msg parameter
        assert debug_msg_annotation is object
        assert info_msg_annotation is object
        assert warning_msg_annotation is object
        assert error_msg_annotation is object
        assert exception_msg_annotation is object

    def test_logger_cannot_be_instantiated_directly(self) -> None:
        """Test that Logger abstract base class cannot be instantiated directly."""
        # Act & Assert: Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError, match="Can't instantiate abstract class Logger"):
            Logger()  # type: ignore[abstract]

    def test_logger_requires_all_method_implementations(self) -> None:
        """Test that Logger subclasses must implement all abstract methods."""

        # Arrange: Incomplete implementation missing debug method
        class IncompleteLogger(Logger):
            def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            # Missing debug implementation

        # Act & Assert: Should raise TypeError when instantiating
        with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteLogger"):
            IncompleteLogger()  # type: ignore[abstract]

    def test_logger_abstract_base_class_minimal_interface(self) -> None:
        """Test that Logger abstract base class has exactly four required methods."""
        # Arrange: Logger abstract methods
        abstract_methods = Logger.__abstractmethods__

        # Act: Count number of required methods
        method_count = len(abstract_methods)

        # Assert: Exactly five methods required (debug, info, warning, error, exception)
        assert method_count == 5
        assert 'debug' in abstract_methods
        assert 'info' in abstract_methods
        assert 'warning' in abstract_methods
        assert 'error' in abstract_methods
        assert 'exception' in abstract_methods

    def test_logger_abstract_base_class_runtime_checkable(self) -> None:
        """Test that Logger abstract base class supports runtime type checking."""

        # Arrange: Concrete implementation class
        class TestLogger(Logger):
            def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

            def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                pass

        instance = TestLogger()

        # Act: Check isinstance() with Logger abstract base class
        result = isinstance(instance, Logger)

        # Assert: Runtime type checking works correctly
        assert result is True

    def test_logger_concrete_implementation_works_with_simple_messages(self) -> None:
        """Test that concrete Logger implementation handles simple string messages."""

        # Arrange: Mock Logger implementation for testing
        class MockLogger(Logger):
            def __init__(self) -> None:
                self.debug_messages: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []
                self.info_messages: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []
                self.warning_messages: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []
                self.error_messages: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []
                self.exception_messages: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []

            def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.debug_messages.append((msg, args, kwargs))

            def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.info_messages.append((msg, args, kwargs))

            def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.warning_messages.append((msg, args, kwargs))

            def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.error_messages.append((msg, args, kwargs))

            def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.exception_messages.append((msg, args, kwargs))

        # Act: Use logger with simple messages
        logger = MockLogger()
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')
        logger.error('Exception message')

        # Assert: All log levels capture simple messages correctly
        assert logger.debug_messages == [('Debug message', (), {})]
        assert logger.info_messages == [('Info message', (), {})]
        assert logger.warning_messages == [('Warning message', (), {})]
        assert logger.error_messages == [('Error message', (), {}), ('Exception message', (), {})]
        assert logger.exception_messages == []

    def test_logger_concrete_implementation_works_with_formatted_messages(self) -> None:
        """Test that concrete Logger implementation handles formatted messages with args."""

        # Arrange: Mock Logger implementation for testing
        class MockLogger(Logger):
            def __init__(self) -> None:
                self.messages: list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]] = []

            def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('debug', msg, args, kwargs))

            def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('info', msg, args, kwargs))

            def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('warning', msg, args, kwargs))

            def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('error', msg, args, kwargs))

            def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('exception', msg, args, kwargs))

        # Act: Use logger with formatted messages
        logger = MockLogger()
        logger.debug('Processing node %s', 'node123')
        logger.info('Created node %s with %d items', 'node456', 5)
        logger.warning('Large binder detected: %d items', 1000)
        logger.error('Failed to create node: %s', 'permission denied')
        logger.error('Exception during processing: %s', 'timeout error')

        # Assert: All formatted messages captured with args
        expected_messages: list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]] = [
            ('debug', 'Processing node %s', ('node123',), {}),
            ('info', 'Created node %s with %d items', ('node456', 5), {}),
            ('warning', 'Large binder detected: %d items', (1000,), {}),
            ('error', 'Failed to create node: %s', ('permission denied',), {}),
            ('error', 'Exception during processing: %s', ('timeout error',), {}),
        ]
        assert logger.messages == expected_messages

    def test_logger_concrete_implementation_works_with_keyword_arguments(self) -> None:
        """Test that concrete Logger implementation handles keyword arguments like 'extra'."""

        # Arrange: Mock Logger implementation for testing
        class MockLogger(Logger):
            def __init__(self) -> None:
                self.messages: list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]] = []

            def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('debug', msg, args, kwargs))

            def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('info', msg, args, kwargs))

            def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('warning', msg, args, kwargs))

            def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('error', msg, args, kwargs))

            def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.messages.append(('exception', msg, args, kwargs))

        # Act: Use logger with keyword arguments
        logger = MockLogger()
        logger.debug('Validation result', extra={'node_id': 'node123'})
        logger.info('Node added to binder', extra={'node_id': 'node456', 'parent_id': 'parent789'})
        logger.warning('Deprecated feature used', extra={'feature': 'old_api'})
        logger.error('Node creation failed', extra={'node_id': 'node999', 'error': 'disk full'})
        logger.error('Exception in handler', extra={'handler': 'auth', 'error_code': 500})

        # Assert: All keyword arguments captured correctly
        expected_messages: list[tuple[str, Any, tuple[Any, ...], dict[str, Any]]] = [
            ('debug', 'Validation result', (), {'extra': {'node_id': 'node123'}}),
            ('info', 'Node added to binder', (), {'extra': {'node_id': 'node456', 'parent_id': 'parent789'}}),
            ('warning', 'Deprecated feature used', (), {'extra': {'feature': 'old_api'}}),
            ('error', 'Node creation failed', (), {'extra': {'node_id': 'node999', 'error': 'disk full'}}),
            ('error', 'Exception in handler', (), {'extra': {'handler': 'auth', 'error_code': 500}}),
        ]
        assert logger.messages == expected_messages

    def test_logger_supports_mocking_for_testing_application_code(self) -> None:
        """Test that Logger abstract base class enables verification through mocking."""

        # Arrange: Application code that uses logger
        def create_node(node_id: str, logger: Logger) -> str:
            """Example application function that uses logger."""
            logger.info('Creating node %s', node_id)
            # Simulate some work
            if node_id == 'invalid':
                logger.error('Failed to create node: invalid ID')
                raise ValueError('Invalid node ID')

            logger.debug('Node %s created successfully', node_id)
            return f'Created {node_id}'

        # Mock Logger using unittest.mock
        mock_logger = MagicMock(spec=Logger)

        # Act: Use application code with mock logger
        result = create_node('test_node', mock_logger)

        # Assert: Mock enables verification of logging behavior
        assert result == 'Created test_node'
        mock_logger.info.assert_called_once_with('Creating node %s', 'test_node')
        mock_logger.debug.assert_called_once_with('Node %s created successfully', 'test_node')
        mock_logger.error.assert_not_called()

    def test_logger_supports_mocking_for_error_scenarios(self) -> None:
        """Test that Logger mock enables verification of error logging."""

        # Arrange: Application code that logs errors
        def validate_node(node_data: dict[str, Any], logger: Logger) -> bool:
            """Example application function that validates and logs errors."""
            if not node_data.get('id'):
                logger.error('Node validation failed: missing ID')
                return False
            logger.info('Node validation passed for %s', node_data['id'])
            return True

        # Mock Logger using unittest.mock
        mock_logger = MagicMock(spec=Logger)

        # Act: Test error scenario
        result = validate_node({}, mock_logger)

        # Assert: Error logging is verified through mock
        assert result is False
        mock_logger.error.assert_called_once_with('Node validation failed: missing ID')
        mock_logger.info.assert_not_called()

    def test_logger_interface_follows_stdlib_logging_patterns(self) -> None:
        """Test that Logger interface follows Python stdlib logging method signatures."""
        # Arrange: Standard library logging module for comparison
        import logging

        stdlib_logger = logging.getLogger('test')

        # Act: Compare method signatures for basic logging methods
        debug_sig = inspect.signature(Logger.debug)
        info_sig = inspect.signature(Logger.info)
        warning_sig = inspect.signature(Logger.warning)
        error_sig = inspect.signature(Logger.error)

        stdlib_debug_sig = inspect.signature(stdlib_logger.debug)
        stdlib_info_sig = inspect.signature(stdlib_logger.info)
        stdlib_warning_sig = inspect.signature(stdlib_logger.warning)
        stdlib_error_sig = inspect.signature(stdlib_logger.error)

        # Assert: Parameter names match stdlib logging (excluding 'self' vs first param)
        # Note: exception method intentionally has simpler signature than stdlib
        assert list(debug_sig.parameters.keys())[1:] == list(stdlib_debug_sig.parameters.keys())
        assert list(info_sig.parameters.keys())[1:] == list(stdlib_info_sig.parameters.keys())
        assert list(warning_sig.parameters.keys())[1:] == list(stdlib_warning_sig.parameters.keys())
        assert list(error_sig.parameters.keys())[1:] == list(stdlib_error_sig.parameters.keys())

    @pytest.mark.parametrize('method_name', ['debug', 'info', 'warning', 'error', 'exception'])
    def test_logger_method_accepts_any_message_type(self, method_name: str) -> None:
        """Test that all Logger methods accept object type for message parameter."""
        # Arrange: Get method from Logger class
        method = getattr(Logger, method_name)
        signature = inspect.signature(method)

        # Act: Check msg parameter annotation
        msg_param = signature.parameters['msg']
        param_annotation = msg_param.annotation

        # Assert: Accepts object type for flexible message handling
        assert param_annotation is object

    def test_logger_enables_dependency_injection_in_hexagonal_architecture(self) -> None:
        """Test that Logger enables dependency injection following hexagonal architecture principles."""

        # Arrange: Application service that depends on Logger port
        class NodeService:
            def __init__(self, logger: Logger) -> None:
                self._logger = logger

            def create_node(self, node_id: str) -> str:
                self._logger.info('Starting node creation for %s', node_id)
                # Business logic here
                self._logger.debug('Node %s creation completed', node_id)
                return f'Node {node_id} created'

        # Test Logger implementation
        class TestLogger(Logger):
            def __init__(self) -> None:
                self.log_entries: list[tuple[str, Any, tuple[Any, ...]]] = []

            def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.log_entries.append(('debug', msg, args))

            def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.log_entries.append(('info', msg, args))

            def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.log_entries.append(('warning', msg, args))

            def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.log_entries.append(('error', msg, args))

            def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
                self.log_entries.append(('exception', msg, args))

        # Act: Inject logger dependency into application service
        test_logger = TestLogger()
        service = NodeService(test_logger)
        result = service.create_node('test123')

        # Assert: Dependency injection enables testable, loosely coupled design
        assert result == 'Node test123 created'
        assert len(test_logger.log_entries) == 2
        assert test_logger.log_entries[0] == ('info', 'Starting node creation for %s', ('test123',))
        assert test_logger.log_entries[1] == ('debug', 'Node %s creation completed', ('test123',))
        assert isinstance(service._logger, Logger)

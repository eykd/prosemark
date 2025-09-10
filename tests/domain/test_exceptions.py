"""Tests for domain exceptions."""


import pytest
from uuid_extension import uuid7

from prosemark.domain.exceptions import (
    BinderIntegrityError,
    NodeIdentityError,
    ProsemarkDomainError,
)
from prosemark.domain.value_objects import NodeId


class TestProsemarkDomainError:
    """Test suite for base domain exception."""

    def test_is_exception(self) -> None:
        """ProsemarkDomainError is an Exception."""
        error = ProsemarkDomainError('Test error')

        assert isinstance(error, Exception)
        assert str(error) == 'Test error'

    def test_inheritance_chain(self) -> None:
        """ProsemarkDomainError provides proper inheritance chain."""
        error = ProsemarkDomainError('Test error')

        # Should be catchable as Exception
        with pytest.raises(Exception):
            raise error

        # Should be catchable as ProsemarkDomainError
        with pytest.raises(ProsemarkDomainError):
            raise error

    def test_custom_message(self) -> None:
        """ProsemarkDomainError accepts custom message."""
        message = 'Custom error message with details'
        error = ProsemarkDomainError(message)

        assert str(error) == message
        assert error.args == (message,)

    def test_empty_message(self) -> None:
        """ProsemarkDomainError can be created without message."""
        error = ProsemarkDomainError()

        assert isinstance(error, ProsemarkDomainError)
        # Empty message should still be handleable
        str(error)  # Should not raise


class TestNodeIdentityError:
    """Test suite for NodeIdentityError."""

    def test_inherits_from_domain_error(self) -> None:
        """NodeIdentityError inherits from ProsemarkDomainError."""
        error = NodeIdentityError('Test error')

        assert isinstance(error, ProsemarkDomainError)
        assert isinstance(error, Exception)

    def test_specific_error_context(self) -> None:
        """NodeIdentityError provides specific context for node ID issues."""
        node_id = NodeId(uuid7())
        message = f'Invalid node ID: {node_id}'
        error = NodeIdentityError(message)

        assert str(error) == message
        assert 'node id' in str(error).lower()

    def test_catchable_as_base_exception(self) -> None:
        """NodeIdentityError can be caught as base domain error."""
        error = NodeIdentityError('Node ID validation failed')

        # Should be catchable as specific type
        with pytest.raises(NodeIdentityError):
            raise error

        # Should be catchable as base domain error
        with pytest.raises(ProsemarkDomainError):
            raise error

    def test_with_node_id_context(self) -> None:
        """NodeIdentityError can include NodeId in error context."""
        node_id = NodeId(uuid7())
        error = NodeIdentityError(f'Duplicate node ID: {node_id}')

        assert str(node_id) in str(error)


class TestBinderIntegrityError:
    """Test suite for BinderIntegrityError."""

    def test_inherits_from_domain_error(self) -> None:
        """BinderIntegrityError inherits from ProsemarkDomainError."""
        error = BinderIntegrityError('Test error')

        assert isinstance(error, ProsemarkDomainError)
        assert isinstance(error, Exception)

    def test_specific_error_context(self) -> None:
        """BinderIntegrityError provides specific context for binder issues."""
        message = 'Binder contains duplicate NodeIds'
        error = BinderIntegrityError(message)

        assert str(error) == message
        assert 'binder' in str(error).lower() or 'duplicate' in str(error).lower()

    def test_catchable_as_base_exception(self) -> None:
        """BinderIntegrityError can be caught as base domain error."""
        error = BinderIntegrityError('Binder validation failed')

        # Should be catchable as specific type
        with pytest.raises(BinderIntegrityError):
            raise error

        # Should be catchable as base domain error
        with pytest.raises(ProsemarkDomainError):
            raise error

    def test_with_duplicate_id_context(self) -> None:
        """BinderIntegrityError can include duplicate ID context."""
        node_id = NodeId(uuid7())
        error = BinderIntegrityError(f'Duplicate NodeId found: {node_id}')

        assert str(node_id) in str(error)
        assert 'duplicate' in str(error).lower()

    def test_with_tree_validation_context(self) -> None:
        """BinderIntegrityError can include tree validation context."""
        error = BinderIntegrityError('Invalid tree structure: cycle detected')

        assert 'tree' in str(error).lower() or 'cycle' in str(error).lower()


class TestExceptionHandling:
    """Test exception handling scenarios."""

    def test_catch_all_domain_exceptions(self) -> None:
        """All domain exceptions can be caught with base class."""
        exceptions = [
            ProsemarkDomainError('Base error'),
            NodeIdentityError('Node error'),
            BinderIntegrityError('Binder error'),
        ]

        for exc in exceptions:
            with pytest.raises(ProsemarkDomainError):
                raise exc

    def test_specific_exception_catching(self) -> None:
        """Specific exceptions can be caught individually."""
        # Test catching specific exception types
        with pytest.raises(NodeIdentityError):
            raise NodeIdentityError('Specific node error')

        with pytest.raises(BinderIntegrityError):
            raise BinderIntegrityError('Specific binder error')

    def test_exception_hierarchy_order(self) -> None:
        """Exception catching respects hierarchy order."""
        node_error = NodeIdentityError('Node issue')

        # More specific exception should be caught first
        with pytest.raises(NodeIdentityError):
            raise node_error

    def test_error_messages_preserved(self) -> None:
        """Error messages are preserved through inheritance chain."""
        original_message = 'Original error with context details'

        for exc_class in [ProsemarkDomainError, NodeIdentityError, BinderIntegrityError]:
            error = exc_class(original_message)
            assert str(error) == original_message

    def test_error_args_preserved(self) -> None:
        """Error args are preserved for programmatic access."""
        message = 'Error message'
        context = {'node_id': str(NodeId(uuid7()))}

        # Test with message only
        error1 = BinderIntegrityError(message)
        assert error1.args == (message,)

        # Test with multiple args
        error2 = BinderIntegrityError(message, context)
        assert error2.args == (message, context)
        assert error2.args[1] == context

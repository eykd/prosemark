"""Tests for domain exception classes."""

import pytest

from prosemark.exceptions import (
    BinderIntegrityError,
    BinderNotFoundError,
    FileSystemError,
    NodeIdentityError,
    NodeNotFoundError,
    ProsemarkError,
)


class TestExceptionCreation:
    """Test creation and basic properties of all exception types."""

    def test_exception_creation(self) -> None:
        """Test all exception types can be created with messages."""
        errors = [
            BinderIntegrityError('Duplicate node found', 'node123'),
            NodeIdentityError('Invalid UUID format', 'bad-uuid'),
            BinderNotFoundError('Binder file missing', '_binder.md'),
            NodeNotFoundError('Node not found', 'missing-id'),
            FileSystemError('Permission denied', '/path/file.md'),
        ]

        for error in errors:
            assert isinstance(error, Exception)
            assert isinstance(error, ProsemarkError)
            assert len(error.args) >= 1

    def test_exception_with_single_argument(self) -> None:
        """Test exceptions can be created with just a message."""
        errors = [
            BinderIntegrityError('Duplicate node found'),
            NodeIdentityError('Invalid UUID format'),
            BinderNotFoundError('Binder file missing'),
            NodeNotFoundError('Node not found'),
            FileSystemError('Permission denied'),
        ]

        for error in errors:
            assert isinstance(error, Exception)
            assert isinstance(error, ProsemarkError)
            assert len(error.args) >= 1
            assert error.args[0] == str(error.args[0])  # Message is a string

    def test_exception_with_multiple_context_arguments(self) -> None:
        """Test exceptions can accept multiple context arguments."""
        error = BinderIntegrityError('Multiple nodes with same ID', 'node123', 'file1.md', 'file2.md')

        assert len(error.args) == 4
        assert error.args[0] == 'Multiple nodes with same ID'
        assert error.args[1] == 'node123'
        assert error.args[2] == 'file1.md'
        assert error.args[3] == 'file2.md'


class TestExceptionChaining:
    """Test exception chaining behavior."""

    def test_exception_chaining(self) -> None:
        """Test exceptions support proper chaining."""
        original = ValueError('Original error')

        def chain_exception() -> None:
            try:
                raise original
            except ValueError as exc:
                raise NodeIdentityError('Chain test', 'node123') from exc

        with pytest.raises(NodeIdentityError) as exc_info:
            chain_exception()

        chained = exc_info.value
        assert chained.__cause__ == original
        assert 'Chain test' in str(chained)
        assert chained.args[0] == 'Chain test'
        assert chained.args[1] == 'node123'

    def test_chaining_different_exception_types(self) -> None:
        """Test chaining between different domain exception types."""
        original = FileSystemError('File read error', '/path/to/file.md')

        def chain_different_types() -> None:
            try:
                raise original
            except FileSystemError as exc:
                raise BinderNotFoundError('Cannot load binder', '_binder.md') from exc

        with pytest.raises(BinderNotFoundError) as exc_info:
            chain_different_types()

        chained = exc_info.value
        assert chained.__cause__ == original
        assert isinstance(chained.__cause__, FileSystemError)
        assert chained.args[0] == 'Cannot load binder'
        assert chained.args[1] == '_binder.md'

    def test_chaining_from_standard_exception(self) -> None:
        """Test chaining from standard Python exceptions."""
        original = OSError('Permission denied')

        def chain_from_standard() -> None:
            try:
                raise original
            except OSError as exc:
                raise FileSystemError('Cannot write file', '/restricted/file.md') from exc

        with pytest.raises(FileSystemError) as exc_info:
            chain_from_standard()

        chained = exc_info.value
        assert chained.__cause__ == original
        assert isinstance(chained.__cause__, OSError)


class TestExceptionHierarchy:
    """Test exception inheritance structure."""

    def test_exception_hierarchy(self) -> None:
        """Test exception inheritance structure."""
        # All domain exceptions should inherit from ProsemarkError
        domain_errors = [
            BinderIntegrityError('msg'),
            NodeIdentityError('msg'),
            BinderNotFoundError('msg'),
            NodeNotFoundError('msg'),
            FileSystemError('msg'),
        ]

        for error in domain_errors:
            assert isinstance(error, Exception)
            assert isinstance(error, ProsemarkError)
            # Should not inherit from generic exceptions
            assert type(error).__bases__ != (Exception,)

    def test_base_exception_class(self) -> None:
        """Test ProsemarkError base class behavior."""
        base_error = ProsemarkError('Base error message', 'extra_context')

        assert isinstance(base_error, Exception)
        assert base_error.args[0] == 'Base error message'
        assert base_error.args[1] == 'extra_context'
        assert str(base_error) == "('Base error message', 'extra_context')"


class TestErrorMessageFormat:
    """Test error message formatting conventions."""

    def test_error_message_format(self) -> None:
        """Test error messages follow conventions."""
        error = BinderIntegrityError('Duplicate node found', 'node123')

        # Should not have variable substitution in message
        assert 'node123' not in error.args[0]
        assert error.args[0] == 'Duplicate node found'

        # Should be able to access additional context
        assert len(error.args) >= 2  # message + context
        assert error.args[1] == 'node123'

    def test_no_variable_interpolation_in_messages(self) -> None:
        """Test that error messages don't contain variable interpolation."""
        # Messages should be static strings, context is in separate args
        errors = [
            BinderIntegrityError('Duplicate node detected', 'node_id_123'),
            NodeIdentityError('Invalid UUID format', 'not-a-uuid'),
            FileSystemError('Permission denied', '/root/file.md'),
        ]

        for error in errors:
            message = error.args[0]
            # Check for common interpolation patterns
            assert '{' not in message
            assert '%' not in message
            assert not message.startswith('f')  # Not an f-string

    def test_error_string_representation(self) -> None:
        """Test string representation of exceptions."""
        error1 = NodeNotFoundError('Node not found')
        error2 = NodeNotFoundError('Node not found', 'node123')

        # Single argument should show just the message in parens
        assert str(error1) == 'Node not found'

        # Multiple arguments should show tuple representation
        assert str(error2) == "('Node not found', 'node123')"


class TestSpecificExceptionBehavior:
    """Test specific behavior for each exception type."""

    def test_binder_integrity_error(self) -> None:
        """Test BinderIntegrityError for tree invariant violations."""
        error = BinderIntegrityError('Duplicate node in tree', 'node_id', 'parent_id')

        assert isinstance(error, ProsemarkError)
        assert error.args[0] == 'Duplicate node in tree'
        assert error.args[1] == 'node_id'
        assert error.args[2] == 'parent_id'

    def test_node_identity_error(self) -> None:
        """Test NodeIdentityError for invalid NodeId operations."""
        error = NodeIdentityError('Invalid UUID format', 'not-a-valid-uuid')

        assert isinstance(error, ProsemarkError)
        assert error.args[0] == 'Invalid UUID format'
        assert error.args[1] == 'not-a-valid-uuid'

    def test_binder_not_found_error(self) -> None:
        """Test BinderNotFoundError when binder file is missing."""
        error = BinderNotFoundError('Binder file not found', '_binder.md', '/project/path')

        assert isinstance(error, ProsemarkError)
        assert error.args[0] == 'Binder file not found'
        assert error.args[1] == '_binder.md'
        assert len(error.args) == 3

    def test_node_not_found_error(self) -> None:
        """Test NodeNotFoundError when referenced node doesn't exist."""
        error = NodeNotFoundError('Referenced node missing', 'node_id_456')

        assert isinstance(error, ProsemarkError)
        assert error.args[0] == 'Referenced node missing'
        assert error.args[1] == 'node_id_456'

    def test_filesystem_error(self) -> None:
        """Test FileSystemError for file system operation failures."""
        error = FileSystemError('Permission denied', '/restricted/path', 'write')

        assert isinstance(error, ProsemarkError)
        assert error.args[0] == 'Permission denied'
        assert error.args[1] == '/restricted/path'
        assert error.args[2] == 'write'

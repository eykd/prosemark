"""Tests for compile service port."""

import pytest

from prosemark.domain.compile.models import CompileRequest, CompileResult
from prosemark.domain.models import NodeId
from prosemark.ports.compile.service import CompileError, CompileServicePort, NodeNotFoundError


class TestNodeNotFoundError:
    """Test the NodeNotFoundError exception."""

    def test_create_exception_with_node_id(self) -> None:
        """Test creating exception with node ID."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        error = NodeNotFoundError(node_id)

        assert error.node_id == node_id
        assert str(error) == f'Node not found: {node_id}'

    def test_exception_inheritance(self) -> None:
        """Test that exception inherits from Exception."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        error = NodeNotFoundError(node_id)

        assert isinstance(error, Exception)


class TestCompileError:
    """Test the CompileError exception."""

    def test_create_base_exception(self) -> None:
        """Test creating base compile error."""
        error = CompileError('Test error message')

        assert str(error) == 'Test error message'
        assert isinstance(error, Exception)


class TestCompileServicePort:
    """Test the CompileServicePort abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            CompileServicePort()  # type: ignore[abstract]

    def test_abstract_method_exists(self) -> None:
        """Test that abstract method is defined."""
        # Verify the abstract method exists and has correct signature
        assert hasattr(CompileServicePort, 'compile_subtree')
        assert CompileServicePort.compile_subtree.__isabstractmethod__  # type: ignore[attr-defined]


class ConcreteCompileService(CompileServicePort):
    """Concrete implementation for testing."""

    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        """Concrete implementation of abstract method."""
        return CompileResult(content='Test content', node_count=1, total_nodes=1, skipped_empty=0)


class TestCompileServicePortImplementation:
    """Test concrete implementation of the port."""

    def test_concrete_implementation_works(self) -> None:
        """Test that concrete implementation works."""
        service = ConcreteCompileService()
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        request = CompileRequest(node_id=node_id)

        result = service.compile_subtree(request)

        assert isinstance(result, CompileResult)
        assert result.content == 'Test content'
        assert result.node_count == 1

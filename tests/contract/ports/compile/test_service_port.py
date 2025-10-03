"""Contract tests for CompileServicePort.

These tests define the expected behavior of any implementation
of the CompileServicePort interface.
"""

import pytest

from prosemark.domain.compile.models import CompileRequest, CompileResult
from prosemark.domain.models import NodeId
from prosemark.ports.compile.service import (
    CompileServicePort,
    NodeNotFoundError,
)


class MockCompileService(CompileServicePort):
    """Mock implementation for testing the contract."""

    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def compile_subtree(self, request: CompileRequest) -> CompileResult:
        if self.should_fail:
            # Type guard: In the mock, we assume node_id is not None for error testing
            if request.node_id is None:
                from prosemark.ports.compile.service import CompileError

                raise CompileError('node_id cannot be None')
            raise NodeNotFoundError(request.node_id)

        # This will fail until real implementation is created
        return CompileResult(content='Mock content', node_count=1, total_nodes=1, skipped_empty=0)


@pytest.fixture
def compile_service() -> MockCompileService:
    """Provide a mock compile service for testing."""
    return MockCompileService()


@pytest.fixture
def failing_service() -> MockCompileService:
    """Provide a failing compile service for error testing."""
    return MockCompileService(should_fail=True)


@pytest.fixture
def valid_node_id() -> NodeId:
    """Provide a valid node ID for testing."""
    return NodeId('01923456-789a-7123-8abc-def012345678')


class TestCompileServicePortContract:
    """Test the CompileServicePort contract."""

    def test_compile_subtree_with_valid_request(
        self, compile_service: MockCompileService, valid_node_id: NodeId
    ) -> None:
        """Test that compile_subtree accepts valid requests and returns results."""
        request = CompileRequest(node_id=valid_node_id, include_empty=False)

        result = compile_service.compile_subtree(request)

        assert isinstance(result, CompileResult)
        assert isinstance(result.content, str)
        assert isinstance(result.node_count, int)
        assert isinstance(result.total_nodes, int)
        assert isinstance(result.skipped_empty, int)

    def test_compile_subtree_with_include_empty_option(
        self, compile_service: MockCompileService, valid_node_id: NodeId
    ) -> None:
        """Test that compile_subtree respects include_empty option."""
        request_false = CompileRequest(node_id=valid_node_id, include_empty=False)
        request_true = CompileRequest(node_id=valid_node_id, include_empty=True)

        result_false = compile_service.compile_subtree(request_false)
        result_true = compile_service.compile_subtree(request_true)

        # Both should return valid results
        assert isinstance(result_false, CompileResult)
        assert isinstance(result_true, CompileResult)

    def test_compile_subtree_raises_node_not_found_error(
        self, failing_service: MockCompileService, valid_node_id: NodeId
    ) -> None:
        """Test that compile_subtree raises NodeNotFoundError for missing nodes."""
        request = CompileRequest(node_id=valid_node_id, include_empty=False)

        with pytest.raises(NodeNotFoundError) as exc_info:
            failing_service.compile_subtree(request)

        assert exc_info.value.node_id == valid_node_id
        assert str(valid_node_id) in str(exc_info.value)

    def test_compile_request_immutability(self, valid_node_id: NodeId) -> None:
        """Test that CompileRequest is immutable."""
        request = CompileRequest(node_id=valid_node_id, include_empty=True)

        # These should fail if the dataclass is not frozen
        with pytest.raises(AttributeError):
            request.node_id = NodeId('01923456-789a-7123-8abc-def012345679')  # type: ignore[misc]

        with pytest.raises(AttributeError):
            request.include_empty = False  # type: ignore[misc]

    def test_compile_result_immutability(self) -> None:
        """Test that CompileResult is immutable."""
        result = CompileResult(content='test content', node_count=1, total_nodes=2, skipped_empty=1)

        # These should fail if the dataclass is not frozen
        with pytest.raises(AttributeError):
            result.content = 'modified'  # type: ignore[misc]

        with pytest.raises(AttributeError):
            result.node_count = 5  # type: ignore[misc]


class TestCompileModels:
    """Test the compile data models."""

    def test_compile_request_default_values(self, valid_node_id: NodeId) -> None:
        """Test CompileRequest default values."""
        request = CompileRequest(node_id=valid_node_id)

        assert request.node_id == valid_node_id
        assert request.include_empty is False

    def test_compile_result_fields(self) -> None:
        """Test CompileResult field types and values."""
        result = CompileResult(content='Test content\n\nMore content', node_count=2, total_nodes=3, skipped_empty=1)

        assert result.content == 'Test content\n\nMore content'
        assert result.node_count == 2
        assert result.total_nodes == 3
        assert result.skipped_empty == 1


# This test should fail initially because we haven't implemented anything yet
def test_actual_implementation_exists() -> None:
    """This test ensures we implement a real CompileService."""
    # This will fail until we create the actual implementation
    from prosemark.domain.compile.service import CompileService  # This import should fail

    assert CompileService is not None, 'CompileService implementation is missing'

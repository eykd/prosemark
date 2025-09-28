"""Tests for compile domain models."""

import pytest

from prosemark.domain.compile.models import CompileRequest, CompileResult, NodeContent
from prosemark.domain.models import NodeId


class TestCompileRequest:
    """Test the CompileRequest model."""

    def test_create_request_with_defaults(self) -> None:
        """Test creating request with default values."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        request = CompileRequest(node_id=node_id)

        assert request.node_id == node_id
        assert request.include_empty is False

    def test_create_request_with_include_empty(self) -> None:
        """Test creating request with include_empty=True."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        request = CompileRequest(node_id=node_id, include_empty=True)

        assert request.node_id == node_id
        assert request.include_empty is True

    def test_request_immutability(self) -> None:
        """Test that CompileRequest is immutable (frozen)."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        request = CompileRequest(node_id=node_id)

        with pytest.raises(AttributeError):
            request.node_id = NodeId('01923456-789a-7123-8abc-def012345679')  # type: ignore[misc]


class TestCompileResult:
    """Test the CompileResult model."""

    def test_create_valid_result(self) -> None:
        """Test creating a valid result."""
        result = CompileResult(content='Test content', node_count=2, total_nodes=3, skipped_empty=1)

        assert result.content == 'Test content'
        assert result.node_count == 2
        assert result.total_nodes == 3
        assert result.skipped_empty == 1

    def test_result_validation_negative_node_count(self) -> None:
        """Test validation fails for negative node_count."""
        with pytest.raises(ValueError, match='node_count must be non-negative'):
            CompileResult(content='Test', node_count=-1, total_nodes=3, skipped_empty=1)

    def test_result_validation_total_less_than_node_count(self) -> None:
        """Test validation fails when total_nodes < node_count."""
        with pytest.raises(ValueError, match='total_nodes must be >= node_count'):
            CompileResult(content='Test', node_count=5, total_nodes=3, skipped_empty=1)

    def test_result_validation_negative_skipped_empty(self) -> None:
        """Test validation fails for negative skipped_empty."""
        with pytest.raises(ValueError, match='skipped_empty must be non-negative'):
            CompileResult(content='Test', node_count=2, total_nodes=3, skipped_empty=-1)

    def test_result_validation_skipped_empty_too_high(self) -> None:
        """Test validation fails when skipped_empty exceeds possible range."""
        with pytest.raises(ValueError, match='skipped_empty cannot exceed traversed - included nodes'):
            CompileResult(
                content='Test',
                node_count=2,
                total_nodes=3,
                skipped_empty=2,  # Only 1 node was skipped (3 - 2 = 1), but we claim 2
            )

    def test_result_edge_case_zero_values(self) -> None:
        """Test result with all zero values."""
        result = CompileResult(content='', node_count=0, total_nodes=0, skipped_empty=0)

        assert result.content == ''
        assert result.node_count == 0
        assert result.total_nodes == 0
        assert result.skipped_empty == 0

    def test_result_edge_case_all_nodes_included(self) -> None:
        """Test result when all nodes are included (none skipped)."""
        result = CompileResult(content='All content', node_count=5, total_nodes=5, skipped_empty=0)

        assert result.node_count == 5
        assert result.total_nodes == 5
        assert result.skipped_empty == 0

    def test_result_edge_case_all_nodes_skipped(self) -> None:
        """Test result when all nodes are skipped."""
        result = CompileResult(content='', node_count=0, total_nodes=3, skipped_empty=3)

        assert result.node_count == 0
        assert result.total_nodes == 3
        assert result.skipped_empty == 3

    def test_result_immutability(self) -> None:
        """Test that CompileResult is immutable (frozen)."""
        result = CompileResult(content='Test', node_count=1, total_nodes=1, skipped_empty=0)

        with pytest.raises(AttributeError):
            result.content = 'Modified'  # type: ignore[misc]


class TestNodeContent:
    """Test the NodeContent model."""

    def test_create_node_content(self) -> None:
        """Test creating node content."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        child1 = NodeId('01923456-789a-7123-8abc-def012345679')
        child2 = NodeId('01923456-789a-7123-8abc-def012345680')

        node_content = NodeContent(id=node_id, content='Node content text', children=[child1, child2])

        assert node_content.id == node_id
        assert node_content.content == 'Node content text'
        assert node_content.children == [child1, child2]

    def test_create_node_content_no_children(self) -> None:
        """Test creating node content with no children."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')

        node_content = NodeContent(id=node_id, content='Leaf node content', children=[])

        assert node_content.id == node_id
        assert node_content.content == 'Leaf node content'
        assert node_content.children == []

    def test_node_content_immutability(self) -> None:
        """Test that NodeContent is immutable (frozen)."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345678')
        node_content = NodeContent(id=node_id, content='Test content', children=[])

        with pytest.raises(AttributeError):
            node_content.content = 'Modified content'  # type: ignore[misc]

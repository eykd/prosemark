"""Unit tests for CompileService domain logic.

These tests verify the core compilation algorithm including
depth-first traversal, content concatenation, and statistics.
"""

import pytest

from prosemark.domain.compile.models import CompileRequest, CompileResult
from prosemark.domain.models import NodeId
from prosemark.ports.compile.service import NodeNotFoundError
from prosemark.ports.node_repo import NodeRepo

# This import will fail until we implement the service
try:
    from prosemark.domain.compile.service import CompileService
except ImportError:
    CompileService = None


class MockNode:
    """Mock node for testing."""

    def __init__(self, node_id: str, content: str, children: list[str] | None = None) -> None:
        self.node_id = node_id
        self.content = content
        self.children = [NodeId(child) for child in (children or [])]


class MockNodeRepo(NodeRepo):
    """Mock node repository for testing."""

    def __init__(self, nodes: dict[str, MockNode]) -> None:
        self._nodes = nodes

    def get_node(self, node_id: NodeId) -> MockNode:
        """Get node by ID."""
        node = self._nodes.get(str(node_id))
        if node is None:
            msg = f'Node not found: {node_id}'
            raise ValueError(msg)
        return node

    def get_children(self, node_id: NodeId) -> list[NodeId]:
        """Get children of a node."""
        node = self.get_node(node_id)
        return node.children

    # Required abstract methods from NodeRepo interface
    def create(self, node_id: NodeId, title: str | None, synopsis: str | None) -> None:
        """Create new node files with initial frontmatter."""
        pass

    def read_frontmatter(self, node_id: NodeId) -> dict[str, str | None]:
        """Read frontmatter from node draft file."""
        # Just verify the node exists to trigger the error handling path
        self.get_node(node_id)
        return {'id': str(node_id), 'title': f'Node {node_id}'}

    def write_frontmatter(self, node_id: NodeId, fm: dict[str, str | None]) -> None:
        """Update frontmatter in node draft file."""
        pass

    def open_in_editor(self, node_id: NodeId, part: str) -> None:
        """Open specified node part in editor."""
        pass

    def delete(self, node_id: NodeId, *, delete_files: bool) -> None:
        """Remove node from system."""
        pass

    def get_existing_files(self) -> set[NodeId]:
        """Get all existing node files from the filesystem."""
        return set(NodeId(node_id) for node_id in self._nodes.keys())

    def file_exists(self, node_id: NodeId, file_type: str) -> bool:
        """Check if a specific node file exists."""
        return str(node_id) in self._nodes

    def create_notes_file(self, node_id: NodeId) -> None:
        """Create only the notes file for an existing node."""
        pass


@pytest.fixture
def sample_nodes() -> dict[str, MockNode]:
    """Provide sample nodes for testing."""
    return {
        # Simple hierarchy for basic tests
        '01923456-789a-7123-8abc-def012345678': MockNode(
            '01923456-789a-7123-8abc-def012345678',
            'Chapter 1',
            ['01923456-789a-7123-8abc-def012345679', '01923456-789a-7123-8abc-def012345680'],
        ),
        '01923456-789a-7123-8abc-def012345679': MockNode('01923456-789a-7123-8abc-def012345679', 'Section 1.1'),
        '01923456-789a-7123-8abc-def012345680': MockNode('01923456-789a-7123-8abc-def012345680', 'Section 1.2'),
        # Empty node for testing skipping behavior
        '01923456-789a-7123-8abc-def012345681': MockNode(
            '01923456-789a-7123-8abc-def012345681',
            '',  # Empty content
            ['01923456-789a-7123-8abc-def012345682'],
        ),
        '01923456-789a-7123-8abc-def012345682': MockNode('01923456-789a-7123-8abc-def012345682', 'After empty'),
        # Deep nesting for traversal tests
        '01923456-789a-7123-8abc-def012345690': MockNode(
            '01923456-789a-7123-8abc-def012345690', 'Root', ['01923456-789a-7123-8abc-def012345691']
        ),
        '01923456-789a-7123-8abc-def012345691': MockNode(
            '01923456-789a-7123-8abc-def012345691',
            'Level 1',
            ['01923456-789a-7123-8abc-def012345692', '01923456-789a-7123-8abc-def012345693'],
        ),
        '01923456-789a-7123-8abc-def012345692': MockNode('01923456-789a-7123-8abc-def012345692', 'Level 2A'),
        '01923456-789a-7123-8abc-def012345693': MockNode('01923456-789a-7123-8abc-def012345693', 'Level 2B'),
    }


@pytest.fixture
def mock_node_repo(sample_nodes: dict[str, MockNode]) -> MockNodeRepo:
    """Provide a mock node repository."""
    return MockNodeRepo(sample_nodes)


@pytest.fixture
def compile_service(mock_node_repo: MockNodeRepo) -> CompileService:
    """Provide a CompileService instance for testing."""
    if CompileService is None:
        pytest.skip('CompileService not implemented yet')
    return CompileService(mock_node_repo)


@pytest.mark.skipif(CompileService is None, reason='CompileService not implemented yet')
class TestCompileServiceDomain:
    """Test the CompileService domain logic."""

    def test_depth_first_traversal_algorithm(self, compile_service: CompileService) -> None:
        """Test that nodes are traversed in depth-first pre-order."""
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345690'), include_empty=False)

        result = compile_service.compile_subtree(request)

        # Should traverse: Root -> Level 1 -> Level 2A -> Level 2B
        expected_content = 'Root\n\nLevel 1\n\nLevel 2A\n\nLevel 2B'
        assert result.content == expected_content

    def test_content_concatenation_with_double_newlines(self, compile_service: CompileService) -> None:
        """Test that content is concatenated with double newline separation."""
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345678'), include_empty=False)

        result = compile_service.compile_subtree(request)

        # Should have double newlines between each node's content
        expected_content = 'Chapter 1\n\nSection 1.1\n\nSection 1.2'
        assert result.content == expected_content
        assert '\n\n' in result.content

    def test_statistics_calculation_node_count(self, compile_service: CompileService) -> None:
        """Test that node_count is calculated correctly."""
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345678'), include_empty=False)

        result = compile_service.compile_subtree(request)

        # Should count 3 nodes: parent + 2 children
        assert result.node_count == 3
        assert result.total_nodes == 3
        assert result.skipped_empty == 0

    def test_statistics_calculation_skipped_empty(self, compile_service: CompileService) -> None:
        """Test that skipped_empty count is calculated correctly."""
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345681'), include_empty=False)

        result = compile_service.compile_subtree(request)

        # Should skip the empty parent but include the child
        assert result.content == 'After empty'
        assert result.node_count == 1  # Only the non-empty child
        assert result.total_nodes == 2  # Traversed both nodes
        assert result.skipped_empty == 1  # Skipped the empty parent

    def test_include_empty_option_behavior(self, compile_service: CompileService) -> None:
        """Test that include_empty option works correctly."""
        node_id = NodeId('01923456-789a-7123-8abc-def012345681')

        # Test with include_empty=False (default)
        request_skip = CompileRequest(node_id=node_id, include_empty=False)
        result_skip = compile_service.compile_subtree(request_skip)

        # Test with include_empty=True
        request_include = CompileRequest(node_id=node_id, include_empty=True)
        result_include = compile_service.compile_subtree(request_include)

        # Skip empty should have different results than include empty
        assert result_skip.content != result_include.content
        assert result_skip.node_count < result_include.node_count
        assert result_skip.skipped_empty > result_include.skipped_empty

    def test_single_node_compilation(self, compile_service: CompileService) -> None:
        """Test compilation of a single node with no children."""
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345679'), include_empty=False)

        result = compile_service.compile_subtree(request)

        assert result.content == 'Section 1.1'
        assert result.node_count == 1
        assert result.total_nodes == 1
        assert result.skipped_empty == 0

    def test_streaming_for_large_subtrees(self, compile_service: CompileService) -> None:
        """Test that service uses memory-efficient streaming."""
        # This test verifies the service doesn't load all content into memory at once
        # We can test this by verifying the service processes nodes incrementally
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345690'), include_empty=False)

        # The service should use generators/iterators for memory efficiency
        # This is more of a code inspection test - the actual implementation
        # should use yield or similar streaming patterns
        result = compile_service.compile_subtree(request)

        # At minimum, verify it works correctly
        assert isinstance(result, CompileResult)
        assert len(result.content) > 0

    def test_node_not_found_error(self, compile_service: CompileService) -> None:
        """Test error handling for non-existent nodes."""
        request = CompileRequest(
            node_id=NodeId('01923456-789a-7123-8abc-def012345999'),  # Non-existent
            include_empty=False,
        )

        with pytest.raises(NodeNotFoundError) as exc_info:
            compile_service.compile_subtree(request)

        # Should raise NodeNotFoundError
        assert 'not found' in str(exc_info.value).lower()


class TestCompileServiceValidation:
    """Test validation and edge cases."""

    @pytest.mark.skipif(CompileService is None, reason='CompileService not implemented yet')
    def test_empty_content_handling(self, mock_node_repo: MockNodeRepo) -> None:
        """Test handling of nodes with empty content."""
        service = CompileService(node_repo=mock_node_repo)
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345681'), include_empty=False)

        result = service.compile_subtree(request)

        # Empty nodes should be skipped completely
        assert '' not in result.content.split('\n\n')

    @pytest.mark.skipif(CompileService is None, reason='CompileService not implemented yet')
    def test_whitespace_preservation(self, mock_node_repo: MockNodeRepo) -> None:
        """Test that whitespace within nodes is preserved."""
        # Add a node with internal whitespace
        node_with_whitespace = MockNode('01923456-789a-7123-8abc-def012345700', 'Line 1\n    Indented line\nLine 3')
        mock_node_repo._nodes['01923456-789a-7123-8abc-def012345700'] = node_with_whitespace

        service = CompileService(node_repo=mock_node_repo)
        request = CompileRequest(node_id=NodeId('01923456-789a-7123-8abc-def012345700'), include_empty=False)

        result = service.compile_subtree(request)

        # Internal formatting should be preserved
        assert '    Indented line' in result.content


# This test should always fail initially to ensure TDD compliance
def test_compile_service_implementation_missing() -> None:
    """This test ensures we fail first before implementing."""
    try:
        from prosemark.domain.compile.service import CompileService

        # If import succeeds, check that it's actually implemented
        assert CompileService is not None, 'CompileService is None'
        # Try to instantiate to ensure it's a real class
        assert callable(CompileService), 'CompileService is not instantiable'
    except ImportError:
        # This is expected initially - the test should fail
        pytest.fail('CompileService not implemented yet (expected failure)')

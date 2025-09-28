"""Unit tests for structure command with node_id parameter.

These tests verify the CLI integration for subtree display functionality.
Following TDD, these tests should FAIL initially until implementation is complete.
"""

import json
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

# Import the CLI app - this will work because main.py exists
from prosemark.cli.main import app
from prosemark.domain.models import NodeId
from prosemark.exceptions import NodeNotFoundError

runner = CliRunner()


class TestStructureCommandWithNodeId:
    """Test structure command with node_id parameter for subtree display."""

    @pytest.fixture
    def mock_binder_repo(self) -> Generator[Mock, None, None]:
        """Mock BinderRepo for testing."""
        with patch('prosemark.cli.main.BinderRepoFs') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_show_structure(self) -> Generator[Mock, None, None]:
        """Mock ShowStructure use case."""
        with patch('prosemark.cli.main.ShowStructure') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_logger(self) -> Generator[Mock, None, None]:
        """Mock logger."""
        with patch('prosemark.cli.main.LoggerStdout') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance

    def test_structure_with_valid_node_id(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command with valid UUID node_id argument.

        Given: A valid UUID node_id is provided
        When: The structure command is executed
        Then: ShowStructure.execute() should be called with the node_id
        """
        # Arrange
        valid_uuid = '01997898-1dca-74d7-a727-b9a7023d0866'
        mock_show_structure.execute.return_value = f'Node Tree (root: {valid_uuid})'

        # Act
        result = runner.invoke(app, ['structure', valid_uuid])

        # Assert
        assert result.exit_code == 0
        # Verify execute was called with NodeId instance
        mock_show_structure.execute.assert_called_once()
        call_args = mock_show_structure.execute.call_args
        # Should be called with node_id parameter
        if call_args.kwargs:  # If using keyword arguments
            assert 'node_id' in call_args.kwargs
            passed_node_id = call_args.kwargs['node_id']
            assert isinstance(passed_node_id, NodeId)
            assert str(passed_node_id) == valid_uuid
        else:  # If using positional arguments
            assert len(call_args.args) > 0
            passed_node_id = call_args.args[0]
            assert isinstance(passed_node_id, NodeId)
            assert str(passed_node_id) == valid_uuid

    def test_structure_with_invalid_uuid_format(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command with invalid UUID format.

        Given: An invalid UUID string is provided
        When: The structure command is executed
        Then: Should show error message about invalid format
        """
        # Arrange
        invalid_uuid = 'abc123'

        # Act
        result = runner.invoke(app, ['structure', invalid_uuid])

        # Assert
        assert result.exit_code == 1
        assert 'Invalid node ID format' in result.output or 'Invalid UUID' in result.output
        # ShowStructure should not be called
        mock_show_structure.execute.assert_not_called()

    def test_structure_with_nonexistent_node_id(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command with non-existent node_id.

        Given: A valid UUID that doesn't exist in binder
        When: The structure command is executed
        Then: Should show error message about node not found
        """
        # Arrange
        nonexistent_uuid = '01996e70-aaaa-7ada-908e-ef3b5ddb5999'
        mock_show_structure.execute.side_effect = NodeNotFoundError('Node not found in binder', nonexistent_uuid)

        # Act
        result = runner.invoke(app, ['structure', nonexistent_uuid])

        # Assert
        assert result.exit_code == 1
        assert 'Node not found' in result.output
        assert nonexistent_uuid in result.output

    def test_structure_with_leaf_node(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command with leaf node (no children).

        Given: A node_id for a leaf node with no children
        When: The structure command is executed
        Then: Should display only that single node
        """
        # Arrange
        leaf_uuid = '01997898-1dcf-7bb2-806d-3c29d1ee5ed1'
        single_node_output = f'⇒ Academic—introducing Kolteo ({leaf_uuid})'
        mock_show_structure.execute.return_value = single_node_output

        # Act
        result = runner.invoke(app, ['structure', leaf_uuid])

        # Assert
        assert result.exit_code == 0
        assert 'Academic—introducing Kolteo' in result.output
        # Verify execute was called with the leaf node_id
        mock_show_structure.execute.assert_called_once()

    def test_structure_without_node_id_shows_full_tree(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command without node_id shows full tree (backward compatibility).

        Given: No node_id argument is provided
        When: The structure command is executed
        Then: Should display the full tree structure
        """
        # Arrange
        full_tree_output = 'Full Tree Structure\n├─ Part 1\n└─ Part 2'
        mock_show_structure.execute.return_value = full_tree_output

        # Act
        result = runner.invoke(app, ['structure'])

        # Assert
        assert result.exit_code == 0
        assert 'Project Structure:' in result.output
        # Verify execute was called without node_id or with None
        mock_show_structure.execute.assert_called_once()
        call_args = mock_show_structure.execute.call_args
        if call_args.kwargs:
            # Either no node_id key or node_id is None
            assert 'node_id' not in call_args.kwargs or call_args.kwargs['node_id'] is None
        else:
            # Called with no arguments or None
            assert len(call_args.args) == 0 or call_args.args[0] is None

    def test_structure_with_node_id_and_json_format(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command with node_id and JSON format output.

        Given: A valid node_id and --format json option
        When: The structure command is executed
        Then: Should output subtree in JSON format
        """
        # Arrange
        node_uuid = '01997898-1dca-74d7-a727-b9a7023d0866'
        # Mock the binder for JSON conversion

        mock_item = Mock()
        mock_item.display_title = 'Test Chapter'
        mock_item.id = NodeId(node_uuid)
        mock_item.children = []

        mock_binder = Mock()
        mock_binder.roots = [mock_item]
        mock_binder.find_by_id.return_value = mock_item
        mock_binder_repo.load.return_value = mock_binder

        # Mock the string output for finding subtree
        mock_show_structure.execute.return_value = f'Test Chapter ({node_uuid})'

        # Act
        result = runner.invoke(app, ['structure', '--format', 'json', node_uuid])

        # Assert
        assert result.exit_code == 0
        # Should produce valid JSON
        try:
            data = json.loads(result.output)
            assert 'roots' in data or 'root' in data or 'display_title' in data
        except json.JSONDecodeError:
            pytest.fail(f'Output is not valid JSON: {result.output}')

    def test_structure_with_json_format_and_nonexistent_node_id(
        self, mock_show_structure: Mock, mock_binder_repo: Mock, mock_logger: Mock
    ) -> None:
        """Test structure command with JSON format and non-existent node_id.

        Given: A valid UUID format that doesn't exist in binder and --format json option
        When: The structure command is executed
        Then: Should exit with error code 1 and show node not found message
        """
        # Arrange
        nonexistent_uuid = '01996e70-aaaa-7ada-908e-ef3b5ddb5999'

        mock_binder = Mock()
        mock_binder.find_by_id.return_value = None  # Node not found
        mock_binder_repo.load.return_value = mock_binder

        # Act
        result = runner.invoke(app, ['structure', '--format', 'json', nonexistent_uuid])

        # Assert
        assert result.exit_code == 1
        assert 'Error: Node not found in binder:' in result.output
        assert nonexistent_uuid in result.output

"""Contract tests for structure command with node_id parameter.

These tests verify the CLI contract as specified in the contracts/cli-interface.md.
Tests the command signature, parameter validation, and expected behavior.
"""

import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from prosemark.cli.main import app

runner = CliRunner()


class TestStructureCommandContract:
    """Test structure command contract with node_id parameter."""

    @pytest.fixture
    def project_with_binder(self) -> Generator[Path, None, None]:
        """Create a test project with binder for contract testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create test binder
            binder_content = """# Project Structure

<!-- BEGIN_MANAGED_BLOCK -->
- [Test Book](01996e70-e27d-7ada-908e-ef3b5ddb5223.md)
  - [Test Chapter](01997898-1dca-74d7-a727-b9a7023d0866.md)
    - [Test Scene](01997898-1dcf-7bb2-806d-3c29d1ee5ed1.md)
<!-- END_MANAGED_BLOCK -->
"""
            binder_file = project_path / '_binder.md'
            binder_file.write_text(binder_content)

            yield project_path

    def test_command_signature_with_node_id(self, project_with_binder: Path) -> None:
        """Test the command signature: pmk structure [OPTIONS] [NODE_ID].

        Given: The CLI contract specifies optional NODE_ID argument
        When: Command is invoked with a UUID node_id
        Then: Should accept and process the node_id
        """
        node_id = '01997898-1dca-74d7-a727-b9a7023d0866'

        # Act
        result = runner.invoke(app, ['structure', '--path', str(project_with_binder), node_id])

        # Assert
        assert result.exit_code == 0
        assert 'Test Chapter' in result.output

    def test_node_id_format_validation(self, project_with_binder: Path) -> None:
        """Test NODE_ID format validation per contract.

        Given: Contract specifies UUID v7 format for NODE_ID
        When: Invalid format is provided
        Then: Should return exit code 1 with error message
        """
        # Test various invalid formats
        invalid_ids = [
            'invalid-id',  # Not a UUID
            '12345',  # Just numbers
            'abc-def-ghi',  # Wrong format
            '',  # Empty string
        ]

        for invalid_id in invalid_ids:
            result = runner.invoke(app, ['structure', '--path', str(project_with_binder), invalid_id])
            assert result.exit_code == 1, f'Should reject invalid ID: {invalid_id}'
            assert 'Invalid' in result.output or 'Error' in result.output

    def test_node_id_optional_parameter(self, project_with_binder: Path) -> None:
        """Test that NODE_ID is optional per contract.

        Given: Contract specifies NODE_ID as optional
        When: Command is run without NODE_ID
        Then: Should display full tree (backward compatibility)
        """
        # Act without node_id
        result = runner.invoke(app, ['structure', '--path', str(project_with_binder)])

        # Assert
        assert result.exit_code == 0
        assert 'Project Structure:' in result.output
        assert 'Test Book' in result.output

    def test_format_option_with_node_id(self, project_with_binder: Path) -> None:
        """Test --format option works with NODE_ID.

        Given: Contract allows --format option with NODE_ID
        When: Both are provided
        Then: Should output subtree in specified format
        """
        node_id = '01996e70-e27d-7ada-908e-ef3b5ddb5223'

        # Test tree format (default)
        result = runner.invoke(app, ['structure', '--format', 'tree', '--path', str(project_with_binder), node_id])
        assert result.exit_code == 0
        assert 'Test Book' in result.output

        # Test JSON format
        result = runner.invoke(app, ['structure', '--format', 'json', '--path', str(project_with_binder), node_id])
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail('JSON format should produce valid JSON')

    def test_error_response_node_not_found(self, project_with_binder: Path) -> None:
        """Test error response for non-existent node per contract.

        Given: Contract specifies error for non-existent nodes
        When: Valid UUID that doesn't exist is provided
        Then: Exit code 1 with specific error message
        """
        nonexistent_id = '01996e70-aaaa-7ada-908e-ef3b5ddb5999'

        # Act
        result = runner.invoke(app, ['structure', '--path', str(project_with_binder), nonexistent_id])

        # Assert per contract
        assert result.exit_code == 1
        assert 'not found' in result.output.lower()
        assert nonexistent_id in result.output

    def test_path_option_with_node_id(self, project_with_binder: Path) -> None:
        """Test --path option works with NODE_ID.

        Given: Contract allows --path option
        When: Used with NODE_ID
        Then: Should use specified project directory
        """
        node_id = '01996e70-e27d-7ada-908e-ef3b5ddb5223'

        # Act with explicit path
        result = runner.invoke(app, ['structure', '--path', str(project_with_binder), node_id])

        # Assert
        assert result.exit_code == 0
        assert 'Test Book' in result.output

    def test_help_text_mentions_node_id(self) -> None:
        """Test that help text documents NODE_ID parameter.

        Given: Contract specifies NODE_ID parameter
        When: --help is invoked
        Then: Should document the NODE_ID parameter
        """
        # Act
        result = runner.invoke(app, ['structure', '--help'])

        # Assert
        assert result.exit_code == 0
        # Should mention NODE_ID or node in help
        # Note: This will fail initially until implementation updates help text
        assert 'NODE_ID' in result.output or 'node' in result.output.lower() or '[ARGUMENTS]' in result.output

    def test_success_indicators(self, project_with_binder: Path) -> None:
        """Test success indicators per contract.

        Given: Contract specifies exit code 0 for success
        When: Valid operations are performed
        Then: Should return exit code 0
        """
        # Test various successful operations
        test_cases = [
            # No node_id
            ['structure', '--path', str(project_with_binder)],
            # With valid node_id
            ['structure', '--path', str(project_with_binder), '01996e70-e27d-7ada-908e-ef3b5ddb5223'],
            # With format option
            ['structure', '--format', 'json', '--path', str(project_with_binder)],
        ]

        for args in test_cases:
            result = runner.invoke(app, args)
            assert result.exit_code == 0, f'Should succeed for: {args}'

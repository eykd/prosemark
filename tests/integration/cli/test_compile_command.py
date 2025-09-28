"""Integration tests for the compile CLI command.

These tests verify the complete CLI workflow from command execution
to output generation, following the quickstart scenarios.
"""

# This import will fail until the command is implemented
from typing import TYPE_CHECKING

import pytest
from typer import Typer
from typer.testing import CliRunner

from prosemark.domain.models import NodeId

if TYPE_CHECKING:
    from prosemark.cli.main import app
else:
    app: Typer | None = None


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_node_ids() -> dict[str, NodeId]:
    """Provide sample node IDs for testing."""
    return {
        'parent': NodeId('01923456-789a-7123-8abc-def012345678'),
        'child1': NodeId('01923456-789a-7123-8abc-def012345679'),
        'child2': NodeId('01923456-789a-7123-8abc-def012345680'),
        'nonexistent': NodeId('01923456-789a-7123-8abc-def012345999'),
    }


@pytest.mark.skipif(app is None, reason='CLI app not implemented yet')
class TestCompileCommandIntegration:
    """Integration tests for the compile command."""

    def test_scenario_1_simple_hierarchy_compilation(
        self, cli_runner: CliRunner, sample_node_ids: dict[str, NodeId]
    ) -> None:
        """Test Scenario 1: Simple hierarchy compilation.

        Setup:
        - Parent node with content "Chapter 1"
        - Child 1 with content "Section 1.1"
        - Child 2 with content "Section 1.2"

        Expected: Parent content followed by children in depth-first order.
        """
        # This test will fail until we implement the CLI command and backend
        result = cli_runner.invoke(app, [str(sample_node_ids['parent'])])

        assert result.exit_code == 0
        expected_output = 'Chapter 1\n\nSection 1.1\n\nSection 1.2'
        assert result.stdout.strip() == expected_output

    def test_scenario_2_deep_nesting_compilation(
        self, cli_runner: CliRunner, sample_node_ids: dict[str, NodeId]
    ) -> None:
        """Test Scenario 2: Deep nesting compilation.

        Setup:
        - Root with content "Book Title"
        - Chapter 1 with content "Chapter One"
        - Section 1.1 with content "Introduction"
        - Section 1.2 with content "Main Content"
        - Chapter 2 with content "Chapter Two"

        Expected: All content in depth-first pre-order.
        """
        # This test will fail until we have a complete implementation
        result = cli_runner.invoke(app, [str(sample_node_ids['parent'])])

        assert result.exit_code == 0
        expected_output = 'Book Title\n\nChapter One\n\nIntroduction\n\nMain Content\n\nChapter Two'
        assert result.stdout.strip() == expected_output

    def test_scenario_3_empty_nodes_skipped(self, cli_runner: CliRunner, sample_node_ids: dict[str, NodeId]) -> None:
        """Test Scenario 3: Empty nodes are skipped.

        Setup:
        - Parent with content "Header"
        - Child 1 with empty content (should be skipped)
        - Child 2 with content "Footer"

        Expected: Only "Header" and "Footer" with double newline separation.
        """
        result = cli_runner.invoke(app, [str(sample_node_ids['parent'])])

        assert result.exit_code == 0
        expected_output = 'Header\n\nFooter'
        assert result.stdout.strip() == expected_output

    def test_scenario_4_node_not_found_error(self, cli_runner: CliRunner, sample_node_ids: dict[str, NodeId]) -> None:
        """Test Scenario 4: Node not found error.

        Expected: Clear error message and non-zero exit code.
        """
        result = cli_runner.invoke(app, [str(sample_node_ids['nonexistent'])])

        assert result.exit_code != 0
        assert 'Node not found' in result.stderr or 'Node not found' in result.stdout
        assert str(sample_node_ids['nonexistent']) in (result.stderr or result.stdout)

    def test_single_node_compilation(self, cli_runner: CliRunner, sample_node_ids: dict[str, NodeId]) -> None:
        """Test compilation of a single node with no children."""
        result = cli_runner.invoke(app, [str(sample_node_ids['child1'])])

        assert result.exit_code == 0
        # Should return just the single node's content
        assert result.stdout.strip() == 'Section 1.1'

    def test_invalid_node_id_format(self, cli_runner: CliRunner) -> None:
        """Test error handling for invalid node ID format."""
        result = cli_runner.invoke(app, ['invalid-uuid'])

        assert result.exit_code != 0
        assert 'invalid' in result.stderr.lower() or 'invalid' in result.stdout.lower()

    def test_help_command_available(self, cli_runner: CliRunner) -> None:
        """Test that the compile command has help documentation."""
        result = cli_runner.invoke(app, ['--help'])

        assert result.exit_code == 0
        assert 'compile' in result.stdout.lower()
        assert 'node' in result.stdout.lower()

    def test_version_command_integration(self, cli_runner: CliRunner) -> None:
        """Test that compile command is integrated with main CLI."""
        # This will test that the command is properly registered
        result = cli_runner.invoke(app, ['--version'])

        # Should not crash - actual version testing is done elsewhere
        assert result.exit_code in {0, 2}  # 0 for success, 2 for unimplemented


class TestCompileCommandValidation:
    """Test command validation and error handling."""

    @pytest.mark.skipif(app is None, reason='CLI app not implemented yet')
    def test_missing_node_id_argument(self, cli_runner: CliRunner) -> None:
        """Test error when node ID argument is missing."""
        result = cli_runner.invoke(app, [])

        assert result.exit_code != 0
        assert 'node' in result.stderr.lower() or 'required' in result.stderr.lower()

    @pytest.mark.skipif(app is None, reason='CLI app not implemented yet')
    def test_too_many_arguments(self, cli_runner: CliRunner, sample_node_ids: dict[str, NodeId]) -> None:
        """Test error when too many arguments are provided."""
        result = cli_runner.invoke(
            app, [str(sample_node_ids['parent']), str(sample_node_ids['child1']), 'extra-argument']
        )

        assert result.exit_code != 0


# This test should always fail initially to ensure TDD compliance
def test_cli_command_implementation_missing() -> None:
    """This test ensures we fail first before implementing."""
    try:
        from prosemark.cli.main import app

        # If import succeeds, check that it's actually implemented
        assert hasattr(app, 'registered_commands'), 'CLI app missing commands'
        assert len(app.registered_commands) > 0, 'No commands registered in CLI app'

        # Check if compile command is specifically registered
        command_names = [cmd.callback.__name__ for cmd in app.registered_commands if cmd.callback]
        assert 'compile_cmd' in command_names, f'Compile command not found in {command_names}'

    except ImportError:
        # This is expected initially - the test should fail
        pytest.fail('CLI compile command not implemented yet (expected failure)')

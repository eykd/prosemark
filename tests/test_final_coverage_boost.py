"""Final tests to reach 100% coverage for specific edge cases."""

from typing import cast

import pytest

from prosemark.domain.batch_materialize_result import BatchMaterializeResult
from prosemark.domain.materialize_failure import MaterializeFailure
from prosemark.domain.materialize_result import MaterializeResult
from prosemark.domain.models import NodeId
from prosemark.domain.placeholder_summary import PlaceholderSummary


class TestFinalCoverageBoost:
    """Test remaining uncovered edge cases."""

    def test_batch_result_complete_success_summary(self) -> None:
        """Test summary message for complete success case."""
        # Missing line 92 in batch_materialize_result.py
        result = BatchMaterializeResult(
            total_placeholders=2,
            successful_materializations=[
                MaterializeResult(
                    display_title='Success1',
                    node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                    file_paths=[
                        '01234567-89ab-7def-8123-456789abcdef.md',
                        '01234567-89ab-7def-8123-456789abcdef.notes.md',
                    ],
                    position='[0]',
                ),
                MaterializeResult(
                    display_title='Success2',
                    node_id=NodeId('01234567-89ab-7def-8123-456789abceef'),
                    file_paths=[
                        '01234567-89ab-7def-8123-456789abceef.md',
                        '01234567-89ab-7def-8123-456789abceef.notes.md',
                    ],
                    position='[1]',
                ),
            ],
            failed_materializations=[],
            execution_time=1.0,
        )

        assert result.is_complete_success is True
        assert result.summary_message() == 'Successfully materialized all 2 placeholders'

    def test_batch_result_execution_time_validation(self) -> None:
        """Test validation of negative execution time."""
        # Lines 47-49 in batch_materialize_result.py
        with pytest.raises(ValueError, match='Execution time must be non-negative'):
            BatchMaterializeResult(
                total_placeholders=0,
                successful_materializations=[],
                failed_materializations=[],
                execution_time=-1.0,  # Negative execution time
            )

    def test_materialize_failure_formatted_error_without_position(self) -> None:
        """Test formatted error without position."""
        # Missing line 84 in materialize_failure.py
        failure = MaterializeFailure(
            display_title='Test Title',
            error_type='filesystem',
            error_message='File creation failed',
            position=None,  # No position
        )
        assert failure.formatted_error() == "✗ Failed to materialize 'Test Title': File creation failed"

    def test_materialize_result_invalid_uuid7_validation(self) -> None:
        """Test MaterializeResult validation with invalid UUIDv7."""
        # Missing lines 41-42 in materialize_result.py
        # We need to create a NodeId that passes NodeId validation but fails MaterializeResult validation
        # This is tricky since NodeId already validates UUIDv7

        # Let's test by creating a MaterializeResult with a valid UUID6 instead
        # First create a valid UUID6 in NodeId format
        from dataclasses import dataclass

        @dataclass
        class MockNodeId:
            value: str

        mock_node_id = MockNodeId('01234567-89ab-6def-8123-456789abcdef')  # Version 6, not 7

        with pytest.raises(ValueError, match='Node ID must be valid UUIDv7'):
            MaterializeResult(
                display_title='Test',
                node_id=cast('NodeId', mock_node_id),
                file_paths=['01234567-89ab-6def-8123-456789abcdef.md', '01234567-89ab-6def-8123-456789abcdef.notes.md'],
                position='[0]',
            )

    def test_placeholder_summary_hierarchy_path_without_parent(self) -> None:
        """Test hierarchy path without parent."""
        # Missing line 73 in placeholder_summary.py
        placeholder = PlaceholderSummary(display_title='Root Item', position='[0]', parent_title=None, depth=0)
        assert placeholder.hierarchy_path == 'Root Item'

    def test_placeholder_summary_str_without_parent(self) -> None:
        """Test string representation without parent."""
        # Missing line 94 in placeholder_summary.py
        placeholder = PlaceholderSummary(display_title='Root Item', position='[0]', parent_title=None, depth=0)
        assert str(placeholder) == "'Root Item' (depth=0)"


class TestCLIMainEdgeCases:
    """Test remaining CLI edge cases."""

    def test_get_summary_message_plural_failures_else_branch(self) -> None:
        """Test the else branch for plural failures in summary message generation."""
        # Missing line 592 in cli/main.py
        from prosemark.cli.main import _get_summary_message

        # Create a result with multiple failures to hit the else branch (plural)
        result = BatchMaterializeResult(
            total_placeholders=4,
            successful_materializations=[
                MaterializeResult(
                    display_title='Success',
                    node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                    file_paths=[
                        '01234567-89ab-7def-8123-456789abcdef.md',
                        '01234567-89ab-7def-8123-456789abcdef.notes.md',
                    ],
                    position='[0]',
                )
            ],
            failed_materializations=[
                MaterializeFailure('Failed1', 'filesystem', 'Error1', '[1]'),
                MaterializeFailure('Failed2', 'validation', 'Error2', '[2]'),
                MaterializeFailure('Failed3', 'filesystem', 'Error3', '[3]'),
            ],
            execution_time=1.0,
        )

        # This should hit the else branch for plural failures (line 592)
        message = _get_summary_message(result, 1)
        assert 'failures)' in message
        assert message == 'Materialized 1 of 4 placeholders (3 failures)'

    def test_materialize_title_none_error_handling(self) -> None:
        """Test handling when title is None in materialize function."""
        # Missing lines 643-644 in cli/main.py
        from pathlib import Path
        from unittest.mock import patch

        import typer

        from prosemark.cli.main import materialize

        with patch('prosemark.cli.main._get_project_root', return_value=Path('/test')):  # noqa: SIM117
            with patch('prosemark.cli.main.BinderRepoFs'):
                with patch('prosemark.cli.main.NodeRepoFs'):
                    with patch('prosemark.cli.main.IdGeneratorUuid7'):
                        with patch('prosemark.cli.main.ClockSystem'):
                            with patch('prosemark.cli.main.LoggerStdout'):
                                with pytest.raises(typer.Exit) as exc_info:
                                    materialize(
                                        title=None,  # This triggers the error
                                        all_placeholders=False,
                                        _parent=None,
                                        json_output=False,
                                        path=None,
                                    )
                                assert exc_info.value.exit_code == 1

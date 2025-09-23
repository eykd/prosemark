"""Targeted tests for the specific missing lines in CLI main.py."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from prosemark.cli.main import _get_summary_message, materialize
from prosemark.domain.batch_materialize_result import BatchMaterializeResult
from prosemark.domain.materialize_failure import MaterializeFailure


class TestCliMainTargetedCoverage:
    """Targeted tests for the exact missing lines."""

    def test_get_summary_message_with_zero_failures(self) -> None:
        """Test line 592 with 0 failures (plural path)."""
        # Create a valid result with successes to match total, but 0 failures
        from prosemark.domain.materialize_result import MaterializeResult
        from prosemark.domain.models import NodeId

        successes = [
            MaterializeResult(
                display_title='Success1',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
                position='[0]',
            ),
            MaterializeResult(
                display_title='Success2',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdee'),
                file_paths=['01234567-89ab-7def-8123-456789abcdee.md', '01234567-89ab-7def-8123-456789abcdee.notes.md'],
                position='[1]',
            ),
        ]
        result = BatchMaterializeResult(
            total_placeholders=2,
            successful_materializations=successes,
            failed_materializations=[],  # 0 failures
            execution_time=1.0,
        )

        # Mock the safe attribute retrieval to return empty for message
        with patch('prosemark.cli.main._get_safe_attribute', return_value=''):
            summary = _get_summary_message(result, 2)
            # When failure_count = 0, it should say "failures" (plural)
            assert 'failures)' in summary
            assert summary == 'Materialized 2 of 2 placeholders (0 failures)'

    def test_get_summary_message_with_multiple_failures(self) -> None:
        """Test line 592 with 2+ failures (plural path)."""
        # Create a result with 2 failures and 1 success to hit the else branch (line 592)
        from prosemark.domain.materialize_result import MaterializeResult
        from prosemark.domain.models import NodeId

        successes = [
            MaterializeResult(
                display_title='Success1',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
                position='[0]',
            ),
        ]
        failures = [
            MaterializeFailure('Failed1', 'filesystem', 'Error1', '[1]'),
            MaterializeFailure('Failed2', 'validation', 'Error2', '[2]'),
        ]
        result = BatchMaterializeResult(
            total_placeholders=3,
            successful_materializations=successes,
            failed_materializations=failures,  # 2 failures != 1
            execution_time=1.0,
        )

        # Mock the safe attribute retrieval to return empty for message
        with patch('prosemark.cli.main._get_safe_attribute', return_value=''):
            summary = _get_summary_message(result, 1)
            # When failure_count = 2, it should say "failures" (plural)
            assert 'failures)' in summary
            assert summary == 'Materialized 1 of 3 placeholders (2 failures)'

    def test_materialize_command_title_none_in_single_mode(self) -> None:
        """Test lines 643-644 where title is None but should not be."""
        # This tests the defensive check for when validation somehow fails
        # We need to bypass the validation and get to the defensive check

        # Mock all the dependencies to isolate the specific code path
        with (
            patch('prosemark.cli.main._validate_materialize_args'),  # Skip validation
            patch('prosemark.cli.main._get_project_root', return_value=Path('/test')),
            patch(
                'prosemark.cli.main._create_shared_dependencies',
                return_value=(Mock(), Mock(), Mock(), Mock(), Mock(), Mock()),
            ),
            pytest.raises(typer.Exit) as exc_info,
        ):
            # This should trigger the defensive check on lines 643-644
            materialize(
                title=None,  # This is None
                all_placeholders=False,  # Not all placeholders, so single mode
                _parent=None,
                json_output=False,
                path=None,
            )
        assert exc_info.value.exit_code == 1

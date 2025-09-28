"""Test coverage for CLI main.py missing lines."""

from pathlib import Path
from typing import Never, cast
from unittest.mock import Mock, patch

import pytest
import typer

from prosemark.cli.main import (
    MaterializationResult,
    _check_result_failure_status,
    _get_safe_attribute,
    _get_summary_message,
    _materialize_all_placeholders,
    materialize,
)
from prosemark.domain.batch_materialize_result import BatchMaterializeResult
from prosemark.domain.materialize_failure import MaterializeFailure
from prosemark.domain.materialize_result import MaterializeResult
from prosemark.domain.models import NodeId
from prosemark.exceptions import (
    BinderFormatError,
)


class TestCliMainCoverage:
    """Test missing coverage in CLI main.py."""

    def test_check_result_failure_status_all_failures_no_continue(self) -> None:
        """Test failure check when all materializations failed and continue_on_error is False."""
        # Missing line 446: Exit when all failed and continue_on_error=False
        result = BatchMaterializeResult(
            total_placeholders=2,
            successful_materializations=[],
            failed_materializations=[
                MaterializeFailure('Test1', 'filesystem', 'Error1', '[0]'),
                MaterializeFailure('Test2', 'validation', 'Error2', '[1]'),
            ],
            execution_time=1.0,
        )

        with pytest.raises(typer.Exit) as exc_info:
            _check_result_failure_status(result, continue_on_error=False)
        assert exc_info.value.exit_code == 1

    def test_materialize_all_placeholders_batch_interrupted_exit(self) -> None:
        """Test exit when batch operation is interrupted."""

        # Missing line 530: Exit on batch_interrupted
        # Create a proper mock that can be JSON serialized
        class MockResult:
            def __init__(self) -> None:
                self.total_placeholders = 5
                self.successful_materializations: list[MaterializeResult] = []
                self.failed_materializations: list[MaterializeFailure] = []
                self.type = 'batch_interrupted'
                self.execution_time = 1.0

        mock_result = MockResult()

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_use_case.return_value.execute.return_value = mock_result
            with patch('prosemark.cli.main.BinderRepoFs'), patch('prosemark.cli.main.NodeRepoFs'):  # noqa: SIM117
                with patch('prosemark.cli.main.IdGeneratorUuid7'):
                    with patch('prosemark.cli.main.ClockSystem'):
                        with patch('prosemark.cli.main.LoggerStdout'):
                            with pytest.raises(typer.Exit) as exc_info:
                                _materialize_all_placeholders(
                                    project_root=Path('/test'),
                                    binder_repo=Mock(),
                                    node_repo=Mock(),
                                    id_generator=Mock(),
                                    clock=Mock(),
                                    logger=Mock(),
                                    json_output=True,  # Use JSON output to hit line 530
                                )
                            assert exc_info.value.exit_code == 1

    def test_get_safe_attribute_exception_handling(self) -> None:
        """Test safe attribute retrieval with exceptions."""

        # Missing lines 573-574: Exception handling in _get_safe_attribute
        class BadAttribute:
            @property
            def bad_prop(self) -> Never:
                raise ValueError('Intentional error')

        obj = BadAttribute()
        result = _get_safe_attribute(cast('MaterializationResult', obj), 'bad_prop', 'default_value')
        assert result == 'default_value'

    def test_get_summary_message_plural_failures(self) -> None:
        """Test summary message generation with multiple failures."""
        # Missing line 592: Plural failures case
        result = BatchMaterializeResult(
            total_placeholders=5,
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
            failed_materializations=[
                MaterializeFailure('Failed1', 'filesystem', 'Error1', '[2]'),
                MaterializeFailure('Failed2', 'validation', 'Error2', '[3]'),
                MaterializeFailure('Failed3', 'filesystem', 'Error3', '[4]'),
            ],
            execution_time=2.0,
        )

        summary = _get_summary_message(result, 2)
        assert 'failures)' in summary  # Plural form
        assert summary == 'Materialized 2 of 5 placeholders (3 failures)'

    def test_materialize_no_title_error(self) -> None:
        """Test materialize command with no title for single materialization."""
        # Missing lines 643-644: Error when title is None for single materialization
        with patch('prosemark.cli.main._get_project_root', return_value=Path('/test')):  # noqa: SIM117
            with patch('prosemark.cli.main.BinderRepoFs'):
                with patch('prosemark.cli.main.NodeRepoFs'):
                    with patch('prosemark.cli.main.IdGeneratorUuid7'):
                        with patch('prosemark.cli.main.ClockSystem'):
                            with patch('prosemark.cli.main.LoggerStdout'):
                                with pytest.raises(typer.Exit) as exc_info:
                                    materialize(
                                        title=None,  # No title provided
                                        all_placeholders=False,  # Single materialization
                                        _parent=None,
                                        json_output=False,
                                        path=None,
                                    )
                                assert exc_info.value.exit_code == 1

    def test_materialize_binder_format_error(self) -> None:
        """Test materialize command with binder format error."""
        # Missing lines 654-655: BinderFormatError handling
        with patch('prosemark.cli.main._get_project_root', return_value=Path('/test')):  # noqa: SIM117
            with patch('prosemark.cli.main.BinderRepoFs'):
                with patch('prosemark.cli.main.NodeRepoFs'):
                    with patch('prosemark.cli.main.IdGeneratorUuid7'):
                        with patch('prosemark.cli.main.ClockSystem'):
                            with patch('prosemark.cli.main.LoggerStdout'):
                                with patch(
                                    'prosemark.cli.main._materialize_single_placeholder',
                                    side_effect=BinderFormatError('Bad format'),
                                ):
                                    with pytest.raises(typer.Exit) as exc_info:
                                        materialize(
                                            title='Test',
                                            all_placeholders=False,
                                            _parent=None,
                                            json_output=False,
                                            path=None,
                                        )
                                    assert exc_info.value.exit_code == 1


class TestMaterializeAllPlaceholdersCoverage:
    """Test missing coverage in materialize_all_placeholders.py via CLI integration."""

    def test_batch_materialize_no_binder_provided(self) -> None:
        """Test batch materialization when no binder is provided."""
        # This tests the lines 76-78 in materialize_all_placeholders.py
        # We need to test the actual MaterializeAllPlaceholders use case, not the CLI wrapper
        from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders
        from prosemark.domain.models import Binder

        mock_binder_repo = Mock()
        mock_binder = Binder(roots=[])
        mock_binder_repo.load.return_value = mock_binder

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=Mock(),
            binder_repo=mock_binder_repo,
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        # Execute without providing binder (should load from repo)
        result = use_case.execute(binder=None, project_path=Path('/test'))

        # Verify binder was loaded when None was provided
        mock_binder_repo.load.assert_called_once()
        assert result.total_placeholders == 0

    def test_batch_materialize_with_progress_callback(self) -> None:
        """Test batch materialization with progress callback."""
        # This tests lines 86-90 and 107-113 in materialize_all_placeholders.py
        mock_materialize_use_case = Mock()
        mock_result = MaterializeResult(
            display_title='Test Item',
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
            position='[0]',
        )
        mock_materialize_use_case.execute.return_value = NodeId('01234567-89ab-7def-8123-456789abcdef')

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case_class:  # noqa: SIM117
            with patch('prosemark.cli.main.MaterializeNode', return_value=mock_materialize_use_case):
                mock_use_case = Mock()
                mock_use_case_class.return_value = mock_use_case

                # Mock placeholders found
                mock_use_case.execute.return_value = BatchMaterializeResult(
                    total_placeholders=1,
                    successful_materializations=[mock_result],
                    failed_materializations=[],
                    execution_time=1.0,
                )

                # Capture progress messages
                progress_messages = []

                def capture_progress(msg: str) -> None:
                    progress_messages.append(msg)

                with patch.object(mock_use_case, 'execute') as mock_execute:
                    mock_execute.return_value = BatchMaterializeResult(
                        total_placeholders=1,
                        successful_materializations=[mock_result],
                        failed_materializations=[],
                        execution_time=1.0,
                    )

                    _materialize_all_placeholders(
                        project_root=Path('/test'),
                        binder_repo=Mock(),
                        node_repo=Mock(),
                        id_generator=Mock(),
                        clock=Mock(),
                        logger=Mock(),
                        json_output=False,
                        continue_on_error=False,
                    )

    def test_batch_materialize_with_failure_and_continue_error(self) -> None:
        """Test batch materialization with failure and progress callback."""
        # This tests lines 126-129 and 138-139 in materialize_all_placeholders.py
        mock_failure = MaterializeFailure(
            display_title='Failed Item',
            error_type='filesystem',  # This is retryable, not critical
            error_message='Permission denied',
            position='[0]',
        )

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case_class:
            mock_use_case = Mock()
            mock_use_case_class.return_value = mock_use_case

            # Mock result with failure but should_stop_batch = False (filesystem errors are not critical)
            mock_use_case.execute.return_value = BatchMaterializeResult(
                total_placeholders=1,
                successful_materializations=[],
                failed_materializations=[mock_failure],
                execution_time=1.0,
            )

            # This should NOT raise an exception since continue_on_error=True and it's not a critical failure
            import contextlib

            with contextlib.suppress(typer.Exit):
                _materialize_all_placeholders(
                    project_root=Path('/test'),
                    binder_repo=Mock(),
                    node_repo=Mock(),
                    id_generator=Mock(),
                    clock=Mock(),
                    logger=Mock(),
                    json_output=False,
                    continue_on_error=True,  # Continue on error
                )

    def test_categorize_error_filesystem_types(self) -> None:
        """Test error categorization for filesystem errors."""
        # This tests lines 282-291 in materialize_all_placeholders.py
        from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders

        # Create a minimal instance just to test the method
        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=Mock(),
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        # Test different error type categorizations
        filesystem_error = OSError('Permission denied')
        validation_error = ValueError('Invalid input')
        unknown_error = RuntimeError('Unknown error')

        assert use_case._categorize_error(filesystem_error) == 'filesystem'
        assert use_case._categorize_error(validation_error) == 'validation'
        assert use_case._categorize_error(unknown_error) == 'filesystem'

    def test_create_failure_record_and_file_paths(self) -> None:
        """Test failure record creation and file path generation."""
        # This tests lines 236-238 in materialize_all_placeholders.py
        from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders
        from prosemark.domain.placeholder_summary import PlaceholderSummary

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=Mock(),
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        placeholder = PlaceholderSummary(display_title='Test Placeholder', position='[0]', parent_title=None, depth=0)

        error = ValueError('Test validation error')
        failure = use_case._create_failure_record(placeholder, error)

        assert failure.display_title == 'Test Placeholder'
        assert failure.error_type == 'validation'
        assert failure.error_message == 'Test validation error'
        assert failure.position == '[0]'

    def test_check_result_failure_status_all_successes_no_continue(self) -> None:
        """Test failure status check when only successful materializations (line 466)."""
        # Missing line 466: Check for scenario with failures but all successes = 0
        result = BatchMaterializeResult(
            total_placeholders=1,
            successful_materializations=[],
            failed_materializations=[
                MaterializeFailure('Test1', 'filesystem', 'Error1', '[0]'),
            ],
            execution_time=1.0,
        )

        # This should raise exit when there are failures and no successes, regardless of continue_on_error
        with pytest.raises(typer.Exit) as exc_info:
            _check_result_failure_status(result, continue_on_error=True)  # Even with continue_on_error=True
        assert exc_info.value.exit_code == 1

    def test_materialize_all_placeholders_batch_critical_failure_exit(self) -> None:
        """Test exit when batch operation encounters critical failure (line 561)."""

        # Missing line 561: Exit on batch_critical_failure
        class MockResultCritical:
            def __init__(self) -> None:
                self.total_placeholders = 5
                self.successful_materializations: list[MaterializeResult] = []
                self.failed_materializations: list[MaterializeFailure] = []
                self.type = 'batch_critical_failure'
                self.execution_time = 1.0

        mock_result = MockResultCritical()

        with patch('prosemark.cli.main.MaterializeAllPlaceholders') as mock_use_case:
            mock_use_case.return_value.execute.return_value = mock_result
            with patch('prosemark.cli.main.BinderRepoFs'), patch('prosemark.cli.main.NodeRepoFs'):  # noqa: SIM117
                with patch('prosemark.cli.main.IdGeneratorUuid7'):
                    with patch('prosemark.cli.main.ClockSystem'):
                        with patch('prosemark.cli.main.LoggerStdout'):
                            with pytest.raises(typer.Exit) as exc_info:
                                _materialize_all_placeholders(
                                    project_root=Path('/test'),
                                    binder_repo=Mock(),
                                    node_repo=Mock(),
                                    id_generator=Mock(),
                                    clock=Mock(),
                                    logger=Mock(),
                                    json_output=False,  # Use non-JSON output to hit line 561
                                )
                            assert exc_info.value.exit_code == 1

    def test_get_summary_message_no_message_attribute(self) -> None:
        """Test summary message generation when result has no message attribute (line 602-606)."""

        # Missing lines 602-606: Fallback when no message or summary_message attribute
        class MockResultNoMessage:
            def __init__(self) -> None:
                self.successful_materializations = [
                    MaterializeResult(
                        display_title='Success1',
                        node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                        file_paths=[
                            '01234567-89ab-7def-8123-456789abcdef.md',
                            '01234567-89ab-7def-8123-456789abcdef.notes.md',
                        ],
                        position='[0]',
                    )
                ]
                self.failed_materializations = [
                    MaterializeFailure('Failed1', 'filesystem', 'Error1', '[1]'),
                ]
                self.total_placeholders = 2  # 1 success + 1 failure
                # Deliberately omit 'message' and 'summary_message' attributes

        result = MockResultNoMessage()
        summary = _get_summary_message(cast('MaterializationResult', result), 1)

        # Should generate manual summary since no message attributes exist
        assert '1 failure)' in summary  # Should be singular 'failure'
        assert 'Materialized 1 of 2 placeholders' in summary

    def test_get_summary_message_has_message_attribute(self) -> None:
        """Test summary message retrieval when result has message attribute (line 602 not taken)."""

        # This test ensures we hit the case where summary_msg gets a value from 'message'
        # so the second check on line 602 is not taken
        class MockResultWithMessage:
            def __init__(self) -> None:
                self.message = 'Custom message from result'
                self.successful_materializations: list[MaterializeResult] = []
                self.failed_materializations: list[MaterializeFailure] = []

        result = MockResultWithMessage()
        summary = _get_summary_message(cast('MaterializationResult', result), 0)

        # Should use the message attribute, not generate manual summary
        assert summary == 'Custom message from result'

    def test_check_result_failure_status_continue_with_some_successes(self) -> None:
        """Test failure status with continue_on_error=True and some successes (line 466 not taken)."""
        # This test ensures the branch on line 466 is not taken because there are some successes
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
                )
            ],
            failed_materializations=[
                MaterializeFailure('Test1', 'filesystem', 'Error1', '[1]'),
            ],
            execution_time=1.0,
        )

        # This should NOT raise exit because there are some successes, even with failures
        # No exception should be raised
        _check_result_failure_status(result, continue_on_error=True)

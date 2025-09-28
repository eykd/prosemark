"""Test coverage for MaterializeAllPlaceholders use case missing lines."""

from pathlib import Path
from unittest.mock import Mock, patch

from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.domain.placeholder_summary import PlaceholderSummary


class TestMaterializeAllPlaceholdersCoverage:
    """Test missing coverage in MaterializeAllPlaceholders."""

    def test_execute_with_no_binder_loads_from_repo(self) -> None:
        """Test that when no binder is provided, it loads from repository."""
        # Missing lines 76-78: Load binder when None provided
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

        result = use_case.execute(binder=None, project_path=Path('/test'))

        # Verify binder was loaded from repo
        mock_binder_repo.load.assert_called_once()
        assert result.total_placeholders == 0

    def test_execute_with_progress_callback_for_found_placeholders(self) -> None:
        """Test execution with progress callback when placeholders are found."""
        # Missing lines 86-90: Progress callback when placeholders found
        progress_messages = []

        def capture_progress(msg: str) -> None:
            progress_messages.append(msg)

        # Create binder with one placeholder
        placeholder_item = BinderItem(
            display_title='Test Placeholder',
            node_id=None,  # This makes it a placeholder
            children=[],
        )
        binder = Binder(roots=[placeholder_item])

        # Mock the materialization to succeed
        from prosemark.app.materialize_node import MaterializeResult

        mock_materialize_use_case = Mock()
        mock_node_id = NodeId('01234567-89ab-7def-8123-456789abcdef')
        mock_materialize_use_case.execute.return_value = MaterializeResult(mock_node_id, was_already_materialized=False)

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        result = use_case.execute(binder=binder, project_path=Path('/test'), progress_callback=capture_progress)

        # Check that progress was reported for found placeholders
        assert len(progress_messages) >= 1
        assert 'Found 1 placeholders to materialize' in progress_messages[0]
        assert result.total_placeholders == 1

    def test_execute_successful_materialization_with_progress(self) -> None:
        """Test successful materialization with progress callback."""
        # Missing lines 107-113: Successful materialization progress reporting
        progress_messages = []

        def capture_progress(msg: str) -> None:
            progress_messages.append(msg)

        # Create binder with one placeholder
        placeholder_item = BinderItem(display_title='Test Success', node_id=None, children=[])
        binder = Binder(roots=[placeholder_item])

        # Mock successful materialization
        from prosemark.app.materialize_node import MaterializeResult

        mock_materialize_use_case = Mock()
        mock_node_id = NodeId('01234567-89ab-7def-8123-456789abcdef')
        mock_materialize_use_case.execute.return_value = MaterializeResult(mock_node_id, was_already_materialized=False)

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        use_case.execute(binder=binder, project_path=Path('/test'), progress_callback=capture_progress)

        # Check success progress message
        success_messages = [msg for msg in progress_messages if '✓ Materialized' in msg]
        assert len(success_messages) >= 1
        assert 'Test Success' in success_messages[0]
        assert mock_node_id.value in success_messages[0]

    def test_execute_failed_materialization_with_progress(self) -> None:
        """Test failed materialization with progress callback."""
        # Missing lines 126-129: Failed materialization progress reporting
        progress_messages = []

        def capture_progress(msg: str) -> None:
            progress_messages.append(msg)

        # Create binder with one placeholder
        placeholder_item = BinderItem(display_title='Test Failure', node_id=None, children=[])
        binder = Binder(roots=[placeholder_item])

        # Mock failed materialization
        mock_materialize_use_case = Mock()
        mock_materialize_use_case.execute.side_effect = ValueError('Test error')

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        use_case.execute(binder=binder, project_path=Path('/test'), progress_callback=capture_progress)

        # Check failure progress message
        failure_messages = [msg for msg in progress_messages if '✗ Failed' in msg]
        assert len(failure_messages) >= 1
        assert 'Test Failure' in failure_messages[0]
        assert 'Test error' in failure_messages[0]

    def test_execute_critical_failure_stops_batch(self) -> None:
        """Test that critical failures stop the batch operation."""
        # Missing lines 138-139: Critical error stops batch
        # Create binder with only one placeholder to avoid domain validation issues
        placeholder1 = BinderItem(display_title='Critical Failure Test', node_id=None, children=[])
        binder = Binder(roots=[placeholder1])

        # Mock critical failure on the placeholder
        mock_materialize_use_case = Mock()
        mock_materialize_use_case.execute.side_effect = Exception('Critical system error')

        # Mock logger to capture the critical error log
        mock_logger = Mock()

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=mock_logger,
        )

        # Override _categorize_error to return critical error
        def mock_categorize_error(error: Exception) -> str:
            return 'binder_integrity'  # Critical error type

        with patch.object(MaterializeAllPlaceholders, '_categorize_error', side_effect=mock_categorize_error):
            result = use_case.execute(binder=binder, project_path=Path('/test'))

        # Verify the critical error caused a batch stop
        assert len(result.failed_materializations) == 1
        assert len(result.successful_materializations) == 0
        assert result.total_placeholders == 1
        assert result.failed_materializations[0].should_stop_batch is True

        # Verify the critical error log was called (line 138)
        mock_logger.exception.assert_called_with('Critical error encountered, stopping batch operation')

    def test_materialize_single_placeholder_creates_file_paths(self) -> None:
        """Test that single placeholder materialization creates correct file paths."""
        # Missing lines 236-238: File path creation in _materialize_single_placeholder
        from prosemark.app.materialize_node import MaterializeResult

        mock_materialize_use_case = Mock()
        mock_node_id = NodeId('01234567-89ab-7def-8123-456789abcdef')
        mock_materialize_use_case.execute.return_value = MaterializeResult(mock_node_id, was_already_materialized=False)

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        placeholder = PlaceholderSummary(display_title='Test', position='[0]', parent_title=None, depth=0)

        result = use_case._materialize_single_placeholder(placeholder=placeholder, project_path=Path('/test'))

        # Check file paths are created correctly
        expected_main = f'{mock_node_id.value}.md'
        expected_notes = f'{mock_node_id.value}.notes.md'
        assert expected_main in result.file_paths
        assert expected_notes in result.file_paths
        assert len(result.file_paths) == 2

    def test_progress_callback_success_branch_coverage(self) -> None:
        """Test specific branch coverage for progress callback success reporting (line 110->113)."""
        # This test specifically targets the missing branch coverage for lines 110->113
        progress_called = False
        captured_message = ''

        def test_progress_callback(message: str) -> None:
            nonlocal progress_called, captured_message
            progress_called = True
            captured_message = message

        # Create binder with one placeholder
        placeholder_item = BinderItem(display_title='Branch Test', node_id=None, children=[])
        binder = Binder(roots=[placeholder_item])

        # Mock successful materialization with specific node ID
        from prosemark.app.materialize_node import MaterializeResult

        mock_materialize_use_case = Mock()
        test_node_id = NodeId('01234567-89ab-7def-8123-456789abcdef')
        mock_materialize_use_case.execute.return_value = MaterializeResult(test_node_id, was_already_materialized=False)

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        # Execute with progress callback to trigger the specific branch
        result = use_case.execute(binder=binder, project_path=Path('/test'), progress_callback=test_progress_callback)

        # Verify the specific success branch was executed
        assert progress_called
        assert "✓ Materialized 'Branch Test'" in captured_message
        assert test_node_id.value in captured_message
        assert result.total_placeholders == 1
        assert len(result.successful_materializations) == 1

    def test_progress_callback_none_branch_coverage(self) -> None:
        """Test branch coverage when progress_callback is None (line 110->113)."""
        # This test targets the missing branch coverage for when progress_callback is None
        # Create binder with one placeholder
        placeholder_item = BinderItem(display_title='No Callback Test', node_id=None, children=[])
        binder = Binder(roots=[placeholder_item])

        # Mock successful materialization
        from prosemark.app.materialize_node import MaterializeResult

        mock_materialize_use_case = Mock()
        test_node_id = NodeId('01234567-89ab-7def-8123-456789abcdef')
        mock_materialize_use_case.execute.return_value = MaterializeResult(test_node_id, was_already_materialized=False)

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=mock_materialize_use_case,
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        # Execute without progress callback (should skip the if block and go to line 113)
        result = use_case.execute(binder=binder, project_path=Path('/test'), progress_callback=None)

        # Verify the materialization succeeded without callback
        assert result.total_placeholders == 1
        assert len(result.successful_materializations) == 1

    def test_categorize_error_various_types(self) -> None:
        """Test error categorization for different exception types."""
        # Missing lines 282-291: Error categorization logic
        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=Mock(),
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        # Test filesystem errors
        filesystem_errors = [
            OSError('Permission denied'),
            FileNotFoundError('File not found'),
            PermissionError('Permission denied'),
        ]
        for error in filesystem_errors:
            assert use_case._categorize_error(error) == 'filesystem'

        # Test validation errors - ValueError should map to validation
        validation_error = ValueError('Invalid value')
        assert use_case._categorize_error(validation_error) == 'validation'

        # Test specific ValidationError in the name
        class CustomValidationError(Exception):
            pass

        custom_validation_error = CustomValidationError('Validation failed')
        assert use_case._categorize_error(custom_validation_error) == 'validation'

        # Test ID generation errors
        class UUIDGenerationError(Exception):
            pass

        uuid_error = UUIDGenerationError('UUID generation failed')
        assert use_case._categorize_error(uuid_error) == 'id_generation'

        # Test binder integrity errors
        class BinderIntegrityError(Exception):
            pass

        binder_error = BinderIntegrityError('Binder corrupted')
        assert use_case._categorize_error(binder_error) == 'binder_integrity'

        # Test already materialized errors
        class AlreadyMaterializedError(Exception):
            pass

        already_error = AlreadyMaterializedError('Already exists')
        assert use_case._categorize_error(already_error) == 'already_materialized'

        # Test unknown error defaults to filesystem
        unknown_error = RuntimeError('Unknown error')
        assert use_case._categorize_error(unknown_error) == 'filesystem'

    def test_collect_placeholders_recursive_with_children(self) -> None:
        """Test recursive placeholder collection with nested children (line 218)."""
        # This test specifically targets line 218: the recursive call for children
        from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders
        from prosemark.domain.models import Binder, BinderItem
        from prosemark.domain.placeholder_summary import PlaceholderSummary

        # Create a binder with nested placeholder structure:
        # - Root placeholder (no node_id)
        #   - Child placeholder (no node_id) <- This will trigger the recursive call on line 218
        child_placeholder = BinderItem(
            display_title='Child Placeholder',
            node_id=None,  # This makes it a placeholder
            children=[],
        )

        root_placeholder = BinderItem(
            display_title='Root Placeholder',
            node_id=None,  # This makes it a placeholder
            children=[child_placeholder],  # Has children, will trigger recursive call
        )

        binder = Binder(roots=[root_placeholder])

        use_case = MaterializeAllPlaceholders(
            materialize_node_use_case=Mock(),
            binder_repo=Mock(),
            node_repo=Mock(),
            id_generator=Mock(),
            clock=Mock(),
            logger=Mock(),
        )

        # Call the internal method to collect placeholders
        placeholders: list[PlaceholderSummary] = []
        use_case._collect_placeholders_recursive(
            items=binder.roots,
            placeholders=placeholders,
            parent_title=None,
            depth=0,
            position_path=[],
        )

        # Verify both root and child placeholders are collected
        assert len(placeholders) == 2

        # Verify root placeholder
        root_ph = placeholders[0]
        assert root_ph.display_title == 'Root Placeholder'
        assert root_ph.depth == 0
        assert root_ph.parent_title is None

        # Verify child placeholder (this proves line 218 was executed)
        child_ph = placeholders[1]
        assert child_ph.display_title == 'Child Placeholder'
        assert child_ph.depth == 1
        assert child_ph.parent_title == 'Root Placeholder'

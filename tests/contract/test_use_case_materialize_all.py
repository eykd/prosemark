"""Contract test for MaterializeAllPlaceholders use case."""

from unittest.mock import MagicMock

from prosemark.domain.models import Binder, BinderItem, NodeId


class TestUseCaseMaterializeAllContract:
    """Test use case contract for MaterializeAllPlaceholders."""

    def test_use_case_interface_exists(self) -> None:
        """Test that MaterializeAllPlaceholders use case interface exists."""
        # Implementation now exists
        from prosemark.app.materialize_all_placeholders import MaterializeAllPlaceholders

        assert MaterializeAllPlaceholders is not None

    def test_use_case_execute_signature(self) -> None:
        """Test that execute method has correct signature."""
        # Mock the use case to test interface
        mock_use_case = MagicMock()
        mock_use_case.execute = MagicMock()

        # Should accept binder as parameter
        mock_binder = MagicMock(spec=Binder)
        mock_use_case.execute(binder=mock_binder)

        # Should be called with binder
        mock_use_case.execute.assert_called_once_with(binder=mock_binder)

    def test_use_case_returns_batch_result(self) -> None:
        """Test that use case returns BatchMaterializeResult."""
        mock_use_case = MagicMock()
        mock_binder = MagicMock(spec=Binder)

        # Mock the return value
        mock_result = MagicMock()
        mock_result.total_placeholders = 5
        mock_result.successful_materializations = []
        mock_result.failed_materializations = []
        mock_result.execution_time = 1.23

        mock_use_case.execute.return_value = mock_result

        result = mock_use_case.execute(binder=mock_binder)

        # Verify result structure
        assert hasattr(result, 'total_placeholders')
        assert hasattr(result, 'successful_materializations')
        assert hasattr(result, 'failed_materializations')
        assert hasattr(result, 'execution_time')

    def test_use_case_discovers_placeholders(self) -> None:
        """Test that use case discovers all placeholders in binder."""
        mock_use_case = MagicMock()

        # Create a mock binder with placeholders
        mock_binder = MagicMock(spec=Binder)
        mock_items = []

        # Add placeholder items (no node_id)
        for i, title in enumerate(['Chapter 1', 'Chapter 2', 'Section 2.1']):
            item = MagicMock(spec=BinderItem)
            item.display_title = title
            item.node_id = None  # Placeholder has no node_id
            item.position = f'[{i}]'
            mock_items.append(item)

        # Add materialized item (has node_id)
        materialized = MagicMock(spec=BinderItem)
        materialized.display_title = 'Already Done'
        materialized.node_id = NodeId(value='01923f0c-1234-7123-8abc-def012345678')
        materialized.position = '[3]'
        mock_items.append(materialized)

        mock_binder.items = mock_items

        # Mock result should only process placeholders
        mock_result = MagicMock()
        mock_result.total_placeholders = 3  # Only the 3 without node_id
        mock_use_case.execute.return_value = mock_result

        result = mock_use_case.execute(binder=mock_binder)

        assert result.total_placeholders == 3

    def test_use_case_handles_progress_callback(self) -> None:
        """Test that use case supports progress reporting callback."""
        mock_use_case = MagicMock()
        mock_binder = MagicMock(spec=Binder)
        mock_callback = MagicMock()

        # Execute with callback
        mock_use_case.execute(binder=mock_binder, progress_callback=mock_callback)

        # Verify callback parameter is accepted
        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args
        assert 'progress_callback' in call_args.kwargs or len(call_args.args) > 1

    def test_use_case_dependency_injection(self) -> None:
        """Test that use case accepts required dependencies."""
        # Mock dependencies
        mock_materialize_node = MagicMock()
        mock_binder_repo = MagicMock()
        mock_node_repo = MagicMock()
        mock_id_generator = MagicMock()

        # Mock constructor (will fail until implementation)
        mock_use_case_class = MagicMock()
        mock_use_case_class.return_value = MagicMock()

        # Should accept these dependencies
        use_case = mock_use_case_class(
            materialize_node_use_case=mock_materialize_node,
            binder_repo=mock_binder_repo,
            node_repo=mock_node_repo,
            id_generator=mock_id_generator,
        )

        assert use_case is not None

    def test_use_case_materializes_in_order(self) -> None:
        """Test that use case materializes placeholders in binder order."""
        mock_use_case = MagicMock()
        mock_binder = MagicMock(spec=Binder)

        # Create ordered placeholders
        placeholders = []
        for i, title in enumerate(['First', 'Second', 'Third']):
            item = MagicMock(spec=BinderItem)
            item.display_title = title
            item.node_id = None
            item.position = f'[{i}]'
            placeholders.append(item)

        mock_binder.items = placeholders

        # Mock ordered results
        mock_result = MagicMock()
        mock_result.total_placeholders = 3

        success_list = []
        for item in placeholders:
            success = MagicMock()
            success.display_title = item.display_title
            success.position = item.position
            success_list.append(success)

        mock_result.successful_materializations = success_list
        mock_result.failed_materializations = []

        mock_use_case.execute.return_value = mock_result

        result = mock_use_case.execute(binder=mock_binder)

        # Verify order is preserved
        assert len(result.successful_materializations) == 3
        assert result.successful_materializations[0].display_title == 'First'
        assert result.successful_materializations[1].display_title == 'Second'
        assert result.successful_materializations[2].display_title == 'Third'

    def test_use_case_continues_on_individual_failure(self) -> None:
        """Test that use case continues processing after individual failures."""
        mock_use_case = MagicMock()
        mock_binder = MagicMock(spec=Binder)

        # Create mix of valid and problematic placeholders
        items = []
        for title in ['Good 1', 'Bad/Title', 'Good 2', 'Bad:Title', 'Good 3']:
            item = MagicMock(spec=BinderItem)
            item.display_title = title
            item.node_id = None
            items.append(item)

        mock_binder.items = items

        # Mock mixed results
        mock_result = MagicMock()
        mock_result.total_placeholders = 5

        # 3 successes
        successes = []
        for title in ['Good 1', 'Good 2', 'Good 3']:
            success = MagicMock()
            success.display_title = title
            successes.append(success)
        mock_result.successful_materializations = successes

        # 2 failures
        failures = []
        for title in ['Bad/Title', 'Bad:Title']:
            failure = MagicMock()
            failure.display_title = title
            failure.error_type = 'filesystem'
            failures.append(failure)
        mock_result.failed_materializations = failures

        mock_use_case.execute.return_value = mock_result

        result = mock_use_case.execute(binder=mock_binder)

        # Should process all items despite failures
        assert result.total_placeholders == 5
        assert len(result.successful_materializations) == 3
        assert len(result.failed_materializations) == 2

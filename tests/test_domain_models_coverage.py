"""Test coverage for domain model validation and edge cases."""

import pytest

from prosemark.domain.batch_materialize_result import BatchMaterializeResult
from prosemark.domain.materialize_failure import MaterializeFailure
from prosemark.domain.materialize_result import MaterializeResult
from prosemark.domain.models import NodeId
from prosemark.domain.placeholder_summary import PlaceholderSummary


class TestBatchMaterializeResultCoverage:
    """Test missing coverage in BatchMaterializeResult."""

    def test_validation_error_total_mismatch(self) -> None:
        """Test validation error when total doesn't match actual results."""
        # Missing lines 7-8, 53-54: TYPE_CHECKING import and validation error
        with pytest.raises(ValueError, match='Total placeholders 5 must equal successes 1 \\+ failures 1 = 2'):
            BatchMaterializeResult(
                total_placeholders=5,  # Mismatched total
                successful_materializations=[
                    MaterializeResult(
                        display_title='Test',
                        node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                        file_paths=[
                            '01234567-89ab-7def-8123-456789abcdef.md',
                            '01234567-89ab-7def-8123-456789abcdef.notes.md',
                        ],
                        position='[0]',
                    )
                ],
                failed_materializations=[
                    MaterializeFailure(
                        display_title='Failed Test', error_type='filesystem', error_message='Test error', position='[1]'
                    )
                ],
                execution_time=1.0,
            )

    def test_validation_error_with_results_but_zero_total(self) -> None:
        """Test validation error when placeholders exist but total is zero."""
        # Missing lines 53-54: Validation for positive total with zero results
        with pytest.raises(ValueError, match=r'Total placeholders 1 must equal successes 0 \+ failures 0 = 0'):
            BatchMaterializeResult(
                total_placeholders=1, successful_materializations=[], failed_materializations=[], execution_time=1.0
            )

    def test_summary_message_no_placeholders(self) -> None:
        """Test summary message for empty result."""
        # Missing line 89: No placeholders case
        result = BatchMaterializeResult(
            total_placeholders=0, successful_materializations=[], failed_materializations=[], execution_time=0.5
        )
        assert result.summary_message() == 'No placeholders found in binder'

    def test_summary_message_complete_failure(self) -> None:
        """Test summary message for complete failure."""
        # Missing line 92: Complete failure case
        result = BatchMaterializeResult(
            total_placeholders=2,
            successful_materializations=[],
            failed_materializations=[
                MaterializeFailure('Test1', 'filesystem', 'Error1', '[0]'),
                MaterializeFailure('Test2', 'validation', 'Error2', '[1]'),
            ],
            execution_time=1.0,
        )
        assert result.summary_message() == 'Failed to materialize all 2 placeholders'

    def test_summary_message_partial_success(self) -> None:
        """Test summary message for partial success."""
        # Missing lines 98-100: Partial success case
        result = BatchMaterializeResult(
            total_placeholders=3,
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
            ],
            execution_time=2.0,
        )
        assert result.summary_message() == 'Materialized 1 of 3 placeholders (2 failures)'


class TestMaterializeFailureCoverage:
    """Test missing coverage in MaterializeFailure."""

    def test_validation_empty_display_title(self) -> None:
        """Test validation for empty display title."""
        # Missing lines 43-44: Empty display title validation
        with pytest.raises(ValueError, match='Display title must be non-empty string'):
            MaterializeFailure(display_title='', error_type='filesystem', error_message='Test error', position='[0]')

    def test_validation_invalid_error_type(self) -> None:
        """Test validation for invalid error type."""
        # Missing lines 48-49: Invalid error type validation
        with pytest.raises(ValueError, match='Error type must be one of'):
            MaterializeFailure(
                display_title='Test', error_type='invalid_type', error_message='Test error', position='[0]'
            )

    def test_validation_empty_error_message(self) -> None:
        """Test validation for empty error message."""
        # Missing lines 53-54: Empty error message validation
        with pytest.raises(ValueError, match='Error message must be non-empty and human-readable'):
            MaterializeFailure(display_title='Test', error_type='filesystem', error_message='', position='[0]')

    def test_validation_empty_position_string(self) -> None:
        """Test validation for empty position string."""
        # Missing lines 59-60: Empty position string validation
        with pytest.raises(ValueError, match='Position must be None or non-empty string'):
            MaterializeFailure(
                display_title='Test',
                error_type='filesystem',
                error_message='Test error',
                position='',  # Empty string but not None
            )

    def test_is_retryable_filesystem_error(self) -> None:
        """Test retryable property for filesystem errors."""
        # Missing lines 65-66: is_retryable property
        failure = MaterializeFailure(
            display_title='Test', error_type='filesystem', error_message='Permission denied', position='[0]'
        )
        assert failure.is_retryable is True

    def test_formatted_error_with_position(self) -> None:
        """Test formatted error with position."""
        # Missing lines 82-84: formatted_error with position
        failure = MaterializeFailure(
            display_title='Test Title', error_type='filesystem', error_message='File creation failed', position='[0][1]'
        )
        assert failure.formatted_error() == "✗ Failed to materialize 'Test Title' at [0][1]: File creation failed"

    def test_str_representation(self) -> None:
        """Test string representation."""
        # Missing line 88: __str__ method
        failure = MaterializeFailure(
            display_title='Test', error_type='validation', error_message='Invalid data', position='[0]'
        )
        assert str(failure) == "✗ Failed to materialize 'Test' at [0]: Invalid data"


class TestMaterializeResultCoverage:
    """Test missing coverage in MaterializeResult."""

    def test_validation_empty_display_title(self) -> None:
        """Test validation for empty display title."""
        # Missing lines 36-37: Empty display title validation
        with pytest.raises(ValueError, match='Display title must be non-empty string'):
            MaterializeResult(
                display_title='',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                file_paths=['test.md', 'test.notes.md'],
                position='[0]',
            )

    def test_validation_invalid_uuid7(self) -> None:
        """Test validation for invalid UUIDv7."""
        # Missing lines 41-42: Invalid UUID validation
        # NodeId validation happens first, so we catch NodeIdentityError
        from prosemark.exceptions import NodeIdentityError

        with pytest.raises(NodeIdentityError):
            NodeId('invalid-uuid')

    def test_validation_wrong_file_path_count(self) -> None:
        """Test validation for wrong file path count."""
        # Missing lines 46-47: Wrong file path count validation
        with pytest.raises(ValueError, match='File paths must contain exactly 2 paths'):
            MaterializeResult(
                display_title='Test',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                file_paths=['only-one-file.md'],  # Only one file
                position='[0]',
            )

    def test_validation_wrong_file_path_format(self) -> None:
        """Test validation for wrong file path format."""
        # Missing lines 53-54: Wrong file path format validation
        with pytest.raises(ValueError, match='File paths must contain'):
            MaterializeResult(
                display_title='Test',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                file_paths=['wrong-name.md', 'also-wrong.notes.md'],  # Wrong file names
                position='[0]',
            )

    def test_validation_invalid_position_format(self) -> None:
        """Test validation for invalid position format."""
        # Missing lines 58-59: Invalid position format validation
        with pytest.raises(ValueError, match='Position must follow'):
            MaterializeResult(
                display_title='Test',
                node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
                file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
                position='invalid-position',  # Invalid format
            )

    def test_main_file_path_property(self) -> None:
        """Test main file path property."""
        # Missing lines 78-79: main_file_path property
        result = MaterializeResult(
            display_title='Test',
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
            position='[0]',
        )
        assert result.main_file_path == '01234567-89ab-7def-8123-456789abcdef.md'

    def test_notes_file_path_property(self) -> None:
        """Test notes file path property."""
        # Missing lines 84-85: notes_file_path property
        result = MaterializeResult(
            display_title='Test',
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
            position='[0]',
        )
        assert result.notes_file_path == '01234567-89ab-7def-8123-456789abcdef.notes.md'

    def test_str_representation(self) -> None:
        """Test string representation."""
        # Missing line 89: __str__ method
        result = MaterializeResult(
            display_title='Test Title',
            node_id=NodeId('01234567-89ab-7def-8123-456789abcdef'),
            file_paths=['01234567-89ab-7def-8123-456789abcdef.md', '01234567-89ab-7def-8123-456789abcdef.notes.md'],
            position='[0]',
        )
        assert str(result) == "Materialized 'Test Title' → 01234567-89ab-7def-8123-456789abcdef"


class TestPlaceholderSummaryCoverage:
    """Test missing coverage in PlaceholderSummary."""

    def test_validation_empty_display_title(self) -> None:
        """Test validation for empty display title."""
        # Missing lines 33-34: Empty display title validation
        with pytest.raises(ValueError, match='Display title must be non-empty string'):
            PlaceholderSummary(display_title='', position='[0]', parent_title=None, depth=0)

    def test_validation_invalid_position(self) -> None:
        """Test validation for invalid position format."""
        # Missing lines 38-39: Invalid position validation
        with pytest.raises(ValueError, match='Position must follow hierarchical format'):
            PlaceholderSummary(display_title='Test', position='invalid', parent_title=None, depth=0)

    def test_validation_negative_depth(self) -> None:
        """Test validation for negative depth."""
        # Missing lines 43-44: Negative depth validation
        with pytest.raises(ValueError, match='Depth must be non-negative integer'):
            PlaceholderSummary(display_title='Test', position='[0]', parent_title=None, depth=-1)

    def test_validation_root_with_parent(self) -> None:
        """Test validation for root level with parent title."""
        # Missing lines 48-49: Root level with parent validation
        with pytest.raises(ValueError, match='Root level items \\(depth=0\\) cannot have parent_title'):
            PlaceholderSummary(
                display_title='Test',
                position='[0]',
                parent_title='Some Parent',  # Invalid for depth=0
                depth=0,
            )

    def test_is_root_level_property(self) -> None:
        """Test is_root_level property."""
        # Missing line 66: is_root_level property
        placeholder = PlaceholderSummary(display_title='Test', position='[0]', parent_title=None, depth=0)
        assert placeholder.is_root_level is True

    def test_hierarchy_path_with_parent(self) -> None:
        """Test hierarchy path with parent."""
        # Missing lines 71-73: hierarchy_path with parent
        placeholder = PlaceholderSummary(display_title='Child', position='[0][1]', parent_title='Parent', depth=1)
        assert placeholder.hierarchy_path == 'Parent > Child'

    def test_position_indices_property(self) -> None:
        """Test position indices extraction."""
        # Missing lines 78-82: position_indices property
        placeholder = PlaceholderSummary(display_title='Test', position='[0][2][1]', parent_title=None, depth=2)
        assert placeholder.position_indices == [0, 2, 1]

    def test_with_updated_position(self) -> None:
        """Test creating instance with updated position."""
        # Missing line 86: with_updated_position method
        original = PlaceholderSummary(display_title='Test', position='[0]', parent_title='Parent', depth=1)
        updated = original.with_updated_position('[1][2]')
        assert updated.position == '[1][2]'
        assert updated.display_title == 'Test'  # Other fields preserved
        assert updated.parent_title == 'Parent'
        assert updated.depth == 1

    def test_str_with_parent(self) -> None:
        """Test string representation with parent."""
        # Missing lines 92-94: __str__ with parent
        placeholder = PlaceholderSummary(display_title='Child', position='[0][1]', parent_title='Parent', depth=1)
        assert str(placeholder) == "'Child' (under 'Parent', depth=1)"

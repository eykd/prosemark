"""Unit tests for BatchMaterializeResult validation."""

from dataclasses import FrozenInstanceError

import pytest

from prosemark.domain.batch_materialize_result import BatchMaterializeResult
from prosemark.domain.materialize_failure import MaterializeFailure
from prosemark.domain.materialize_result import MaterializeResult
from prosemark.domain.models import NodeId


class TestBatchMaterializeResult:
    """Test BatchMaterializeResult validation and behavior."""

    def test_successful_batch_result(self) -> None:
        """Test creation of fully successful batch result."""
        # Arrange
        successes = [
            MaterializeResult(
                display_title='Chapter 1',
                node_id=NodeId('01923f0c-1234-7123-8abc-def012345678'),
                file_paths=['01923f0c-1234-7123-8abc-def012345678.md', '01923f0c-1234-7123-8abc-def012345678.notes.md'],
                position='[0]',
            ),
            MaterializeResult(
                display_title='Chapter 2',
                node_id=NodeId('01923f0c-1234-7123-8abc-def012345679'),
                file_paths=['01923f0c-1234-7123-8abc-def012345679.md', '01923f0c-1234-7123-8abc-def012345679.notes.md'],
                position='[1]',
            ),
        ]

        # Act
        result = BatchMaterializeResult(
            total_placeholders=2, successful_materializations=successes, failed_materializations=[], execution_time=1.5
        )

        # Assert
        assert result.total_placeholders == 2
        assert len(result.successful_materializations) == 2
        assert len(result.failed_materializations) == 0
        assert result.execution_time == 1.5
        assert result.success_rate == 100.0
        assert result.is_complete_success is True

    def test_partial_failure_batch_result(self) -> None:
        """Test creation of batch result with some failures."""
        # Arrange
        successes = [
            MaterializeResult(
                display_title='Valid Chapter',
                node_id=NodeId('01923f0c-1234-7123-8abc-def012345678'),
                file_paths=['01923f0c-1234-7123-8abc-def012345678.md', '01923f0c-1234-7123-8abc-def012345678.notes.md'],
                position='[0]',
            )
        ]
        failures = [
            MaterializeFailure(
                display_title='Invalid/Chapter',
                error_type='filesystem',
                error_message='Invalid characters in filename',
                position='[1]',
            )
        ]

        # Act
        result = BatchMaterializeResult(
            total_placeholders=2,
            successful_materializations=successes,
            failed_materializations=failures,
            execution_time=2.0,
        )

        # Assert
        assert result.total_placeholders == 2
        assert len(result.successful_materializations) == 1
        assert len(result.failed_materializations) == 1
        assert result.execution_time == 2.0
        assert result.success_rate == 50.0
        assert result.is_complete_success is False

    def test_complete_failure_batch_result(self) -> None:
        """Test creation of batch result with all failures."""
        # Arrange
        failures = [
            MaterializeFailure(
                display_title='Bad/Title1', error_type='filesystem', error_message='Invalid characters', position='[0]'
            ),
            MaterializeFailure(
                display_title='Bad:Title2', error_type='filesystem', error_message='Invalid characters', position='[1]'
            ),
        ]

        # Act
        result = BatchMaterializeResult(
            total_placeholders=2, successful_materializations=[], failed_materializations=failures, execution_time=0.5
        )

        # Assert
        assert result.total_placeholders == 2
        assert len(result.successful_materializations) == 0
        assert len(result.failed_materializations) == 2
        assert result.execution_time == 0.5
        assert result.success_rate == 0.0
        assert result.is_complete_success is False

    def test_empty_batch_result(self) -> None:
        """Test creation of batch result with no placeholders."""
        # Act
        result = BatchMaterializeResult(
            total_placeholders=0, successful_materializations=[], failed_materializations=[], execution_time=0.1
        )

        # Assert
        assert result.total_placeholders == 0
        assert len(result.successful_materializations) == 0
        assert len(result.failed_materializations) == 0
        assert result.execution_time == 0.1
        assert result.success_rate == 100.0  # 100% success rate when no operations
        assert result.is_complete_success is False  # Complete success requires >0 placeholders

    def test_invalid_total_placeholders(self) -> None:
        """Test validation of mismatched total vs actual counts."""
        with pytest.raises(ValueError, match='Total placeholders -1 must equal'):
            BatchMaterializeResult(
                total_placeholders=-1, successful_materializations=[], failed_materializations=[], execution_time=1.0
            )

    def test_invalid_execution_time(self) -> None:
        """Test validation of execution_time field."""
        with pytest.raises(ValueError, match='Execution time must be non-negative'):
            BatchMaterializeResult(
                total_placeholders=0, successful_materializations=[], failed_materializations=[], execution_time=-0.5
            )

    def test_count_mismatch_validation(self) -> None:
        """Test validation that success + failure counts match total."""
        success = MaterializeResult(
            display_title='Chapter 1',
            node_id=NodeId('01923f0c-1234-7123-8abc-def012345678'),
            file_paths=['01923f0c-1234-7123-8abc-def012345678.md', '01923f0c-1234-7123-8abc-def012345678.notes.md'],
            position='[0]',
        )

        with pytest.raises(ValueError, match='Total placeholders 3 must equal'):
            BatchMaterializeResult(
                total_placeholders=3,
                successful_materializations=[success],
                failed_materializations=[],
                execution_time=1.0,
            )

    def test_immutability(self) -> None:
        """Test that BatchMaterializeResult is immutable."""
        result = BatchMaterializeResult(
            total_placeholders=0, successful_materializations=[], failed_materializations=[], execution_time=0.1
        )

        with pytest.raises(FrozenInstanceError):
            result.total_placeholders = 5  # type: ignore[misc]

    def test_success_rate_calculation(self) -> None:
        """Test various success rate calculations."""
        # Test perfect success (empty case)
        result = BatchMaterializeResult(
            total_placeholders=0, successful_materializations=[], failed_materializations=[], execution_time=0.1
        )
        assert result.success_rate == 100.0

        # Test 75% success rate
        successes = [
            MaterializeResult(
                display_title=f'Chapter {i}',
                node_id=NodeId(f'01923f0c-1234-7123-8abc-def01234567{i}'),
                file_paths=[
                    f'01923f0c-1234-7123-8abc-def01234567{i}.md',
                    f'01923f0c-1234-7123-8abc-def01234567{i}.notes.md',
                ],
                position=f'[{i}]',
            )
            for i in range(3)
        ]
        failures = [
            MaterializeFailure(
                display_title='Bad Chapter', error_type='filesystem', error_message='Error', position='[3]'
            )
        ]

        result = BatchMaterializeResult(
            total_placeholders=4,
            successful_materializations=successes,
            failed_materializations=failures,
            execution_time=2.0,
        )
        assert result.success_rate == 75.0

"""BatchMaterializeResult value object for bulk materialization operations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prosemark.domain.materialize_failure import MaterializeFailure
    from prosemark.domain.materialize_result import MaterializeResult


@dataclass(frozen=True)
class BatchMaterializeResult:
    """Represents the outcome of materializing all placeholders in a binder.

    This value object encapsulates the complete result of a batch materialization
    operation, including both successes and failures, along with execution metrics.

    Args:
        total_placeholders: Total number of placeholders found and processed
        successful_materializations: List of successful materialization results
        failed_materializations: List of failed materialization attempts
        execution_time: Total time taken for batch operation in seconds

    Raises:
        ValueError: If validation rules are violated during construction

    """

    total_placeholders: int
    successful_materializations: list['MaterializeResult']
    failed_materializations: list['MaterializeFailure']
    execution_time: float

    def __post_init__(self) -> None:
        """Validate the batch result after construction."""
        # Validate total_placeholders matches sum of successes and failures
        actual_total = len(self.successful_materializations) + len(self.failed_materializations)
        if self.total_placeholders != actual_total:
            msg = (
                f'Total placeholders {self.total_placeholders} must equal '
                f'successes {len(self.successful_materializations)} + '
                f'failures {len(self.failed_materializations)} = {actual_total}'
            )
            raise ValueError(msg)

        # Validate execution_time is non-negative
        if self.execution_time < 0:
            msg = f'Execution time must be non-negative, got {self.execution_time}'
            raise ValueError(msg)

        # Validate that if placeholders exist, we have at least some results
        if self.total_placeholders > 0 and actual_total == 0:  # pragma: no cover
            msg = f'If total_placeholders is {self.total_placeholders}, must have results'  # pragma: no cover
            raise ValueError(msg)  # pragma: no cover

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_placeholders == 0:
            return 100.0
        return (len(self.successful_materializations) / self.total_placeholders) * 100.0

    @property
    def has_failures(self) -> bool:
        """Check if any materializations failed."""
        return len(self.failed_materializations) > 0

    @property
    def is_complete_success(self) -> bool:
        """Check if all materializations succeeded."""
        return (
            self.total_placeholders > 0
            and len(self.successful_materializations) == self.total_placeholders
            and not self.has_failures
        )

    @property
    def is_complete_failure(self) -> bool:
        """Check if all materializations failed."""
        return (
            self.total_placeholders > 0
            and len(self.failed_materializations) == self.total_placeholders
            and len(self.successful_materializations) == 0
        )

    def summary_message(self) -> str:
        """Generate a human-readable summary message."""
        if self.total_placeholders == 0:
            return 'No placeholders found in binder'

        if self.is_complete_success:
            return f'Successfully materialized all {self.total_placeholders} placeholders'

        if self.is_complete_failure:
            return f'Failed to materialize all {self.total_placeholders} placeholders'

        # Partial success/failure
        successful_count = len(self.successful_materializations)
        failed_count = len(self.failed_materializations)
        return f'Materialized {successful_count} of {self.total_placeholders} placeholders ({failed_count} failures)'

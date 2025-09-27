"""MaterializeAllPlaceholders use case for bulk conversion of placeholders to nodes."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.batch_materialize_result import BatchMaterializeResult
from prosemark.domain.materialize_failure import MaterializeFailure
from prosemark.domain.materialize_result import MaterializeResult
from prosemark.domain.models import Binder, BinderItem
from prosemark.domain.placeholder_summary import PlaceholderSummary

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.app.materialize_node import MaterializeNode
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.clock import Clock
    from prosemark.ports.id_generator import IdGenerator
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


class MaterializeAllPlaceholders:
    """Materialize all placeholder items in a binder to actual content nodes."""

    def __init__(
        self,
        *,
        materialize_node_use_case: 'MaterializeNode',
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        id_generator: 'IdGenerator',
        clock: 'Clock',
        logger: 'Logger',
    ) -> None:
        """Initialize the MaterializeAllPlaceholders use case.

        Args:
            materialize_node_use_case: Use case for individual node materialization
            binder_repo: Repository for binder operations
            node_repo: Repository for node operations
            id_generator: Generator for unique node IDs
            clock: Clock for timestamps
            logger: Logger port

        """
        self.materialize_node_use_case = materialize_node_use_case
        self.binder_repo = binder_repo
        self.node_repo = node_repo
        self.id_generator = id_generator
        self.clock = clock
        self.logger = logger

    def execute(
        self,
        *,
        binder: Binder | None = None,
        project_path: Path | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> BatchMaterializeResult:
        """Materialize all placeholders in the binder.

        Args:
            binder: Optional binder to process (if not provided, loads from repo)
            project_path: Project directory path
            progress_callback: Optional callback for progress reporting

        Returns:
            BatchMaterializeResult containing success/failure information

        """
        start_time = time.time()
        project_path = project_path or Path.cwd()

        # Load binder if not provided
        if binder is None:
            binder = self.binder_repo.load()

        self.logger.info('Starting batch materialization of all placeholders')

        # Discover all placeholders
        placeholders = self._discover_placeholders(binder)
        total_placeholders = len(placeholders)

        self.logger.info('Found %d placeholders to materialize', total_placeholders)
        if progress_callback:
            progress_callback(f'Found {total_placeholders} placeholders to materialize...')

        # If no placeholders, return early
        if total_placeholders == 0:
            execution_time = time.time() - start_time
            return BatchMaterializeResult(
                total_placeholders=0,
                successful_materializations=[],
                failed_materializations=[],
                execution_time=execution_time,
            )

        # Process each placeholder
        successful_materializations: list[MaterializeResult] = []
        failed_materializations: list[MaterializeFailure] = []

        for i, placeholder in enumerate(placeholders, 1):
            try:
                # Attempt materialization using existing use case
                result = self._materialize_single_placeholder(placeholder=placeholder, project_path=project_path)
                successful_materializations.append(result)

                # Report progress
                if progress_callback:
                    progress_callback(f"✓ Materialized '{result.display_title}' → {result.node_id.value}")

                self.logger.info(
                    'Successfully materialized placeholder %d/%d: %s',
                    i,
                    total_placeholders,
                    placeholder.display_title,
                )

            except Exception as e:
                # Create failure record
                failure = MaterializeAllPlaceholders._create_failure_record(placeholder, e)
                failed_materializations.append(failure)

                # Report progress
                if progress_callback:
                    progress_callback(f"✗ Failed to materialize '{placeholder.display_title}': {failure.error_message}")

                self.logger.exception(
                    'Failed to materialize placeholder %d/%d: %s',
                    i,
                    total_placeholders,
                    placeholder.display_title,
                )

                # Check if we should stop the batch on critical errors
                if failure.should_stop_batch:
                    self.logger.exception('Critical error encountered, stopping batch operation')
                    break

        execution_time = time.time() - start_time

        # Create final result
        batch_result = BatchMaterializeResult(
            total_placeholders=total_placeholders,
            successful_materializations=successful_materializations,
            failed_materializations=failed_materializations,
            execution_time=execution_time,
        )

        self.logger.info(
            'Batch materialization complete: %d successes, %d failures in %.2f seconds',
            len(successful_materializations),
            len(failed_materializations),
            execution_time,
        )

        return batch_result

    def _discover_placeholders(self, binder: Binder) -> list[PlaceholderSummary]:
        """Discover all items in the binder hierarchy that need processing.

        This includes both placeholders (items without node IDs) and materialized nodes
        (items with node IDs that may have missing files). The enhanced MaterializeNode
        can handle both cases appropriately.

        Args:
            binder: Binder to scan for items to process

        Returns:
            List of item summaries in hierarchical order

        """
        placeholders: list[PlaceholderSummary] = []
        self._collect_placeholders_recursive(binder.roots, placeholders, parent_title=None, depth=0, position_path=[])
        return placeholders

    def _collect_placeholders_recursive(
        self,
        items: list[BinderItem],
        placeholders: list[PlaceholderSummary],
        parent_title: str | None,
        depth: int,
        position_path: list[int] | None = None,
    ) -> None:
        """Recursively collect all items that need processing from binder hierarchy.

        Collects both placeholders and materialized nodes since the enhanced
        MaterializeNode can handle both cases (creating new nodes or fixing missing files).

        Args:
            items: Current level items to process
            placeholders: List to append discovered items to
            parent_title: Title of parent item (if any)
            depth: Current nesting depth
            position_path: Hierarchical position path from root

        """
        for i, item in enumerate(items):
            # Create position string based on index
            position_path = position_path or []
            position = '[' + ']['.join(str(idx) for idx in [*position_path, i]) + ']'

            # Collect both placeholders (node_id is None) and materialized nodes (node_id exists)
            # The enhanced MaterializeNode can handle both cases:
            # - Placeholders: creates new nodes with both .md and .notes.md files
            # - Materialized nodes: creates missing .notes.md files if needed
            placeholder = PlaceholderSummary(
                display_title=item.display_title,
                position=position,
                parent_title=parent_title,
                depth=depth,
            )
            placeholders.append(placeholder)

            # Recursively process children
            if item.children:
                self._collect_placeholders_recursive(
                    items=item.children,
                    placeholders=placeholders,
                    parent_title=item.display_title,
                    depth=depth + 1,
                    position_path=[*position_path, i],
                )

    def _materialize_single_placeholder(
        self, *, placeholder: PlaceholderSummary, project_path: Path
    ) -> MaterializeResult:
        """Materialize a single placeholder using the existing MaterializeNode use case.

        Args:
            placeholder: Placeholder to materialize
            project_path: Project directory path

        Returns:
            MaterializeResult with the outcome

        Raises:
            Various exceptions from the underlying materialization process

        """
        # Use the existing MaterializeNode use case
        result = self.materialize_node_use_case.execute(title=placeholder.display_title, project_path=project_path)

        # Create file paths
        file_paths = [f'{result.node_id.value}.md', f'{result.node_id.value}.notes.md']

        return MaterializeResult(
            display_title=placeholder.display_title,
            node_id=result.node_id,
            file_paths=file_paths,
            position=placeholder.position,
        )

    @staticmethod
    def _create_failure_record(placeholder: PlaceholderSummary, error: Exception) -> MaterializeFailure:
        """Create a MaterializeFailure record from an exception.

        Args:
            placeholder: Placeholder that failed to materialize
            error: Exception that occurred during materialization

        Returns:
            MaterializeFailure record with categorized error information

        """
        # Categorize the error type based on exception
        error_type = MaterializeAllPlaceholders._categorize_error(error)
        error_message = str(error)

        return MaterializeFailure(
            display_title=placeholder.display_title,
            error_type=error_type,
            error_message=error_message,
            position=placeholder.position,
        )

    @staticmethod
    def _categorize_error(error: Exception) -> str:
        """Categorize an exception into a known error type.

        Args:
            error: Exception to categorize

        Returns:
            Error type string from MaterializeFailure.VALID_ERROR_TYPES

        """
        error_type_name = type(error).__name__

        # Map common exception types to our error categories
        if 'FileSystem' in error_type_name or 'Permission' in error_type_name or 'OSError' in error_type_name:
            return 'filesystem'
        if 'Validation' in error_type_name or 'ValueError' in error_type_name:
            return 'validation'
        if 'AlreadyMaterialized' in error_type_name:
            return 'already_materialized'
        if 'Binder' in error_type_name or 'Integrity' in error_type_name:
            return 'binder_integrity'
        if 'UUID' in error_type_name or 'Id' in error_type_name:
            return 'id_generation'
        # Default to filesystem for unknown errors
        return 'filesystem'

"""AuditProject use case for checking project integrity."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from prosemark.domain.models import BinderItem, NodeId
from prosemark.exceptions import FileSystemError, FrontmatterFormatError, NodeNotFoundError

if TYPE_CHECKING:  # pragma: no cover
    from prosemark.ports.binder_repo import BinderRepo
    from prosemark.ports.console_port import ConsolePort
    from prosemark.ports.logger import Logger
    from prosemark.ports.node_repo import NodeRepo


@dataclass(frozen=True)
class PlaceholderIssue:
    """Represents a placeholder item found during audit."""

    display_title: str
    position: str  # Human-readable position like "[0][1]"


@dataclass(frozen=True)
class MissingIssue:
    """Represents a missing node file found during audit."""

    node_id: NodeId
    expected_path: str


@dataclass(frozen=True)
class OrphanIssue:
    """Represents an orphaned node file found during audit."""

    node_id: NodeId
    file_path: str


@dataclass(frozen=True)
class MismatchIssue:
    """Represents a mismatch between file name and content ID."""

    node_id: NodeId
    file_id: str
    file_path: str


@dataclass(frozen=True)
class AuditReport:
    """Complete audit report for a project."""

    placeholders: list[PlaceholderIssue]
    missing: list[MissingIssue]
    orphans: list[OrphanIssue]
    mismatches: list[MismatchIssue]

    @property
    def has_issues(self) -> bool:
        """Check if the report contains any issues."""
        return bool(self.placeholders or self.missing or self.orphans or self.mismatches)


class AuditProject:
    """Audit a prosemark project for consistency and integrity."""

    def __init__(
        self,
        *,
        binder_repo: 'BinderRepo',
        node_repo: 'NodeRepo',
        console: 'ConsolePort',
        logger: 'Logger',
    ) -> None:
        """Initialize the AuditProject use case.

        Args:
            binder_repo: Repository for binder operations.
            node_repo: Repository for node operations.
            console: Console output port.
            logger: Logger port.

        """
        self.binder_repo = binder_repo
        self.node_repo = node_repo
        self.console = console
        self.logger = logger

    def execute(self, *, project_path: Path | None = None) -> AuditReport:
        """Audit the project for consistency issues.

        Args:
            project_path: Project directory path.

        Returns:
            Audit report with all found issues.

        """
        project_path = project_path or Path.cwd()
        self.logger.info('Auditing project at %s', project_path)

        # Load binder
        binder = self.binder_repo.load()

        # Collect all issues
        placeholders: list[PlaceholderIssue] = []
        missing: list[MissingIssue] = []
        mismatches: list[MismatchIssue] = []

        # Check binder items
        self._check_items(binder.roots, placeholders, missing, mismatches, project_path)

        # Check for orphaned files
        orphans = self._find_orphans(binder.roots, project_path)

        # Create report
        report = AuditReport(
            placeholders=placeholders,
            missing=missing,
            orphans=orphans,
            mismatches=mismatches,
        )

        # Display results
        self._display_report(report)

        return report

    def _check_items(
        self,
        items: list[BinderItem],
        placeholders: list[PlaceholderIssue],
        missing: list[MissingIssue],
        mismatches: list[MismatchIssue],
        project_path: Path,
        position_prefix: str = '',
    ) -> None:
        """Recursively check binder items for issues.

        Args:
            items: List of binder items to check.
            placeholders: List to collect placeholder issues.
            missing: List to collect missing file issues.
            mismatches: List to collect mismatch issues.
            project_path: Project directory path.
            position_prefix: Position string prefix for nested items.

        """
        for i, item in enumerate(items):
            position = f'{position_prefix}[{i}]'

            if not item.node_id:
                # Found a placeholder
                placeholders.append(
                    PlaceholderIssue(
                        display_title=item.display_title,
                        position=position,
                    ),
                )
            else:
                # Check if node files exist
                draft_path = project_path / f'{item.node_id.value}.md'
                notes_path = project_path / f'{item.node_id.value}.notes.md'

                if not draft_path.exists():
                    missing.append(
                        MissingIssue(
                            node_id=item.node_id,
                            expected_path=str(draft_path),
                        ),
                    )
                else:
                    # Check for ID mismatch
                    try:
                        frontmatter = self.node_repo.read_frontmatter(item.node_id)
                        node_id_from_frontmatter = frontmatter.get('id')
                        if node_id_from_frontmatter != item.node_id.value:
                            mismatches.append(
                                MismatchIssue(
                                    node_id=item.node_id,
                                    file_id=node_id_from_frontmatter or '',
                                    file_path=str(draft_path),
                                ),
                            )
                    except (NodeNotFoundError, FileSystemError, FrontmatterFormatError):  # pragma: no cover
                        # Frontmatter read failed - will be caught as missing  # pragma: no cover
                        pass  # pragma: no cover

                if not notes_path.exists():
                    missing.append(
                        MissingIssue(
                            node_id=item.node_id,
                            expected_path=str(notes_path),
                        ),
                    )

            # Recursively check children
            self._check_items(
                item.children,
                placeholders,
                missing,
                mismatches,
                project_path,
                position,
            )

    def _find_orphans(self, items: list[BinderItem], project_path: Path) -> list[OrphanIssue]:
        """Find orphaned node files not referenced in the binder.

        Args:
            items: List of binder items.
            project_path: Project directory path.

        Returns:
            List of orphan issues.

        """
        # Collect all referenced node IDs
        referenced_ids: set[str] = set()
        self._collect_ids(items, referenced_ids)

        # Find all node files in the directory
        orphans: list[OrphanIssue] = []
        for path in project_path.glob('*.md'):
            if path.name == '_binder.md':
                continue
            if path.name.endswith('.notes.md'):
                continue

            # Extract ID from filename
            file_id = path.stem
            if file_id not in referenced_ids:
                orphans.append(
                    OrphanIssue(
                        node_id=NodeId(file_id),
                        file_path=str(path),
                    ),
                )

        return orphans

    def _collect_ids(self, items: list[BinderItem], ids: set[str]) -> None:
        """Recursively collect all node IDs from binder items.

        Args:
            items: List of binder items.
            ids: Set to collect IDs into.

        """
        for item in items:
            if item.node_id:
                ids.add(item.node_id.value)
            self._collect_ids(item.children, ids)

    def _display_report(self, report: AuditReport) -> None:
        """Display the audit report to the console.

        Args:
            report: The audit report to display.

        """
        self.console.print_info('Project integrity check completed')

        if not report.has_issues:
            self.console.print_success('✓ All nodes have valid files')
            self.console.print_success('✓ All references are consistent')
            self.console.print_success('✓ No orphaned files found')
            return

        # Display issues
        if report.placeholders:
            self.console.print_warning(f'Found {len(report.placeholders)} placeholder(s):')
            for issue in report.placeholders:
                self.console.print_info(f'  {issue.position}: {issue.display_title}')

        if report.missing:
            self.console.print_error(f'Found {len(report.missing)} missing file(s):')
            for missing_issue in report.missing:
                self.console.print_info(f'  {missing_issue.expected_path}')

        if report.orphans:
            self.console.print_warning(f'Found {len(report.orphans)} orphaned file(s):')
            for orphan_issue in report.orphans:
                self.console.print_info(f'  {orphan_issue.file_path}')

        if report.mismatches:
            self.console.print_error(f'Found {len(report.mismatches)} ID mismatch(es):')
            for mismatch_issue in report.mismatches:
                expected = mismatch_issue.node_id.value
                found = mismatch_issue.file_id
                msg = f'  {mismatch_issue.file_path}: expected {expected}, found {found}'
                self.console.print_info(msg)

"""CLI command for auditing project integrity."""

from pathlib import Path
from typing import Any, Protocol

import click

from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.app.use_cases import AuditBinder
from prosemark.exceptions import FileSystemError


class AuditReport(Protocol):
    """A protocol representing the audit report with various node integrity checks."""

    placeholders: list[Any]
    missing: list[Any]
    orphans: list[Any]
    mismatches: list[Any]

    def is_clean(self) -> bool:
        """Determine if the audit report indicates no integrity issues.

        Returns:
            bool: True if no integrity issues found, False otherwise.

        """
        ...


def _report_placeholders(report: AuditReport) -> None:
    """Report placeholder nodes."""
    if report.placeholders:
        for placeholder in report.placeholders:
            if hasattr(placeholder, 'display_title'):
                click.echo(f'⚠ PLACEHOLDER: "{placeholder.display_title}" (no associated files)')


def _report_missing_nodes(report: AuditReport) -> None:
    """Report missing nodes."""
    if report.missing:
        for missing in report.missing:
            if hasattr(missing, 'node_id'):
                click.echo(f'⚠ MISSING: Node {missing.node_id} referenced but files not found')


def _report_orphans(report: AuditReport) -> None:
    """Report orphaned files."""
    if report.orphans:
        for orphan in report.orphans:
            if hasattr(orphan, 'file_path'):
                click.echo(f'⚠ ORPHAN: File {orphan.file_path} exists but not in binder')


def _report_mismatches(report: AuditReport) -> None:
    """Report file mismatches."""
    if report.mismatches:
        for mismatch in report.mismatches:
            if hasattr(mismatch, 'file_path'):
                click.echo(f'⚠ MISMATCH: File {mismatch.file_path} ID mismatch')


@click.command()
@click.option('--fix/--no-fix', default=False, help='Attempt to fix discovered issues')
def audit_command(*, fix: bool) -> None:
    """Check project integrity."""
    try:
        project_root = Path.cwd()

        # Wire up dependencies
        binder_repo = BinderRepoFs(project_root)
        clock = ClockSystem()
        editor = EditorLauncherSystem()
        node_repo = NodeRepoFs(project_root, editor, clock)
        logger = LoggerStdout()

        # Execute use case
        interactor = AuditBinder(
            binder_repo=binder_repo,
            node_repo=node_repo,
            logger=logger,
        )

        report = interactor.execute()

        if report.is_clean():
            click.echo('Project integrity check completed')
            click.echo('✓ All nodes have valid files')
            click.echo('✓ All references are consistent')
            click.echo('✓ No orphaned files found')
        else:
            click.echo('Project integrity issues found:')

            _report_placeholders(report)
            _report_missing_nodes(report)
            _report_orphans(report)
            _report_mismatches(report)

            if fix:
                click.echo('\nNote: Auto-fix not implemented in MVP')
                raise SystemExit(2)
            raise SystemExit(1)

    except FileSystemError as err:
        click.echo(f'Error: {err}', err=True)
        raise SystemExit(2) from err

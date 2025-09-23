"""Coverage tests for CLI audit command uncovered lines."""

from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from prosemark.app.use_cases import AuditReport, MismatchIssue, MissingIssue, OrphanIssue, PlaceholderIssue
from prosemark.cli.audit import (
    _report_mismatches,
    _report_missing_nodes,
    _report_orphans,
    _report_placeholders,
    audit_command,
)
from prosemark.domain.models import NodeId
from prosemark.exceptions import FileSystemError


class MockPlaceholder:
    """Mock placeholder object without display_title."""


@dataclass
class MockPlaceholderWithTitle:
    """Mock placeholder object with display_title."""

    display_title: str


class MockMissing:
    """Mock missing object without node_id."""


@dataclass
class MockMissingWithId:
    """Mock missing object with node_id."""

    node_id: str


class MockOrphan:
    """Mock orphan object without file_path."""


@dataclass
class MockOrphanWithPath:
    """Mock orphan object with file_path."""

    file_path: str


class MockMismatch:
    """Mock mismatch object without file_path."""


@dataclass
class MockMismatchWithPath:
    """Mock mismatch object with file_path."""

    file_path: str


class TestCLIAuditCoverage:
    """Test uncovered lines in CLI audit command."""

    def test_report_placeholders_without_display_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_placeholders with objects without display_title attribute."""
        # Create a mock object without display_title to test error handling
        from unittest.mock import Mock

        mock_placeholder = Mock(spec=[])  # No attributes
        report = AuditReport(placeholders=[mock_placeholder], missing=[], orphans=[], mismatches=[])

        _report_placeholders(report)

        captured = capsys.readouterr()
        # Should not output anything for objects without display_title
        assert captured.out == ''

    def test_report_placeholders_with_display_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_placeholders with objects with display_title attribute."""
        report = AuditReport(
            placeholders=[PlaceholderIssue(display_title='Test Chapter', position='[0]')],
            missing=[],
            orphans=[],
            mismatches=[],
        )

        _report_placeholders(report)

        captured = capsys.readouterr()
        assert '⚠ PLACEHOLDER: "Test Chapter" (no associated files)' in captured.out

    def test_report_missing_nodes_without_node_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_missing_nodes with objects without node_id attribute."""
        # Create a mock object without node_id to test error handling
        from unittest.mock import Mock

        mock_missing = Mock(spec=[])  # No attributes
        report = AuditReport(placeholders=[], missing=[mock_missing], orphans=[], mismatches=[])

        _report_missing_nodes(report)

        captured = capsys.readouterr()
        # Should not output anything for objects without node_id
        assert captured.out == ''

    def test_report_missing_nodes_with_node_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_missing_nodes with objects with node_id attribute."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        report = AuditReport(
            placeholders=[],
            missing=[MissingIssue(node_id=node_id, expected_path='test-id-123.md')],
            orphans=[],
            mismatches=[],
        )

        _report_missing_nodes(report)

        captured = capsys.readouterr()
        assert '⚠ MISSING: Node 0192f0c1-2345-7123-8abc-def012345678 referenced but files not found' in captured.out

    def test_report_orphans_without_file_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_orphans with objects without file_path attribute."""
        # Create a mock object without file_path to test error handling
        from unittest.mock import Mock

        mock_orphan = Mock(spec=[])  # No attributes
        report = AuditReport(placeholders=[], missing=[], orphans=[mock_orphan], mismatches=[])

        _report_orphans(report)

        captured = capsys.readouterr()
        # Should not output anything for objects without file_path
        assert captured.out == ''

    def test_report_orphans_with_file_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_orphans with objects with file_path attribute."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        report = AuditReport(
            placeholders=[], missing=[], orphans=[OrphanIssue(node_id=node_id, file_path='test-file.md')], mismatches=[]
        )

        _report_orphans(report)

        captured = capsys.readouterr()
        assert '⚠ ORPHAN: File test-file.md exists but not in binder' in captured.out

    def test_report_mismatches_without_file_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_mismatches with objects without file_path attribute."""
        # Create a mock object without file_path to test error handling
        from unittest.mock import Mock

        mock_mismatch = Mock(spec=[])  # No attributes
        report = AuditReport(placeholders=[], missing=[], orphans=[], mismatches=[mock_mismatch])

        _report_mismatches(report)

        captured = capsys.readouterr()
        # Should not output anything for objects without file_path
        assert captured.out == ''

    def test_report_mismatches_with_file_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_mismatches with objects with file_path attribute."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        node_id2 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        report = AuditReport(
            placeholders=[],
            missing=[],
            orphans=[],
            mismatches=[MismatchIssue(file_path='test-file.md', expected_id=node_id, actual_id=node_id2)],
        )

        _report_mismatches(report)

        captured = capsys.readouterr()
        assert '⚠ MISMATCH: File test-file.md ID mismatch' in captured.out

    def test_audit_command_fix_flag_not_implemented(self) -> None:
        """Test audit command with --fix flag when auto-fix is not implemented."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock audit report with real issues to trigger fix behavior
            mock_missing = Mock()
            mock_missing.node_id = 'missing123'

            mock_report = Mock()
            mock_report.is_clean.return_value = False
            mock_report.placeholders = []
            mock_report.missing = [mock_missing]
            mock_report.orphans = []
            mock_report.mismatches = []

            with patch('prosemark.cli.audit.AuditBinder') as mock_audit_class:
                mock_audit_instance = mock_audit_class.return_value
                mock_audit_instance.execute.return_value = mock_report

                # Run audit with --fix flag
                result = runner.invoke(audit_command, ['--fix'])

                # Should exit with code 2 and show not implemented message
                assert result.exit_code == 2
                assert 'Note: Auto-fix not implemented in MVP' in result.output

    def test_audit_command_filesystem_error(self) -> None:
        """Test audit command handles FileSystemError properly."""
        runner = CliRunner()

        with (
            runner.isolated_filesystem(),
            patch('prosemark.cli.audit.AuditBinder') as mock_audit_class,
        ):
            # Mock the AuditBinder class to raise FileSystemError
            mock_audit_instance = mock_audit_class.return_value
            mock_audit_instance.execute.side_effect = FileSystemError('Permission denied')

            result = runner.invoke(audit_command, [])

            assert result.exit_code == 2
            assert 'Error: Permission denied' in result.output

    def test_audit_command_clean_report(self) -> None:
        """Test audit command with clean report (lines 71-110)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock a clean audit report
            mock_clean_report = Mock()
            mock_clean_report.is_clean.return_value = True
            mock_clean_report.placeholders = []
            mock_clean_report.missing = []
            mock_clean_report.orphans = []
            mock_clean_report.mismatches = []

            with patch('prosemark.cli.audit.AuditBinder') as mock_audit_class:
                mock_audit_instance = mock_audit_class.return_value
                mock_audit_instance.execute.return_value = mock_clean_report

                result = runner.invoke(audit_command, [])

                assert result.exit_code == 0
                assert 'Project integrity check completed' in result.output
                assert '✓ All nodes have valid files' in result.output
                assert '✓ All references are consistent' in result.output
                assert '✓ No orphaned files found' in result.output

    def test_audit_command_dirty_report_no_fix(self) -> None:
        """Test audit command with issues found and no fix flag (lines 71-110)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            from prosemark.cli import init_command

            # Initialize project first
            init_result = runner.invoke(init_command, ['--title', 'Test Project'])
            assert init_result.exit_code == 0

            # Mock a dirty audit report with real issues
            mock_missing = Mock()
            mock_missing.node_id = 'missing123'

            mock_dirty_report = Mock()
            mock_dirty_report.is_clean.return_value = False
            mock_dirty_report.placeholders = []
            mock_dirty_report.missing = [mock_missing]
            mock_dirty_report.orphans = []
            mock_dirty_report.mismatches = []

            with patch('prosemark.cli.audit.AuditBinder') as mock_audit_class:
                mock_audit_instance = mock_audit_class.return_value
                mock_audit_instance.execute.return_value = mock_dirty_report

                result = runner.invoke(audit_command, [])

                assert result.exit_code == 1
                assert 'Project integrity issues found:' in result.output

    def test_report_placeholders_with_placeholders(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_placeholders with placeholders (lines 37-40)."""
        report = AuditReport(
            placeholders=[PlaceholderIssue(display_title='Test Chapter', position='[0]')],
            missing=[],
            orphans=[],
            mismatches=[],
        )

        _report_placeholders(report)

        captured = capsys.readouterr()
        assert '⚠ PLACEHOLDER: "Test Chapter" (no associated files)' in captured.out

    def test_report_missing_nodes_with_missing(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_missing_nodes with missing nodes (lines 45-48)."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        report = AuditReport(
            placeholders=[],
            missing=[MissingIssue(node_id=node_id, expected_path='missing-node-123.md')],
            orphans=[],
            mismatches=[],
        )

        _report_missing_nodes(report)

        captured = capsys.readouterr()
        assert '⚠ MISSING: Node 0192f0c1-2345-7123-8abc-def012345678 referenced but files not found' in captured.out

    def test_report_orphans_with_orphans(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_orphans with orphans (lines 53-56)."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        report = AuditReport(
            placeholders=[],
            missing=[],
            orphans=[OrphanIssue(node_id=node_id, file_path='orphan-file.md')],
            mismatches=[],
        )

        _report_orphans(report)

        captured = capsys.readouterr()
        assert '⚠ ORPHAN: File orphan-file.md exists but not in binder' in captured.out

    def test_report_mismatches_with_mismatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_mismatches with mismatches (lines 61-64)."""
        node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        node_id2 = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        report = AuditReport(
            placeholders=[],
            missing=[],
            orphans=[],
            mismatches=[MismatchIssue(file_path='mismatch-file.md', expected_id=node_id, actual_id=node_id2)],
        )

        _report_mismatches(report)

        captured = capsys.readouterr()
        assert '⚠ MISMATCH: File mismatch-file.md ID mismatch' in captured.out

    def test_audit_report_is_clean_method(self) -> None:
        """Test AuditReport.is_clean method returns correct values."""
        # Import the protocol from cli.audit to test the interface implementation

        # Create a concrete implementation for testing the protocol
        class ConcreteAuditReport:
            def __init__(
                self, placeholders: list[object], missing: list[object], orphans: list[object], mismatches: list[object]
            ) -> None:
                self.placeholders = placeholders
                self.missing = missing
                self.orphans = orphans
                self.mismatches = mismatches

            def is_clean(self) -> bool:
                """Test the protocol implementation."""
                return not (self.placeholders or self.missing or self.orphans or self.mismatches)

        # Test clean report
        clean_report = ConcreteAuditReport(placeholders=[], missing=[], orphans=[], mismatches=[])
        assert clean_report.is_clean() is True

        # Test dirty report with placeholders
        dirty_report = ConcreteAuditReport(placeholders=[1], missing=[], orphans=[], mismatches=[])
        assert dirty_report.is_clean() is False

        # Test dirty report with missing
        dirty_report2 = ConcreteAuditReport(placeholders=[], missing=[1], orphans=[], mismatches=[])
        assert dirty_report2.is_clean() is False

        # Also test the real AuditReport from use_cases
        from prosemark.app.use_cases import AuditReport as UseCaseAuditReport

        real_clean_report = UseCaseAuditReport(placeholders=[], missing=[], orphans=[], mismatches=[])
        assert real_clean_report.is_clean() is True

    @patch('prosemark.cli.audit.AuditBinder')
    def test_audit_command_spacing_after_placeholders(self, mock_audit_binder: Mock) -> None:
        """Test audit command adds spacing after placeholders when real issues exist (line 80)."""
        runner = CliRunner()

        # Mock the audit use case to return a report with both placeholders and real issues
        mock_audit = Mock()
        mock_audit_binder.return_value = mock_audit

        # Create a report with placeholders AND real issues to trigger line 80
        placeholder = PlaceholderIssue(display_title='Test Placeholder', position='[0]')
        missing = MissingIssue(node_id=NodeId('0192f0c1-2345-7123-8abc-def012345678'), expected_path='test.md')

        report = AuditReport(placeholders=[placeholder], missing=[missing], orphans=[], mismatches=[])
        mock_audit.execute.return_value = report

        # Execute the command
        result = runner.invoke(audit_command, [])

        # Should succeed and show spacing after placeholders
        assert result.exit_code == 1  # Exit code 1 because there are real issues
        output = result.output
        assert '⚠ PLACEHOLDER: "Test Placeholder" (no associated files)' in output
        assert 'Project integrity issues found:' in output
        # The spacing line should be between placeholders and real issues sections
        assert '\n\nProject integrity issues found:' in output  # Double newline shows spacing was added

    def test_report_placeholders_with_empty_list(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test _report_placeholders with empty placeholders list (line 18->exit)."""
        # Arrange - Report with no placeholders
        report = AuditReport(placeholders=[], missing=[], orphans=[], mismatches=[])

        # Act - This should hit the exit branch (18->exit) when placeholders is empty
        _report_placeholders(report)

        # Assert - No output should be produced
        captured = capsys.readouterr()
        assert captured.out == ''

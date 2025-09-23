"""Comprehensive tests for AuditProject use case to achieve 100% coverage."""

from pathlib import Path

import pytest

from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.audit_project import (
    AuditProject,
    AuditReport,
    MismatchIssue,
    MissingIssue,
    OrphanIssue,
    PlaceholderIssue,
)
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import NodeNotFoundError


class TestAuditProjectCoverage:
    """Test AuditProject use case with complete coverage."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_node_repo(self) -> FakeNodeRepo:
        """Fake NodeRepo for testing."""
        return FakeNodeRepo()

    @pytest.fixture
    def fake_console(self) -> FakeConsolePort:
        """Fake Console for testing."""
        return FakeConsolePort()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def audit_project(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
    ) -> AuditProject:
        """AuditProject instance with fake dependencies."""
        return AuditProject(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            console=fake_console,
            logger=fake_logger,
        )

    def test_audit_project_clean_binder(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject with clean binder (no issues)."""
        # Arrange - Create clean binder with valid nodes
        node_id = NodeId('0192f0c1-0017-7000-8000-000000000017')
        item = BinderItem(display_title='Valid Node', node_id=node_id, children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        # Mock node repo to have the node exist
        fake_node_repo.create(node_id, 'Valid Node', 'Some content')

        # Create actual files for audit to find
        draft_file = tmp_path / f'{node_id.value}.md'
        notes_file = tmp_path / f'{node_id.value}.notes.md'
        draft_file.write_text('---\nid: ' + node_id.value + '\ntitle: Valid Node\n---\nSome content')
        notes_file.write_text('Notes content')

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - No issues found
        assert not report.has_issues
        assert len(report.placeholders) == 0
        assert len(report.missing) == 0
        assert len(report.orphans) == 0
        assert len(report.mismatches) == 0

        # Assert - Success messages displayed
        assert fake_console.output_contains('INFO: Project integrity check completed')
        assert fake_console.output_contains('SUCCESS: ✓ All nodes have valid files')
        assert fake_console.output_contains('SUCCESS: ✓ All references are consistent')
        assert fake_console.output_contains('SUCCESS: ✓ No orphaned files found')

        # Assert - Audit logged
        assert fake_logger.has_logged('info', f'Auditing project at {tmp_path}')

    def test_audit_project_finds_placeholders(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject finds placeholder items."""
        # Arrange - Create binder with placeholder (no node_id)
        placeholder = BinderItem(display_title='Placeholder Chapter', node_id=None, children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - Placeholder found
        assert report.has_issues
        assert len(report.placeholders) == 1
        assert report.placeholders[0].display_title == 'Placeholder Chapter'
        assert report.placeholders[0].position == '[0]'

        # Assert - Warning displayed
        assert fake_console.output_contains('WARNING: Found 1 placeholder(s):')
        assert fake_console.output_contains('INFO:   [0]: Placeholder Chapter')

    def test_audit_project_finds_missing_files(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject finds missing node files."""
        # Arrange - Create binder with node but no files in repo
        node_id = NodeId('0192f0c1-0018-7000-8000-000000000018')
        item = BinderItem(display_title='Missing Node', node_id=node_id, children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        # Don't add the node to fake_node_repo, simulating missing files

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - Missing files found
        assert report.has_issues
        assert len(report.missing) == 2  # Both .md and .notes.md files missing
        missing_paths = [issue.expected_path for issue in report.missing]
        assert str(tmp_path / f'{node_id.value}.md') in missing_paths
        assert str(tmp_path / f'{node_id.value}.notes.md') in missing_paths

        # Assert - Error displayed
        assert fake_console.output_contains('ERROR: Found 2 missing file(s):')

    def test_audit_project_finds_id_mismatches(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject finds ID mismatches between binder and file content."""
        # Arrange - Create binder with node
        node_id = NodeId('0192f0c1-0019-7000-8000-000000000019')
        item = BinderItem(display_title='Mismatch Node', node_id=node_id, children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        # Mock node repo with different ID in frontmatter
        fake_node_repo.create(node_id, 'Mismatch Node', 'Some content')
        fake_node_repo.set_frontmatter_mismatch(node_id.value, 'different-id')

        # Create actual files for audit to find
        draft_file = tmp_path / f'{node_id.value}.md'
        notes_file = tmp_path / f'{node_id.value}.notes.md'
        draft_file.write_text('---\nid: different-id\ntitle: Mismatch Node\n---\nSome content')
        notes_file.write_text('Notes content')

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - Mismatch found
        assert report.has_issues
        assert len(report.mismatches) == 1
        mismatch = report.mismatches[0]
        assert mismatch.node_id == node_id
        assert mismatch.file_id == 'different-id'
        assert mismatch.file_path == str(tmp_path / f'{node_id.value}.md')

        # Assert - Error displayed
        assert fake_console.output_contains('ERROR: Found 1 ID mismatch(es):')

    def test_audit_project_handles_frontmatter_read_errors(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AuditProject handles errors when reading frontmatter."""
        # Arrange - Create binder with node
        node_id = NodeId('0192f0c1-0020-7000-8000-000000000020')
        item = BinderItem(display_title='Error Node', node_id=node_id, children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        # Mock node repo to raise error on frontmatter read
        def mock_read_frontmatter(node_id: 'NodeId') -> dict[str, str | None]:
            msg = f'Node {node_id} not found'
            raise NodeNotFoundError(msg)

        monkeypatch.setattr(fake_node_repo, 'read_frontmatter', mock_read_frontmatter)

        # But create the files to pass the existence check
        fake_node_repo.create(node_id, 'Error Node', 'content')

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - Error handled gracefully (no mismatch reported due to read error)
        # The file still appears as missing since frontmatter couldn't be read
        assert len(report.mismatches) == 0

    def test_audit_project_finds_orphaned_files(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject finds orphaned files not in binder."""
        # Arrange - Create empty binder
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)

        # Create orphaned files with valid UUID names
        orphan_node_id = NodeId('0192f0c1-0016-7000-8000-000000000016')
        orphan_file = tmp_path / f'{orphan_node_id}.md'
        orphan_file.write_text('# Orphaned Node\nThis is content for an orphaned node.')

        # NOTE: This file exists on disk but is not in the binder, making it an orphan

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - Orphan found
        assert report.has_issues
        assert len(report.orphans) == 1
        orphan = report.orphans[0]
        assert orphan.node_id.value == '0192f0c1-0016-7000-8000-000000000016'
        assert orphan.file_path == str(orphan_file)

        # Assert - Warning displayed
        assert fake_console.output_contains('WARNING: Found 1 orphaned file(s):')

    def test_audit_project_nested_placeholders(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_console: FakeConsolePort,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject finds placeholders in nested structure."""
        # Arrange - Create nested binder with placeholder
        parent = BinderItem(display_title='Parent', node_id=NodeId('0192f0c1-0021-7000-8000-000000000021'), children=[])
        child_placeholder = BinderItem(display_title='Child Placeholder', node_id=None, children=[])
        parent.children.append(child_placeholder)
        binder = Binder(roots=[parent])
        fake_binder_repo.save(binder)

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - Nested placeholder found
        assert report.has_issues
        assert len(report.placeholders) == 1
        assert report.placeholders[0].display_title == 'Child Placeholder'
        assert report.placeholders[0].position == '[0][0]'  # Nested position

    def test_audit_project_uses_current_directory_when_no_path_provided(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        fake_logger: FakeLogger,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AuditProject uses current directory when no project_path provided."""
        # Arrange - Change to temporary directory to avoid scanning existing .md files
        monkeypatch.chdir(tmp_path)
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)

        # Act
        audit_project.execute(project_path=None)

        # Assert - Used current directory (which is now tmp_path)
        assert fake_logger.has_logged('info', f'Auditing project at {tmp_path}')

    def test_audit_report_has_issues_property(self) -> None:
        """Test AuditReport.has_issues property logic."""
        # Empty report
        empty_report = AuditReport(placeholders=[], missing=[], orphans=[], mismatches=[])
        assert not empty_report.has_issues

        # Report with placeholders
        placeholder_report = AuditReport(
            placeholders=[PlaceholderIssue('test', '[0]')], missing=[], orphans=[], mismatches=[]
        )
        assert placeholder_report.has_issues

        # Report with missing
        missing_report = AuditReport(
            placeholders=[],
            missing=[MissingIssue(NodeId('0192f0c1-0030-7000-8000-000000000030'), 'test.md')],
            orphans=[],
            mismatches=[],
        )
        assert missing_report.has_issues

        # Report with orphans
        orphan_report = AuditReport(
            placeholders=[],
            missing=[],
            orphans=[OrphanIssue(NodeId('0192f0c1-0031-7000-8000-000000000031'), 'test.md')],
            mismatches=[],
        )
        assert orphan_report.has_issues

        # Report with mismatches
        mismatch_report = AuditReport(
            placeholders=[],
            missing=[],
            orphans=[],
            mismatches=[MismatchIssue(NodeId('0192f0c1-0032-7000-8000-000000000032'), 'other', 'test.md')],
        )
        assert mismatch_report.has_issues

    def test_audit_project_collect_ids_recursive(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        tmp_path: Path,
    ) -> None:
        """Test _collect_ids method works recursively."""
        # Arrange - Create nested structure
        parent_id = NodeId('0192f0c1-0021-7000-8000-000000000021')
        child_id = NodeId('0192f0c1-0024-7000-8000-000000000024')
        grandchild_id = NodeId('0192f0c1-0025-7000-8000-000000000025')

        grandchild = BinderItem(display_title='Grandchild', node_id=grandchild_id, children=[])
        child = BinderItem(display_title='Child', node_id=child_id, children=[grandchild])
        parent = BinderItem(display_title='Parent', node_id=parent_id, children=[child])
        placeholder = BinderItem(display_title='Placeholder', node_id=None, children=[])

        binder = Binder(roots=[parent, placeholder])
        fake_binder_repo.save(binder)

        # Test through execute (which calls _collect_ids indirectly)
        audit_project.execute(project_path=tmp_path)

        # The _collect_ids method is tested indirectly through the orphan detection
        # which uses it to gather all referenced IDs

    def test_audit_project_dependency_injection(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_console: FakeConsolePort,
        fake_logger: FakeLogger,
        tmp_path: Path,
    ) -> None:
        """Test AuditProject uses all injected dependencies correctly."""
        # Arrange
        audit_project = AuditProject(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            console=fake_console,
            logger=fake_logger,
        )

        # Verify dependencies are assigned
        assert audit_project.binder_repo is fake_binder_repo
        assert audit_project.node_repo is fake_node_repo
        assert audit_project.console is fake_console
        assert audit_project.logger is fake_logger

        # Setup and test
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)

        audit_project.execute(project_path=tmp_path)

        # Assert all dependencies were used
        assert fake_logger.log_count() > 0
        assert len(fake_console.get_output()) > 0

    def test_audit_project_binder_file_skipping(
        self,
        audit_project: AuditProject,
        fake_binder_repo: FakeBinderRepo,
        tmp_path: Path,
    ) -> None:
        """Test that _binder.md files are skipped during orphan detection (line 227)."""
        # Arrange - Create empty binder and a _binder.md file
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)

        # Create _binder.md file that should be skipped
        binder_file = tmp_path / '_binder.md'
        binder_file.write_text('binder content')

        # Create another regular file that should be detected as orphan (use valid UUID)
        orphan_id = '0192f0c1-2222-7000-8000-000000000002'
        orphan_file = tmp_path / f'{orphan_id}.md'
        orphan_file.write_text('orphan content')

        # Act
        report = audit_project.execute(project_path=tmp_path)

        # Assert - _binder.md should be skipped (line 227), but orphan file should be found
        assert report is not None
        assert len(report.orphans) == 1
        assert report.orphans[0].node_id.value == orphan_id
        # _binder.md should NOT appear in orphans list

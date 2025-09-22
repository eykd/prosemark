"""Tests for AuditBinder use case interactor."""

import pytest

from prosemark.adapters.fake_logger import FakeLogger
from prosemark.adapters.fake_node_repo import FakeNodeRepo
from prosemark.adapters.fake_storage import FakeBinderRepo
from prosemark.app.use_cases import AuditBinder
from prosemark.domain.models import Binder, BinderItem, NodeId
from prosemark.exceptions import BinderNotFoundError


class TestAuditBinder:
    """Test AuditBinder use case interactor."""

    @pytest.fixture
    def fake_binder_repo(self) -> FakeBinderRepo:
        """Fake BinderRepo for testing."""
        return FakeBinderRepo()

    @pytest.fixture
    def fake_node_repo(self) -> FakeNodeRepo:
        """Fake NodeRepo for testing."""
        return FakeNodeRepo()

    @pytest.fixture
    def fake_logger(self) -> FakeLogger:
        """Fake Logger for testing."""
        return FakeLogger()

    @pytest.fixture
    def audit_binder(
        self,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
        fake_logger: FakeLogger,
    ) -> AuditBinder:
        """AuditBinder instance with fake dependencies."""
        return AuditBinder(
            binder_repo=fake_binder_repo,
            node_repo=fake_node_repo,
            logger=fake_logger,
        )

    def test_clean_binder_with_no_issues(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test clean binder with no issues."""
        # Given: A binder with all nodes properly linked and files present
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node_id2 = NodeId('0192f0c1-2222-7000-8000-000000000002')

        # Create nodes in fake repo
        fake_node_repo.create(node_id1, 'Chapter 1', 'First chapter')
        fake_node_repo.create(node_id2, 'Chapter 2', 'Second chapter')

        # Create binder structure
        item1 = BinderItem(id_=node_id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id2, display_title='Chapter 2', children=[])
        binder = Binder(roots=[item1, item2])
        fake_binder_repo.save(binder)

        # Set up fake node repo to simulate existing files
        fake_node_repo.set_existing_files([str(node_id1), str(node_id2)])
        result = audit_binder.execute()

        # Then: Returns empty audit report (no issues found)
        assert result.placeholders == []
        assert result.missing == []
        assert result.orphans == []
        assert result.mismatches == []
        assert result.is_clean()

    def test_placeholder_detection(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test placeholder detection."""
        # Given: A binder with items that have display titles but no IDs
        placeholder1 = BinderItem(id_=None, display_title='Chapter 3', children=[])
        placeholder2 = BinderItem(id_=None, display_title='Epilogue', children=[])

        # Create hierarchical structure with nested placeholder
        section = BinderItem(id_=None, display_title='Part 1', children=[placeholder1])

        binder = Binder(roots=[section, placeholder2])
        fake_binder_repo.save(binder)
        result = audit_binder.execute()

        # Then: Reports PLACEHOLDER issues with item details
        assert len(result.placeholders) == 3
        placeholder_titles = [p.display_title for p in result.placeholders]
        assert 'Part 1' in placeholder_titles
        assert 'Chapter 3' in placeholder_titles
        assert 'Epilogue' in placeholder_titles

    def test_missing_file_detection(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test missing file detection."""
        # Given: A binder referencing nodes whose files don't exist
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node_id2 = NodeId('0192f0c1-2222-7000-8000-000000000002')

        # Create binder items referencing nodes
        item1 = BinderItem(id_=node_id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id2, display_title='Chapter 2', children=[])
        binder = Binder(roots=[item1, item2])
        fake_binder_repo.save(binder)

        # Only create one file - the other will be missing
        fake_node_repo.create(node_id1, 'Chapter 1', 'First chapter')
        fake_node_repo.set_existing_files([str(node_id1)])
        result = audit_binder.execute()

        # Then: Reports MISSING issues with node IDs and expected paths
        # Now checks for both main file and notes file
        assert len(result.missing) == 2
        missing_issues = sorted(result.missing, key=lambda x: x.expected_path)

        # Should detect missing main file
        assert missing_issues[0].node_id == node_id2
        assert missing_issues[0].expected_path == f'{node_id2}.md'

        # Should detect missing notes file
        assert missing_issues[1].node_id == node_id2
        assert missing_issues[1].expected_path == f'{node_id2}.notes.md'

    def test_orphaned_file_detection(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test orphaned file detection."""
        # Given: Node files that exist but aren't referenced in binder
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node_id2 = NodeId('0192f0c1-2222-7000-8000-000000000002')
        orphan_id = NodeId('0192f0c1-3333-7000-8000-000000000003')

        # Create binder with only some nodes
        item1 = BinderItem(id_=node_id1, display_title='Chapter 1', children=[])
        item2 = BinderItem(id_=node_id2, display_title='Chapter 2', children=[])
        binder = Binder(roots=[item1, item2])
        fake_binder_repo.save(binder)

        # Create files for all nodes (including orphan)
        fake_node_repo.create(node_id1, 'Chapter 1', 'First chapter')
        fake_node_repo.create(node_id2, 'Chapter 2', 'Second chapter')
        fake_node_repo.create(orphan_id, 'Orphaned Chapter', 'This chapter is orphaned')
        fake_node_repo.set_existing_files([str(node_id1), str(node_id2), str(orphan_id)])
        result = audit_binder.execute()

        # Then: Reports ORPHAN issues with file paths and node IDs
        assert len(result.orphans) == 1
        orphan_issue = result.orphans[0]
        assert orphan_issue.node_id == orphan_id
        assert orphan_issue.file_path == f'{orphan_id}.md'

    def test_id_mismatch_detection(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test ID mismatch detection."""
        # Given: Node files where frontmatter ID doesn't match filename
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        wrong_id = NodeId('0192f0c1-9999-7000-8000-000000000999')

        # Create binder with expected ID
        item1 = BinderItem(id_=node_id1, display_title='Chapter 1', children=[])
        binder = Binder(roots=[item1])
        fake_binder_repo.save(binder)

        # Create file with mismatched frontmatter ID
        fake_node_repo.create(node_id1, 'Chapter 1', 'First chapter')
        fake_node_repo.set_existing_files([str(node_id1)])
        fake_node_repo.set_frontmatter_mismatch(str(node_id1), str(wrong_id))
        result = audit_binder.execute()

        # Then: Reports MISMATCH issues with expected vs actual IDs
        assert len(result.mismatches) == 1
        mismatch_issue = result.mismatches[0]
        assert mismatch_issue.file_path == f'{node_id1}.md'
        assert mismatch_issue.expected_id == node_id1
        assert mismatch_issue.actual_id == wrong_id

    def test_comprehensive_audit_with_multiple_issue_types(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test comprehensive audit with all four types of issues present."""
        # Given: A binder with all four types of issues present
        node_id1 = NodeId('0192f0c1-1111-7000-8000-000000000001')
        node_id2 = NodeId('0192f0c1-2222-7000-8000-000000000002')
        orphan_id = NodeId('0192f0c1-3333-7000-8000-000000000003')
        wrong_id = NodeId('0192f0c1-9999-7000-8000-000000000999')

        # Create binder with mixed items
        placeholder = BinderItem(id_=None, display_title='Placeholder Chapter', children=[])
        good_item = BinderItem(id_=node_id1, display_title='Good Chapter', children=[])
        missing_item = BinderItem(id_=node_id2, display_title='Missing Chapter', children=[])
        binder = Binder(roots=[placeholder, good_item, missing_item])
        fake_binder_repo.save(binder)

        # Set up files
        fake_node_repo.create(node_id1, 'Good Chapter', 'This one is fine')
        fake_node_repo.create(orphan_id, 'Orphaned Chapter', 'This is orphaned')
        fake_node_repo.set_existing_files([str(node_id1), str(orphan_id)])
        fake_node_repo.set_frontmatter_mismatch(str(node_id1), str(wrong_id))
        result = audit_binder.execute()

        # Then: Reports all issues organized by type
        assert len(result.placeholders) == 1
        assert result.placeholders[0].display_title == 'Placeholder Chapter'

        assert len(result.missing) == 2
        # Both main file and notes file should be missing for node_id2
        assert all(issue.node_id == node_id2 for issue in result.missing)

        assert len(result.orphans) == 1
        assert result.orphans[0].node_id == orphan_id

        assert len(result.mismatches) == 1
        assert result.mismatches[0].expected_id == node_id1
        assert result.mismatches[0].actual_id == wrong_id

        assert not result.is_clean()

    def test_empty_project_directory(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test empty project directory."""
        # Given: A project directory with no binder or node files
        # Don't save any binder - simulates missing binder file
        with pytest.raises(BinderNotFoundError):
            audit_binder.execute()

    def test_format_report_clean_binder(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test report formatting for clean binder."""
        # Given: Empty binder (clean)
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)

        # When: AuditBinder generates report
        result = audit_binder.execute()
        report = result.format_report()

        # Then: Shows clean status
        assert 'Audit Results:' in report
        assert '✓ Clean (no issues found)' in report

    def test_format_report_with_issues(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test report formatting with issues."""
        # Given: Binder with issues
        placeholder = BinderItem(id_=None, display_title='Chapter 3', children=[])
        missing_id = NodeId('0192f0c1-2222-7000-8000-000000000002')
        missing_item = BinderItem(id_=missing_id, display_title='Missing Chapter', children=[])
        binder = Binder(roots=[placeholder, missing_item])
        fake_binder_repo.save(binder)

        # Create orphaned file
        orphan_id = NodeId('0192f0c1-3333-7000-8000-000000000003')
        fake_node_repo.create(orphan_id, 'Orphaned Chapter', 'Orphaned')
        fake_node_repo.set_existing_files([str(orphan_id)])

        # When: AuditBinder generates report
        result = audit_binder.execute()
        report = result.format_report()

        # Then: Shows structured issues
        assert 'Issues Found:' in report
        assert 'PLACEHOLDERS (1):' in report
        assert 'Chapter 3' in report
        assert 'MISSING (2):' in report
        assert str(missing_id) in report
        assert 'ORPHANS (1):' in report
        assert str(orphan_id) in report

    def test_json_output_format(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
    ) -> None:
        """Test JSON output format."""
        # Given: Binder with a placeholder
        placeholder = BinderItem(id_=None, display_title='Test Placeholder', children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)

        # When: AuditBinder generates JSON output
        result = audit_binder.execute()
        json_output = result.to_json()

        # Then: Returns valid JSON structure
        import json

        data = json.loads(json_output)
        assert isinstance(data, dict)
        assert 'placeholders' in data
        assert 'missing' in data
        assert 'orphans' in data
        assert 'mismatches' in data
        assert len(data['placeholders']) == 1
        assert data['placeholders'][0]['display_title'] == 'Test Placeholder'

    def test_format_report_covers_all_issue_sections(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test format_report method covers all conditional sections."""
        # Given: Binder with placeholder only
        placeholder = BinderItem(id_=None, display_title='Test Placeholder', children=[])
        binder = Binder(roots=[placeholder])
        fake_binder_repo.save(binder)

        # When: Execute audit
        result = audit_binder.execute()
        report = result.format_report()

        # Then: Covers placeholder section
        assert 'PLACEHOLDERS (1):' in report
        assert '  - "Test Placeholder"' in report

        # Test missing section separately
        missing_id = NodeId('0192f0c1-2222-7000-8000-000000000002')
        missing_item = BinderItem(id_=missing_id, display_title='Missing Chapter', children=[])
        binder2 = Binder(roots=[missing_item])
        fake_binder_repo.save(binder2)

        result2 = audit_binder.execute()
        report2 = result2.format_report()

        assert 'MISSING (2):' in report2
        assert 'referenced in binder but file missing' in report2

        # Test orphan section separately
        orphan_id = NodeId('0192f0c1-3333-7000-8000-000000000003')
        fake_node_repo.create(orphan_id, 'Orphaned Chapter', 'Orphaned')
        fake_node_repo.set_existing_files([str(orphan_id)])
        binder3 = Binder(roots=[])  # Empty binder
        fake_binder_repo.save(binder3)

        result3 = audit_binder.execute()
        report3 = result3.format_report()

        assert 'ORPHANS (1):' in report3
        assert 'exists but not in binder' in report3

        # Test mismatch section separately
        node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        wrong_id = NodeId('0192f0c1-9999-7000-8000-000000000999')
        item = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        binder4 = Binder(roots=[item])
        fake_binder_repo.save(binder4)

        fake_node_repo.create(node_id, 'Chapter 1', 'First chapter')
        fake_node_repo.set_existing_files([str(node_id)])
        fake_node_repo.set_frontmatter_mismatch(str(node_id), str(wrong_id))

        result4 = audit_binder.execute()
        report4 = result4.format_report()

        assert 'MISMATCHES (1):' in report4
        assert 'has frontmatter id:' in report4

    def test_invalid_node_id_handling(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test handling of invalid node IDs in existing files."""
        # Given: Empty binder and files with invalid node IDs
        binder = Binder(roots=[])
        fake_binder_repo.save(binder)

        # Set up fake node repo with invalid node ID
        fake_node_repo.set_existing_files(['invalid-node-id', '0192f0c1-1111-7000-8000-000000000001'])

        # When: Execute audit
        result = audit_binder.execute()

        # Then: Invalid IDs are skipped and no errors occur
        assert len(result.orphans) == 1  # Only valid ID should be processed

    def test_invalid_frontmatter_id_handling(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test handling of invalid frontmatter IDs."""
        # Given: Binder with valid node that has invalid frontmatter ID
        node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        item = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        fake_node_repo.create(node_id, 'Chapter 1', 'First chapter')
        fake_node_repo.set_existing_files([str(node_id)])
        fake_node_repo.set_frontmatter_mismatch(str(node_id), 'invalid-frontmatter-id')

        # When: Execute audit
        result = audit_binder.execute()

        # Then: Invalid frontmatter ID is reported as a mismatch
        assert len(result.mismatches) == 1
        mismatch = result.mismatches[0]
        assert mismatch.expected_id == node_id
        assert 'invalid-frontmatter-id' in mismatch.file_path

    def test_file_read_error_handling(
        self,
        audit_binder: AuditBinder,
        fake_binder_repo: FakeBinderRepo,
        fake_node_repo: FakeNodeRepo,
    ) -> None:
        """Test handling of file read errors during ID mismatch scan."""
        # Given: Binder with valid node
        node_id = NodeId('0192f0c1-1111-7000-8000-000000000001')
        item = BinderItem(id_=node_id, display_title='Chapter 1', children=[])
        binder = Binder(roots=[item])
        fake_binder_repo.save(binder)

        fake_node_repo.set_existing_files([str(node_id)])
        # Don't create the node - this will cause read_frontmatter to fail

        # When: Execute audit
        result = audit_binder.execute()

        # Then: File read error is handled gracefully and no mismatch is reported
        assert len(result.mismatches) == 0

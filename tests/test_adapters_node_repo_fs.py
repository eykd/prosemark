"""Tests for NodeRepoFs adapter."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from prosemark.adapters.node_repo_fs import NodeRepoFs
from prosemark.domain.models import NodeId
from prosemark.exceptions import (
    EditorError,
    FileSystemError,
    FrontmatterFormatError,
    InvalidPartError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
)


class TestNodeRepoFs:
    """Test NodeRepoFs adapter."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.mock_editor = Mock()
        self.mock_clock = Mock()
        self.mock_frontmatter_codec = Mock()
        self.test_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

    def _create_repo(self, project_path: Path) -> NodeRepoFs:
        """Create a NodeRepoFs instance with mocked dependencies."""
        repo = NodeRepoFs(
            project_path=project_path,
            editor=self.mock_editor,
            clock=self.mock_clock,
        )
        # Inject the mock codec
        repo.frontmatter_codec = self.mock_frontmatter_codec
        return repo

    def test_init_sets_attributes(self, tmp_path: Path) -> None:
        """Test that __init__ properly sets instance attributes."""
        test_project_path = tmp_path / 'test_init'
        repo = self._create_repo(test_project_path)

        assert repo.project_path == test_project_path
        assert repo.editor == self.mock_editor
        assert repo.clock == self.mock_clock

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.write_text')
    def test_create_success(self, mock_write_text: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test successful node creation."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = False
        self.mock_clock.now_iso.return_value = '2023-01-01T00:00:00Z'
        self.mock_frontmatter_codec.generate.return_value = '---\nfrontmatter\n---\n'

        repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

        # Verify frontmatter generation
        expected_frontmatter = {
            'id': str(self.test_node_id),
            'title': 'Test Title',
            'synopsis': 'Test Synopsis',
            'created': '2023-01-01T00:00:00Z',
            'updated': '2023-01-01T00:00:00Z',
        }
        self.mock_frontmatter_codec.generate.assert_called_once_with(expected_frontmatter, '')

        # Verify file writing
        assert mock_write_text.call_count == 2

    @patch('pathlib.Path.exists')
    def test_create_node_already_exists_draft(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test create raises error when draft file already exists."""
        repo = self._create_repo(tmp_path / 'test_project')
        # First call for draft file returns True, second call for notes file returns False
        mock_exists.side_effect = [True, False]

        with pytest.raises(NodeAlreadyExistsError, match='Node files already exist'):
            repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

    @patch('pathlib.Path.exists')
    def test_create_node_already_exists_notes(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test create raises error when notes file already exists."""
        repo = self._create_repo(tmp_path / 'test_project')
        # First call for draft file returns False, second call for notes file returns True
        mock_exists.side_effect = [False, True]

        with pytest.raises(NodeAlreadyExistsError, match='Node files already exist'):
            repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.write_text')
    def test_create_os_error(self, mock_write_text: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test create handles OSError."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = False
        self.mock_clock.now_iso.return_value = '2023-01-01T00:00:00Z'
        self.mock_frontmatter_codec.generate.return_value = '---\nfrontmatter\n---\n'
        mock_write_text.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot create node files'):
            repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_frontmatter_success(self, mock_read_text: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test successful frontmatter reading."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        mock_read_text.return_value = '---\ntitle: Test\n---\nContent'
        self.mock_frontmatter_codec.parse.return_value = ({'title': 'Test'}, 'Content')

        result = repo.read_frontmatter(self.test_node_id)

        assert result == {'title': 'Test'}
        mock_read_text.assert_called_once_with(encoding='utf-8')

    @patch('pathlib.Path.exists')
    def test_read_frontmatter_file_not_found(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test read_frontmatter with missing file."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = False

        with pytest.raises(NodeNotFoundError, match='Node file not found'):
            repo.read_frontmatter(self.test_node_id)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_frontmatter_os_error(self, mock_read_text: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test read_frontmatter handles OSError."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot read node file'):
            repo.read_frontmatter(self.test_node_id)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_frontmatter_parse_error(self, mock_read_text: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test read_frontmatter handles frontmatter parse error."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        mock_read_text.return_value = '---\nmalformed yaml\n---\nContent'
        self.mock_frontmatter_codec.parse.side_effect = Exception('Parse error')

        with pytest.raises(FrontmatterFormatError, match='Invalid frontmatter'):
            repo.read_frontmatter(self.test_node_id)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_write_frontmatter_success(
        self, mock_write_text: Mock, mock_read_text: Mock, mock_exists: Mock, tmp_path: Path
    ) -> None:
        """Test successful frontmatter writing."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        mock_read_text.return_value = '---\ntitle: Old\n---\nContent'
        self.mock_clock.now_iso.return_value = '2023-01-01T00:00:00Z'
        self.mock_frontmatter_codec.update_frontmatter.return_value = '---\ntitle: New\n---\nContent'

        frontmatter = {'title': 'New'}
        repo.write_frontmatter(self.test_node_id, frontmatter)

        # Verify updated frontmatter includes timestamp
        expected_frontmatter = {'title': 'New', 'updated': '2023-01-01T00:00:00Z'}
        self.mock_frontmatter_codec.update_frontmatter.assert_called_once_with(
            '---\ntitle: Old\n---\nContent', expected_frontmatter
        )
        mock_write_text.assert_called_once_with('---\ntitle: New\n---\nContent', encoding='utf-8')

    @patch('pathlib.Path.exists')
    def test_write_frontmatter_file_not_found(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test write_frontmatter with missing file."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = False

        with pytest.raises(NodeNotFoundError, match='Node file not found'):
            repo.write_frontmatter(self.test_node_id, {'title': 'Test'})

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_write_frontmatter_os_error(self, mock_read_text: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test write_frontmatter handles OSError."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot write node file'):
            repo.write_frontmatter(self.test_node_id, {'title': 'Test'})

    @patch('pathlib.Path.exists')
    def test_open_in_editor_draft_success(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test successful editor opening for draft."""
        test_project_path = tmp_path / 'test_project'
        repo = self._create_repo(test_project_path)
        mock_exists.return_value = True

        repo.open_in_editor(self.test_node_id, 'draft')

        expected_path = str(test_project_path / f'{self.test_node_id}.md')
        self.mock_editor.open.assert_called_once_with(expected_path, cursor_hint=None)

    @patch('pathlib.Path.exists')
    def test_open_in_editor_notes_success(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test successful editor opening for notes."""
        test_project_path = tmp_path / 'test_project'
        repo = self._create_repo(test_project_path)
        mock_exists.return_value = True

        repo.open_in_editor(self.test_node_id, 'notes')

        expected_path = str(test_project_path / f'{self.test_node_id}.notes.md')
        self.mock_editor.open.assert_called_once_with(expected_path, cursor_hint=None)

    @patch('pathlib.Path.exists')
    def test_open_in_editor_synopsis_success(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test successful editor opening for synopsis."""
        test_project_path = tmp_path / 'test_project'
        repo = self._create_repo(test_project_path)
        mock_exists.return_value = True

        repo.open_in_editor(self.test_node_id, 'synopsis')

        expected_path = str(test_project_path / f'{self.test_node_id}.md')
        self.mock_editor.open.assert_called_once_with(expected_path, cursor_hint='1')

    def test_open_in_editor_invalid_part(self, tmp_path: Path) -> None:
        """Test open_in_editor with invalid part."""
        repo = self._create_repo(tmp_path / 'test_project')
        with pytest.raises(InvalidPartError, match='Invalid part: invalid'):
            repo.open_in_editor(self.test_node_id, 'invalid')

    @patch('pathlib.Path.exists')
    def test_open_in_editor_file_not_found(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test open_in_editor with missing file."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = False

        with pytest.raises(NodeNotFoundError, match='Node file not found'):
            repo.open_in_editor(self.test_node_id, 'draft')

    @patch('pathlib.Path.exists')
    def test_open_in_editor_editor_error(self, mock_exists: Mock, tmp_path: Path) -> None:
        """Test open_in_editor handles editor exceptions."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        self.mock_editor.open.side_effect = Exception('Editor failed')

        with pytest.raises(EditorError, match='Failed to open editor'):
            repo.open_in_editor(self.test_node_id, 'draft')

    def test_delete_no_delete_files(self, tmp_path: Path) -> None:
        """Test delete with delete_files=False does nothing."""
        repo = self._create_repo(tmp_path / 'test_project')
        repo.delete(self.test_node_id, delete_files=False)
        # Should not raise any errors and do nothing

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_success(self, mock_unlink: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test successful file deletion."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True

        repo.delete(self.test_node_id, delete_files=True)

        assert mock_unlink.call_count == 2  # Both draft and notes files

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_partial_exists(self, mock_unlink: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test deletion when only some files exist."""
        repo = self._create_repo(tmp_path / 'test_project')
        # First call for draft file returns True, second call for notes file returns False
        mock_exists.side_effect = [True, False]

        repo.delete(self.test_node_id, delete_files=True)

        mock_unlink.assert_called_once()  # Only draft file deleted

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_only_notes_exists(self, mock_unlink: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test deletion when only notes file exists."""
        repo = self._create_repo(tmp_path / 'test_project')
        # First call for draft file returns False, second call for notes file returns True
        mock_exists.side_effect = [False, True]

        repo.delete(self.test_node_id, delete_files=True)

        mock_unlink.assert_called_once()  # Only notes file deleted

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_os_error(self, mock_unlink: Mock, mock_exists: Mock, tmp_path: Path) -> None:
        """Test delete handles OSError."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_exists.return_value = True
        mock_unlink.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot delete node files'):
            repo.delete(self.test_node_id, delete_files=True)

    def test_get_existing_files_handles_notes_files(self, tmp_path: Path) -> None:
        """Test get_existing_files skips .notes.md files (line 278)."""
        test_dir = tmp_path / 'test_project'
        test_dir.mkdir()

        # Create a file that would pass _is_valid_node_id but has .notes suffix
        # "some-reasonable-id.notes" should pass _is_reasonable_node_id
        # (alphanumeric+hyphens, >3 chars, not reserved) and trigger the .notes check
        valid_notes_file = test_dir / 'some-reasonable-id.notes.md'
        valid_notes_file.write_text('notes content')

        # Create a regular file that should be included
        regular_file = test_dir / '0192f0c1-2345-7123-8abc-def012345678.md'
        regular_file.write_text('content')

        repo = self._create_repo(test_dir)
        existing_files = repo.get_existing_files()

        # Only the regular file should be included, not the notes file
        assert len(existing_files) == 1
        assert NodeId('0192f0c1-2345-7123-8abc-def012345678') in existing_files

    @patch('pathlib.Path.glob')
    def test_get_existing_files_handles_os_error(self, mock_glob: Mock, tmp_path: Path) -> None:
        """Test get_existing_files handles OSError (lines 288-290)."""
        repo = self._create_repo(tmp_path / 'test_project')
        mock_glob.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot scan directory for node files'):
            repo.get_existing_files()

    def test_is_valid_node_id_empty_filename(self, tmp_path: Path) -> None:
        """Test _is_valid_node_id handles empty filename (line 309)."""
        repo = self._create_repo(tmp_path)

        # Test _is_valid_node_id directly with empty string
        # This should return False due to line 309
        assert not repo._is_valid_node_id('')

    def test_is_uuid7_format_invalid_dash_count(self, tmp_path: Path) -> None:
        """Test _is_uuid7_format with wrong number of dashes (line 325)."""
        repo = self._create_repo(tmp_path)

        # Test with 36 chars but wrong number of dashes (should have 5 parts when split by '-')
        # This has 36 chars but only 3 dashes (4 parts) instead of 4 dashes (5 parts)
        invalid_uuid = '0192f0c1-2345-7123-8abcdef0123456789'  # 36 chars, wrong dash pattern
        assert len(invalid_uuid) == 36
        assert len(invalid_uuid.split('-')) == 4  # Should be 5 for valid UUID

        # Test _is_uuid7_format directly - should return False due to line 325
        assert not repo._is_uuid7_format(invalid_uuid)

        # This should be excluded from get_existing_files
        existing = repo.get_existing_files()
        assert len(existing) == 0  # Invalid format should be excluded

    def test_is_uuid7_format_wrong_part_lengths(self, tmp_path: Path) -> None:
        """Test _is_uuid7_format with wrong part lengths (line 331)."""
        repo = self._create_repo(tmp_path)

        # Create file with wrong part lengths (second part too long, third too short)
        invalid_filename = '0192f0c1-23456-123-8abc-def012345678'
        (tmp_path / f'{invalid_filename}.md').write_text('content')

        # This should be excluded from get_existing_files
        existing = repo.get_existing_files()
        assert len(existing) == 0  # Invalid format should be excluded

    def test_is_uuid7_format_invalid_hex(self, tmp_path: Path) -> None:
        """Test _is_uuid7_format with invalid hex characters (lines 337-338)."""
        repo = self._create_repo(tmp_path)

        # Create file with invalid hex characters
        invalid_filename = '0192f0g1-2345-7123-8abc-def012345678'  # 'g' is not hex
        (tmp_path / f'{invalid_filename}.md').write_text('content')

        # This should be excluded from get_existing_files
        existing = repo.get_existing_files()
        assert len(existing) == 0  # Invalid format should be excluded

    def test_file_exists_notes_type(self, tmp_path: Path) -> None:
        """Test file_exists with notes file type (line 367)."""
        test_dir = tmp_path / 'test_project'
        test_dir.mkdir()
        notes_file = test_dir / f'{self.test_node_id}.notes.md'
        notes_file.write_text('notes content')

        repo = self._create_repo(test_dir)
        assert repo.file_exists(self.test_node_id, 'notes')

    def test_file_exists_draft_type(self, tmp_path: Path) -> None:
        """Test file_exists with draft file type (line 367)."""
        test_dir = tmp_path / 'test_project'
        test_dir.mkdir()
        draft_file = test_dir / f'{self.test_node_id}.md'
        draft_file.write_text('draft content')

        repo = self._create_repo(test_dir)
        assert repo.file_exists(self.test_node_id, 'draft')

    def test_file_exists_invalid_type(self, tmp_path: Path) -> None:
        """Test file_exists with invalid file type (lines 371-372)."""
        repo = self._create_repo(tmp_path)

        with pytest.raises(ValueError, match=r'Invalid file_type: invalid\. Must be "draft" or "notes"'):
            repo.file_exists(self.test_node_id, 'invalid')

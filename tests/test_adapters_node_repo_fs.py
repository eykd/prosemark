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
        self.test_project_path = Path('/tmp/test_project')  # noqa: S108
        self.mock_editor = Mock()
        self.mock_clock = Mock()
        self.mock_frontmatter_codec = Mock()

        self.repo = NodeRepoFs(
            project_path=self.test_project_path,
            editor=self.mock_editor,
            clock=self.mock_clock,
        )
        # Inject the mock codec
        self.repo.frontmatter_codec = self.mock_frontmatter_codec

        self.test_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')

    def test_init_sets_attributes(self) -> None:
        """Test that __init__ properly sets instance attributes."""
        repo = NodeRepoFs(
            project_path=self.test_project_path,
            editor=self.mock_editor,
            clock=self.mock_clock,
        )

        assert repo.project_path == self.test_project_path
        assert repo.editor == self.mock_editor
        assert repo.clock == self.mock_clock

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.write_text')
    def test_create_success(self, mock_write_text: Mock, mock_exists: Mock) -> None:
        """Test successful node creation."""
        mock_exists.return_value = False
        self.mock_clock.now_iso.return_value = '2023-01-01T00:00:00Z'
        self.mock_frontmatter_codec.generate.return_value = '---\nfrontmatter\n---\n# Draft Content\n'

        self.repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

        # Verify frontmatter generation
        expected_frontmatter = {
            'id': str(self.test_node_id),
            'title': 'Test Title',
            'synopsis': 'Test Synopsis',
            'created': '2023-01-01T00:00:00Z',
            'updated': '2023-01-01T00:00:00Z',
        }
        self.mock_frontmatter_codec.generate.assert_called_once_with(expected_frontmatter, '\n# Draft Content\n')

        # Verify file writing
        assert mock_write_text.call_count == 2

    @patch('pathlib.Path.exists')
    def test_create_node_already_exists_draft(self, mock_exists: Mock) -> None:
        """Test create raises error when draft file already exists."""
        # First call for draft file returns True, second call for notes file returns False
        mock_exists.side_effect = [True, False]

        with pytest.raises(NodeAlreadyExistsError, match='Node files already exist'):
            self.repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

    @patch('pathlib.Path.exists')
    def test_create_node_already_exists_notes(self, mock_exists: Mock) -> None:
        """Test create raises error when notes file already exists."""
        # First call for draft file returns False, second call for notes file returns True
        mock_exists.side_effect = [False, True]

        with pytest.raises(NodeAlreadyExistsError, match='Node files already exist'):
            self.repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.write_text')
    def test_create_os_error(self, mock_write_text: Mock, mock_exists: Mock) -> None:
        """Test create handles OSError."""
        mock_exists.return_value = False
        self.mock_clock.now_iso.return_value = '2023-01-01T00:00:00Z'
        self.mock_frontmatter_codec.generate.return_value = '---\nfrontmatter\n---\n# Draft Content\n'
        mock_write_text.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot create node files'):
            self.repo.create(self.test_node_id, 'Test Title', 'Test Synopsis')

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_frontmatter_success(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test successful frontmatter reading."""
        mock_exists.return_value = True
        mock_read_text.return_value = '---\ntitle: Test\n---\nContent'
        self.mock_frontmatter_codec.parse.return_value = ({'title': 'Test'}, 'Content')

        result = self.repo.read_frontmatter(self.test_node_id)

        assert result == {'title': 'Test'}
        mock_read_text.assert_called_once_with(encoding='utf-8')

    @patch('pathlib.Path.exists')
    def test_read_frontmatter_file_not_found(self, mock_exists: Mock) -> None:
        """Test read_frontmatter with missing file."""
        mock_exists.return_value = False

        with pytest.raises(NodeNotFoundError, match='Node file not found'):
            self.repo.read_frontmatter(self.test_node_id)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_frontmatter_os_error(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test read_frontmatter handles OSError."""
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot read node file'):
            self.repo.read_frontmatter(self.test_node_id)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_frontmatter_parse_error(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test read_frontmatter handles frontmatter parse error."""
        mock_exists.return_value = True
        mock_read_text.return_value = '---\nmalformed yaml\n---\nContent'
        self.mock_frontmatter_codec.parse.side_effect = Exception('Parse error')

        with pytest.raises(FrontmatterFormatError, match='Invalid frontmatter'):
            self.repo.read_frontmatter(self.test_node_id)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_write_frontmatter_success(self, mock_write_text: Mock, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test successful frontmatter writing."""
        mock_exists.return_value = True
        mock_read_text.return_value = '---\ntitle: Old\n---\nContent'
        self.mock_clock.now_iso.return_value = '2023-01-01T00:00:00Z'
        self.mock_frontmatter_codec.update_frontmatter.return_value = '---\ntitle: New\n---\nContent'

        frontmatter = {'title': 'New'}
        self.repo.write_frontmatter(self.test_node_id, frontmatter)

        # Verify updated frontmatter includes timestamp
        expected_frontmatter = {'title': 'New', 'updated': '2023-01-01T00:00:00Z'}
        self.mock_frontmatter_codec.update_frontmatter.assert_called_once_with(
            '---\ntitle: Old\n---\nContent', expected_frontmatter
        )
        mock_write_text.assert_called_once_with('---\ntitle: New\n---\nContent', encoding='utf-8')

    @patch('pathlib.Path.exists')
    def test_write_frontmatter_file_not_found(self, mock_exists: Mock) -> None:
        """Test write_frontmatter with missing file."""
        mock_exists.return_value = False

        with pytest.raises(NodeNotFoundError, match='Node file not found'):
            self.repo.write_frontmatter(self.test_node_id, {'title': 'Test'})

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_write_frontmatter_os_error(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test write_frontmatter handles OSError."""
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot write node file'):
            self.repo.write_frontmatter(self.test_node_id, {'title': 'Test'})

    @patch('pathlib.Path.exists')
    def test_open_in_editor_draft_success(self, mock_exists: Mock) -> None:
        """Test successful editor opening for draft."""
        mock_exists.return_value = True

        self.repo.open_in_editor(self.test_node_id, 'draft')

        expected_path = str(self.test_project_path / f'{self.test_node_id}.md')
        self.mock_editor.open.assert_called_once_with(expected_path, cursor_hint=None)

    @patch('pathlib.Path.exists')
    def test_open_in_editor_notes_success(self, mock_exists: Mock) -> None:
        """Test successful editor opening for notes."""
        mock_exists.return_value = True

        self.repo.open_in_editor(self.test_node_id, 'notes')

        expected_path = str(self.test_project_path / f'{self.test_node_id}.notes.md')
        self.mock_editor.open.assert_called_once_with(expected_path, cursor_hint=None)

    @patch('pathlib.Path.exists')
    def test_open_in_editor_synopsis_success(self, mock_exists: Mock) -> None:
        """Test successful editor opening for synopsis."""
        mock_exists.return_value = True

        self.repo.open_in_editor(self.test_node_id, 'synopsis')

        expected_path = str(self.test_project_path / f'{self.test_node_id}.md')
        self.mock_editor.open.assert_called_once_with(expected_path, cursor_hint='1')

    def test_open_in_editor_invalid_part(self) -> None:
        """Test open_in_editor with invalid part."""
        with pytest.raises(InvalidPartError, match='Invalid part: invalid'):
            self.repo.open_in_editor(self.test_node_id, 'invalid')

    @patch('pathlib.Path.exists')
    def test_open_in_editor_file_not_found(self, mock_exists: Mock) -> None:
        """Test open_in_editor with missing file."""
        mock_exists.return_value = False

        with pytest.raises(NodeNotFoundError, match='Node file not found'):
            self.repo.open_in_editor(self.test_node_id, 'draft')

    @patch('pathlib.Path.exists')
    def test_open_in_editor_editor_error(self, mock_exists: Mock) -> None:
        """Test open_in_editor handles editor exceptions."""
        mock_exists.return_value = True
        self.mock_editor.open.side_effect = Exception('Editor failed')

        with pytest.raises(EditorError, match='Failed to open editor'):
            self.repo.open_in_editor(self.test_node_id, 'draft')

    def test_delete_no_delete_files(self) -> None:
        """Test delete with delete_files=False does nothing."""
        self.repo.delete(self.test_node_id, delete_files=False)
        # Should not raise any errors and do nothing

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_success(self, mock_unlink: Mock, mock_exists: Mock) -> None:
        """Test successful file deletion."""
        mock_exists.return_value = True

        self.repo.delete(self.test_node_id, delete_files=True)

        assert mock_unlink.call_count == 2  # Both draft and notes files

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_partial_exists(self, mock_unlink: Mock, mock_exists: Mock) -> None:
        """Test deletion when only some files exist."""
        # First call for draft file returns True, second call for notes file returns False
        mock_exists.side_effect = [True, False]

        self.repo.delete(self.test_node_id, delete_files=True)

        mock_unlink.assert_called_once()  # Only draft file deleted

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_only_notes_exists(self, mock_unlink: Mock, mock_exists: Mock) -> None:
        """Test deletion when only notes file exists."""
        # First call for draft file returns False, second call for notes file returns True
        mock_exists.side_effect = [False, True]

        self.repo.delete(self.test_node_id, delete_files=True)

        mock_unlink.assert_called_once()  # Only notes file deleted

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_files_os_error(self, mock_unlink: Mock, mock_exists: Mock) -> None:
        """Test delete handles OSError."""
        mock_exists.return_value = True
        mock_unlink.side_effect = OSError('Permission denied')

        with pytest.raises(FileSystemError, match='Cannot delete node files'):
            self.repo.delete(self.test_node_id, delete_files=True)

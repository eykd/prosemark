"""Unit tests for FileTemplateRepository adapter.

These tests focus on error paths and edge cases to achieve 100% coverage.
"""

from pathlib import Path

import pytest

from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateDirectoryNotFoundError,
    TemplateNotFoundError,
)


class TestFileTemplateRepositoryInit:
    """Tests for FileTemplateRepository initialization."""

    def test_init_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test initialization with non-existent directory raises error."""
        nonexistent_dir = tmp_path / 'nonexistent'

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            FileTemplateRepository(templates_root=nonexistent_dir)

        error_message = str(exc_info.value)
        assert 'not found' in error_message.lower()
        assert str(nonexistent_dir) in error_message

    def test_init_with_file_instead_of_directory(self, tmp_path: Path) -> None:
        """Test initialization with file path instead of directory raises error."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('not a directory')

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            FileTemplateRepository(templates_root=file_path)

        error_message = str(exc_info.value)
        assert 'not a directory' in error_message.lower()
        assert str(file_path) in error_message


class TestGetTemplate:
    """Tests for get_template method."""

    def test_get_template_os_error_converted_to_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that OSError during template loading is converted to TemplateNotFoundError."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a template file
        template_file = templates_dir / 'test.md'
        template_file.write_text('---\ntitle: Test\n---\n\n# Test')

        repository = FileTemplateRepository(templates_root=templates_dir)

        # Monkeypatch Path.read_text to raise OSError
        from prosemark.templates.domain.values.template_path import TemplatePath

        original_from_file = TemplatePath.__init__

        def mock_init(*args: object, **kwargs: object) -> None:
            raise OSError('Simulated file read error')

        monkeypatch.setattr(TemplatePath, '__init__', mock_init)

        with pytest.raises(TemplateNotFoundError) as exc_info:
            repository.get_template('test')

        error_message = str(exc_info.value)
        assert 'test' in error_message

        # Restore original
        monkeypatch.setattr(TemplatePath, '__init__', original_from_file)


class TestGetTemplateDirectory:
    """Tests for get_template_directory method."""

    def test_get_template_directory_path_is_file(self, tmp_path: Path) -> None:
        """Test get_template_directory when path exists but is a file."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a file with the same name as requested directory
        file_path = templates_dir / 'not-a-dir'
        file_path.write_text('I am a file')

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.get_template_directory('not-a-dir')

        error_message = str(exc_info.value)
        assert 'not a directory' in error_message.lower()

    def test_get_template_directory_load_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_template_directory when TemplateDirectory.from_directory fails."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a directory
        subdir = templates_dir / 'subdir'
        subdir.mkdir()

        # Create a template in it
        (subdir / 'template.md').write_text('---\ntitle: Test\n---\n\n# Test')

        repository = FileTemplateRepository(templates_root=templates_dir)

        # Monkeypatch TemplateDirectory.from_directory to raise exception
        from prosemark.templates.domain.entities.template_directory import TemplateDirectory

        def mock_from_directory(*args: object, **kwargs: object) -> TemplateDirectory:
            raise ValueError('Simulated load error')

        monkeypatch.setattr(TemplateDirectory, 'from_directory', mock_from_directory)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.get_template_directory('subdir')

        error_message = str(exc_info.value)
        assert 'Failed to load' in error_message
        assert 'subdir' in error_message


class TestListTemplates:
    """Tests for list_templates class method."""

    def test_list_templates_search_path_not_directory(self, tmp_path: Path) -> None:
        """Test list_templates when search path is a file, not directory."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('not a directory')

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            FileTemplateRepository.list_templates(file_path)

        error_message = str(exc_info.value)
        assert 'not a directory' in error_message.lower()

    def test_list_templates_skips_invalid_templates(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Test list_templates skips invalid template files and logs warnings."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a valid template
        valid_template = templates_dir / 'valid.md'
        valid_template.write_text('---\ntitle: Valid\n---\n\n# Valid')

        # Create an invalid template (malformed YAML)
        invalid_template = templates_dir / 'invalid.md'
        invalid_template.write_text('---\ntitle: {unclosed\n---\n\n# Invalid')

        # List templates
        templates = FileTemplateRepository.list_templates(templates_dir)

        # Should only return valid template
        assert len(templates) == 1
        assert templates[0].name == 'valid'

        # Should log warning about invalid template
        assert any('Skipping invalid template' in record.message for record in caplog.records)


class TestListTemplateDirectories:
    """Tests for list_template_directories method."""

    def test_list_template_directories_search_path_not_directory(self, tmp_path: Path) -> None:
        """Test list_template_directories when search path is a file."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('not a directory')

        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.list_template_directories(file_path)

        error_message = str(exc_info.value)
        assert 'not a directory' in error_message.lower()

    def test_list_template_directories_skips_invalid_directories(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test list_template_directories skips invalid template directories."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a valid template directory
        valid_dir = templates_dir / 'valid'
        valid_dir.mkdir()
        (valid_dir / 'template.md').write_text('---\ntitle: Valid\n---\n\n# Valid')

        # Create an invalid template directory (with bad template)
        invalid_dir = templates_dir / 'invalid'
        invalid_dir.mkdir()
        (invalid_dir / 'bad.md').write_text('---\ntitle: {unclosed\n---\n\n# Bad')

        repository = FileTemplateRepository(templates_root=templates_dir)

        # List template directories - should skip invalid one
        directories = repository.list_template_directories(templates_dir)

        # Should only return valid directory
        assert len(directories) == 1
        assert directories[0].name == 'valid'

        # Should log warning about invalid directory
        assert any('Skipping invalid template directory' in record.message for record in caplog.records)


class TestListAllTemplateNames:
    """Tests for list_all_template_names method."""

    def test_list_all_template_names_filters_non_files(self, tmp_path: Path) -> None:
        """Test that list_all_template_names only includes files, not directories."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a template file
        (templates_dir / 'template1.md').write_text('---\ntitle: Test\n---\n\n# Test')

        # Create a directory with .md extension (edge case)
        md_dir = templates_dir / 'directory.md'
        md_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)
        names = repository.list_all_template_names()

        # Should only include the file
        assert names == ['template1']


class TestListAllTemplateDirectoryNames:
    """Tests for list_all_template_directory_names method."""

    def test_list_all_template_directory_names_filters_non_template_dirs(self, tmp_path: Path) -> None:
        """Test that list_all_template_directory_names filters directories without templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a directory with templates
        with_templates = templates_dir / 'with-templates'
        with_templates.mkdir()
        (with_templates / 'template.md').write_text('---\ntitle: Test\n---\n\n# Test')

        # Create a directory without templates
        without_templates = templates_dir / 'without-templates'
        without_templates.mkdir()
        (without_templates / 'readme.txt').write_text('Not a template')

        repository = FileTemplateRepository(templates_root=templates_dir)
        names = repository.list_all_template_directory_names()

        # Should only include directory with templates
        assert names == ['with-templates']


class TestFindTemplateByName:
    """Tests for find_template_by_name class method."""

    def test_find_template_by_name_search_path_not_directory(self, tmp_path: Path) -> None:
        """Test find_template_by_name when search path is not a directory."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('not a directory')

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            FileTemplateRepository.find_template_by_name('any', file_path)

        error_message = str(exc_info.value)
        assert 'not a directory' in error_message.lower()

    def test_find_template_by_name_returns_none_for_invalid_template(self, tmp_path: Path) -> None:
        """Test find_template_by_name returns None when template exists but is invalid."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create an invalid template
        invalid_template = templates_dir / 'invalid.md'
        invalid_template.write_text('---\ntitle: {unclosed\n---\n\n# Invalid')

        result = FileTemplateRepository.find_template_by_name('invalid', templates_dir)

        assert result is None


class TestFindTemplateDirectory:
    """Tests for find_template_directory method."""

    def test_find_template_directory_search_path_not_exists(self, tmp_path: Path) -> None:
        """Test find_template_directory when search path doesn't exist."""
        nonexistent = tmp_path / 'nonexistent'

        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.find_template_directory('any', nonexistent)

        error_message = str(exc_info.value)
        assert 'does not exist' in error_message.lower()

    def test_find_template_directory_search_path_not_directory(self, tmp_path: Path) -> None:
        """Test find_template_directory when search path is a file."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('not a directory')

        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.find_template_directory('any', file_path)

        error_message = str(exc_info.value)
        assert 'not a directory' in error_message.lower()

    def test_find_template_directory_returns_none_for_invalid_directory(self, tmp_path: Path) -> None:
        """Test find_template_directory returns None when directory has invalid templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a directory with invalid template (InvalidTemplateDirectoryError)
        invalid_dir = templates_dir / 'invalid'
        invalid_dir.mkdir()
        (invalid_dir / 'bad.md').write_text('---\ntitle: {unclosed\n---\n\n# Bad')

        repository = FileTemplateRepository(templates_root=templates_dir)

        # Should return None when directory contains invalid templates
        result = repository.find_template_directory('invalid', templates_dir)

        assert result is None


class TestLoadTemplateContent:
    """Tests for load_template_content class method."""

    def test_load_template_content_file_not_exists(self, tmp_path: Path) -> None:
        """Test load_template_content raises error when file doesn't exist."""
        nonexistent_file = tmp_path / 'nonexistent.md'

        with pytest.raises(TemplateNotFoundError) as exc_info:
            FileTemplateRepository.load_template_content(nonexistent_file)

        error_message = str(exc_info.value)
        assert 'nonexistent' in error_message


class TestValidateTemplatePath:
    """Tests for validate_template_path class method."""

    def test_validate_template_path_directory(self, tmp_path: Path) -> None:
        """Test validate_template_path returns False for directory."""
        directory = tmp_path / 'directory'
        directory.mkdir()

        result = FileTemplateRepository.validate_template_path(directory)

        assert result is False

    def test_validate_template_path_wrong_extension(self, tmp_path: Path) -> None:
        """Test validate_template_path returns False for non-.md file."""
        txt_file = tmp_path / 'file.txt'
        txt_file.write_text('not markdown')

        result = FileTemplateRepository.validate_template_path(txt_file)

        assert result is False


class TestTemplateExists:
    """Tests for template_exists method."""

    def test_template_exists_is_directory(self, tmp_path: Path) -> None:
        """Test template_exists returns False when path is directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a directory with same name as template
        dir_path = templates_dir / 'template.md'
        dir_path.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        result = repository.template_exists('template')

        assert result is False


class TestTemplateDirectoryExists:
    """Tests for template_directory_exists method."""

    def test_template_directory_exists_is_file(self, tmp_path: Path) -> None:
        """Test template_directory_exists returns False when path is file."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a file with directory name
        file_path = templates_dir / 'directory'
        file_path.write_text('not a directory')

        repository = FileTemplateRepository(templates_root=templates_dir)

        result = repository.template_directory_exists('directory')

        assert result is False

    def test_template_directory_exists_no_templates(self, tmp_path: Path) -> None:
        """Test template_directory_exists returns False for empty directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create empty directory
        empty_dir = templates_dir / 'empty'
        empty_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        result = repository.template_directory_exists('empty')

        assert result is False


class TestGetTemplateInfo:
    """Tests for get_template_info method."""

    def test_get_template_info_nonexistent(self, tmp_path: Path) -> None:
        """Test get_template_info raises error for nonexistent template."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateNotFoundError) as exc_info:
            repository.get_template_info('nonexistent')

        error_message = str(exc_info.value)
        assert 'nonexistent' in error_message


class TestGetTemplateDirectoryInfo:
    """Tests for get_template_directory_info method."""

    def test_get_template_directory_info_nonexistent(self, tmp_path: Path) -> None:
        """Test get_template_directory_info raises error for nonexistent directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.get_template_directory_info('nonexistent')

        error_message = str(exc_info.value)
        assert 'nonexistent' in error_message

    def test_get_template_directory_info_is_file(self, tmp_path: Path) -> None:
        """Test get_template_directory_info raises error when path is file."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a file with directory name
        file_path = templates_dir / 'file-not-dir'
        file_path.write_text('not a directory')

        repository = FileTemplateRepository(templates_root=templates_dir)

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            repository.get_template_directory_info('file-not-dir')

        error_message = str(exc_info.value)
        assert 'file-not-dir' in error_message

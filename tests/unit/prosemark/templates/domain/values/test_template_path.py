"""Unit tests for TemplatePath value object."""

from pathlib import Path

import pytest

from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.template_path import TemplatePath


class TestTemplatePathInitialization:
    """Tests for TemplatePath initialization and validation."""

    def test_init_with_valid_path_object(self, tmp_path: Path) -> None:
        """Test initialization with a valid Path object."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.value == template_file.resolve()

    def test_init_with_valid_string_path(self, tmp_path: Path) -> None:
        """Test initialization with a valid string path."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(str(template_file))
        assert template_path.value == template_file.resolve()

    def test_init_resolves_relative_paths(self, tmp_path: Path) -> None:
        """Test that initialization resolves relative paths to absolute."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        import os

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            template_path = TemplatePath('template.md')
            assert template_path.value == template_file.resolve()
            assert template_path.value.is_absolute()
        finally:
            os.chdir(original_cwd)

    def test_init_raises_error_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that initialization raises error for non-existent file."""
        nonexistent = tmp_path / 'does_not_exist.md'

        with pytest.raises(TemplateNotFoundError) as exc_info:
            TemplatePath(nonexistent)

        assert 'does_not_exist.md' in str(exc_info.value)

    def test_init_raises_error_for_directory_path(self, tmp_path: Path) -> None:
        """Test that initialization raises error when path points to a directory."""
        directory = tmp_path / 'directory'
        directory.mkdir()

        with pytest.raises(TemplateValidationError) as exc_info:
            TemplatePath(directory)

        assert 'must point to a file' in str(exc_info.value)
        assert 'not a directory' in str(exc_info.value)

    def test_init_raises_error_for_non_md_extension(self, tmp_path: Path) -> None:
        """Test that initialization raises error for non-.md files."""
        text_file = tmp_path / 'file.txt'
        text_file.write_text('Not a markdown file')

        with pytest.raises(TemplateValidationError) as exc_info:
            TemplatePath(text_file)

        assert 'must have .md extension' in str(exc_info.value)


class TestTemplatePathProperties:
    """Tests for TemplatePath properties."""

    def test_value_property_returns_path(self, tmp_path: Path) -> None:
        """Test that value property returns the Path object."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.value == template_file.resolve()
        assert isinstance(template_path.value, Path)

    def test_name_property_returns_filename_without_extension(self, tmp_path: Path) -> None:
        """Test that name property returns filename without .md extension."""
        template_file = tmp_path / 'my_template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.name == 'my_template'

    def test_exists_property_returns_true_for_existing_file(self, tmp_path: Path) -> None:
        """Test that exists returns True for existing file."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.exists is True

    def test_exists_property_returns_false_for_deleted_file(self, tmp_path: Path) -> None:
        """Test that exists returns False after file is deleted."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.exists is True

        # Delete the file
        template_file.unlink()
        assert template_path.exists is False

    def test_is_readable_property_returns_true_for_readable_file(self, tmp_path: Path) -> None:
        """Test that is_readable returns True for readable file."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.is_readable is True

    def test_parent_directory_property_returns_parent(self, tmp_path: Path) -> None:
        """Test that parent_directory returns the parent directory."""
        subdir = tmp_path / 'templates'
        subdir.mkdir()
        template_file = subdir / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert template_path.parent_directory == subdir.resolve()


class TestTemplatePathMethods:
    """Tests for TemplatePath methods."""

    def test_read_content_returns_file_content(self, tmp_path: Path) -> None:
        """Test reading template file content."""
        content = '# My Template\n\nTemplate content here.'
        template_file = tmp_path / 'template.md'
        template_file.write_text(content, encoding='utf-8')

        template_path = TemplatePath(template_file)
        assert template_path.read_content() == content

    def test_read_content_handles_unicode(self, tmp_path: Path) -> None:
        """Test reading template file with unicode content."""
        content = '# Template with Unicode: éèê 中文 🚀'
        template_file = tmp_path / 'template.md'
        template_file.write_text(content, encoding='utf-8')

        template_path = TemplatePath(template_file)
        assert template_path.read_content() == content

    def test_read_content_raises_error_for_deleted_file(self, tmp_path: Path) -> None:
        """Test that read_content raises error for deleted file."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)

        # Delete the file
        template_file.unlink()

        with pytest.raises(TemplateNotFoundError):
            template_path.read_content()

    def test_get_relative_path_for_contained_path(self, tmp_path: Path) -> None:
        """Test getting relative path when template is within base directory."""
        subdir = tmp_path / 'templates'
        subdir.mkdir()
        template_file = subdir / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        relative = template_path.get_relative_path(tmp_path)

        assert relative == Path('templates/template.md')

    def test_get_relative_path_returns_absolute_for_unrelated_path(self, tmp_path: Path) -> None:
        """Test that get_relative_path returns absolute path for unrelated directories."""
        other_dir = tmp_path.parent / 'other_dir'
        other_dir.mkdir()
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        try:
            template_path = TemplatePath(template_file)
            relative = template_path.get_relative_path(other_dir)

            # Should return the absolute path since it's not relative
            assert relative == template_path.value
        finally:
            # Cleanup
            other_dir.rmdir()


class TestTemplatePathClassMethods:
    """Tests for TemplatePath class methods."""

    def test_from_name_and_directory_without_md_extension(self, tmp_path: Path) -> None:
        """Test creating TemplatePath from name and directory without .md extension."""
        template_file = tmp_path / 'my_template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath.from_name_and_directory('my_template', tmp_path)

        assert template_path.value == template_file.resolve()
        assert template_path.name == 'my_template'

    def test_from_name_and_directory_with_md_extension(self, tmp_path: Path) -> None:
        """Test creating TemplatePath from name and directory with .md extension."""
        template_file = tmp_path / 'my_template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath.from_name_and_directory('my_template.md', tmp_path)

        assert template_path.value == template_file.resolve()
        assert template_path.name == 'my_template'

    def test_from_name_and_directory_raises_error_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that from_name_and_directory raises error for non-existent file."""
        with pytest.raises(TemplateNotFoundError):
            TemplatePath.from_name_and_directory('nonexistent', tmp_path)


class TestTemplatePathDunderMethods:
    """Tests for TemplatePath special methods."""

    def test_str_returns_path_string(self, tmp_path: Path) -> None:
        """Test that __str__ returns the path as a string."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        assert str(template_path) == str(template_file.resolve())

    def test_repr_returns_developer_representation(self, tmp_path: Path) -> None:
        """Test that __repr__ returns developer representation."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)
        repr_str = repr(template_path)

        assert 'TemplatePath' in repr_str
        assert str(template_file.resolve()) in repr_str

    def test_eq_returns_true_for_same_path(self, tmp_path: Path) -> None:
        """Test equality for same path."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path1 = TemplatePath(template_file)
        template_path2 = TemplatePath(template_file)

        assert template_path1 == template_path2

    def test_eq_returns_false_for_different_paths(self, tmp_path: Path) -> None:
        """Test inequality for different paths."""
        template_file1 = tmp_path / 'template1.md'
        template_file1.write_text('# Template 1')
        template_file2 = tmp_path / 'template2.md'
        template_file2.write_text('# Template 2')

        template_path1 = TemplatePath(template_file1)
        template_path2 = TemplatePath(template_file2)

        assert template_path1 != template_path2

    def test_eq_returns_not_implemented_for_non_template_path(self, tmp_path: Path) -> None:
        """Test that equality with non-TemplatePath returns NotImplemented."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path = TemplatePath(template_file)

        result = template_path.__eq__('not a TemplatePath')
        assert result is NotImplemented

    def test_hash_is_consistent(self, tmp_path: Path) -> None:
        """Test that hash is consistent for same path."""
        template_file = tmp_path / 'template.md'
        template_file.write_text('# Template')

        template_path1 = TemplatePath(template_file)
        template_path2 = TemplatePath(template_file)

        assert hash(template_path1) == hash(template_path2)

    def test_hash_allows_use_in_set(self, tmp_path: Path) -> None:
        """Test that TemplatePath can be used in a set."""
        template_file1 = tmp_path / 'template1.md'
        template_file1.write_text('# Template 1')
        template_file2 = tmp_path / 'template2.md'
        template_file2.write_text('# Template 2')

        template_path1 = TemplatePath(template_file1)
        template_path2 = TemplatePath(template_file2)
        template_path3 = TemplatePath(template_file1)  # Same as template_path1

        path_set = {template_path1, template_path2, template_path3}
        assert len(path_set) == 2  # template_path1 and template_path3 are duplicates

"""Unit tests for DirectoryPath value object."""

from pathlib import Path

import pytest

from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateDirectoryNotFoundError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.directory_path import DirectoryPath


class TestDirectoryPathInitialization:
    """Tests for DirectoryPath initialization and validation."""

    def test_init_with_valid_path_object(self, tmp_path: Path) -> None:
        """Test initialization with a valid Path object."""
        dir_path = DirectoryPath(tmp_path)
        assert dir_path.value == tmp_path.resolve()

    def test_init_with_valid_string_path(self, tmp_path: Path) -> None:
        """Test initialization with a valid string path."""
        dir_path = DirectoryPath(str(tmp_path))
        assert dir_path.value == tmp_path.resolve()

    def test_init_resolves_relative_paths(self, tmp_path: Path) -> None:
        """Test that initialization resolves relative paths to absolute."""
        # Create a subdirectory
        subdir = tmp_path / 'subdir'
        subdir.mkdir()

        # Change to tmp_path and create DirectoryPath with relative path
        import os

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            dir_path = DirectoryPath('subdir')
            assert dir_path.value == subdir.resolve()
            assert dir_path.value.is_absolute()
        finally:
            os.chdir(original_cwd)

    def test_init_raises_error_for_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test that initialization raises error for non-existent directory."""
        nonexistent = tmp_path / 'does_not_exist'

        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            DirectoryPath(nonexistent)

        assert str(nonexistent) in str(exc_info.value)

    def test_init_raises_error_for_file_path(self, tmp_path: Path) -> None:
        """Test that initialization raises error when path points to a file."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('content')

        with pytest.raises(TemplateValidationError) as exc_info:
            DirectoryPath(file_path)

        assert 'must point to a directory' in str(exc_info.value)
        assert 'not a file' in str(exc_info.value)


class TestDirectoryPathProperties:
    """Tests for DirectoryPath properties."""

    def test_value_property_returns_path(self, tmp_path: Path) -> None:
        """Test that value property returns the Path object."""
        dir_path = DirectoryPath(tmp_path)
        assert dir_path.value == tmp_path.resolve()
        assert isinstance(dir_path.value, Path)

    def test_name_property_returns_directory_name(self, tmp_path: Path) -> None:
        """Test that name property returns the directory name."""
        subdir = tmp_path / 'my_directory'
        subdir.mkdir()

        dir_path = DirectoryPath(subdir)
        assert dir_path.name == 'my_directory'

    def test_exists_property_returns_true_for_existing_directory(self, tmp_path: Path) -> None:
        """Test that exists returns True for existing directory."""
        dir_path = DirectoryPath(tmp_path)
        assert dir_path.exists is True

    def test_exists_property_returns_false_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that exists returns False after directory is deleted."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()

        dir_path = DirectoryPath(subdir)
        assert dir_path.exists is True

        # Delete the directory
        subdir.rmdir()
        assert dir_path.exists is False

    def test_template_count_returns_zero_for_empty_directory(self, tmp_path: Path) -> None:
        """Test that template_count returns 0 for empty directory."""
        dir_path = DirectoryPath(tmp_path)
        assert dir_path.template_count == 0

    def test_template_count_counts_md_files_only(self, tmp_path: Path) -> None:
        """Test that template_count counts only .md files."""
        # Create various files
        (tmp_path / 'template1.md').write_text('# Template 1')
        (tmp_path / 'template2.md').write_text('# Template 2')
        (tmp_path / 'readme.txt').write_text('Not a template')
        (tmp_path / 'data.json').write_text('{}')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.template_count == 2

    def test_template_count_ignores_subdirectories(self, tmp_path: Path) -> None:
        """Test that template_count doesn't count files in subdirectories."""
        # Create files in root
        (tmp_path / 'root.md').write_text('# Root')

        # Create files in subdirectory
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        (subdir / 'sub.md').write_text('# Sub')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.template_count == 1  # Only root.md

    def test_template_count_returns_zero_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that template_count returns 0 for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()
        (subdir / 'template.md').write_text('# Template')

        dir_path = DirectoryPath(subdir)
        assert dir_path.template_count == 1

        # Delete the directory
        (subdir / 'template.md').unlink()
        subdir.rmdir()
        assert dir_path.template_count == 0

    def test_total_template_count_includes_subdirectories(self, tmp_path: Path) -> None:
        """Test that total_template_count counts .md files recursively."""
        # Create files in root
        (tmp_path / 'root1.md').write_text('# Root 1')
        (tmp_path / 'root2.md').write_text('# Root 2')

        # Create files in subdirectory
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        (subdir / 'sub1.md').write_text('# Sub 1')
        (subdir / 'sub2.md').write_text('# Sub 2')

        # Create files in nested subdirectory
        nested = subdir / 'nested'
        nested.mkdir()
        (nested / 'nested.md').write_text('# Nested')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.total_template_count == 5

    def test_total_template_count_returns_zero_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that total_template_count returns 0 for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()
        (subdir / 'template.md').write_text('# Template')

        dir_path = DirectoryPath(subdir)
        assert dir_path.total_template_count == 1

        # Delete the directory
        (subdir / 'template.md').unlink()
        subdir.rmdir()
        assert dir_path.total_template_count == 0

    def test_subdirectory_count_returns_zero_for_no_subdirectories(self, tmp_path: Path) -> None:
        """Test that subdirectory_count returns 0 when no subdirectories exist."""
        (tmp_path / 'file.md').write_text('# File')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.subdirectory_count == 0

    def test_subdirectory_count_counts_only_directories(self, tmp_path: Path) -> None:
        """Test that subdirectory_count counts only directories."""
        # Create files
        (tmp_path / 'file1.md').write_text('# File 1')
        (tmp_path / 'file2.txt').write_text('Text')

        # Create subdirectories
        (tmp_path / 'dir1').mkdir()
        (tmp_path / 'dir2').mkdir()
        (tmp_path / 'dir3').mkdir()

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.subdirectory_count == 3

    def test_subdirectory_count_returns_zero_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that subdirectory_count returns 0 for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()
        (subdir / 'nested').mkdir()

        dir_path = DirectoryPath(subdir)
        assert dir_path.subdirectory_count == 1

        # Delete the directory
        (subdir / 'nested').rmdir()
        subdir.rmdir()
        assert dir_path.subdirectory_count == 0

    def test_is_valid_template_directory_with_md_files(self, tmp_path: Path) -> None:
        """Test that directory with .md files is valid."""
        (tmp_path / 'template.md').write_text('# Template')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.is_valid_template_directory is True

    def test_is_valid_template_directory_with_subdirectory_md_files(self, tmp_path: Path) -> None:
        """Test that directory with .md files in subdirectories is valid."""
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        (subdir / 'template.md').write_text('# Template')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.is_valid_template_directory is True

    def test_is_valid_template_directory_returns_false_for_empty_directory(self, tmp_path: Path) -> None:
        """Test that empty directory is not valid."""
        dir_path = DirectoryPath(tmp_path)
        assert dir_path.is_valid_template_directory is False

    def test_is_valid_template_directory_returns_false_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that deleted directory is not valid."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()
        (subdir / 'template.md').write_text('# Template')

        dir_path = DirectoryPath(subdir)
        assert dir_path.is_valid_template_directory is True

        # Delete the directory
        (subdir / 'template.md').unlink()
        subdir.rmdir()
        assert dir_path.is_valid_template_directory is False


class TestDirectoryPathMethods:
    """Tests for DirectoryPath methods."""

    def test_list_template_files_non_recursive(self, tmp_path: Path) -> None:
        """Test listing template files non-recursively."""
        # Create files in root
        (tmp_path / 'b.md').write_text('# B')
        (tmp_path / 'a.md').write_text('# A')
        (tmp_path / 'not_template.txt').write_text('Text')

        # Create files in subdirectory (should be ignored)
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        (subdir / 'sub.md').write_text('# Sub')

        dir_path = DirectoryPath(tmp_path)
        files = dir_path.list_template_files(recursive=False)

        assert len(files) == 2
        assert files[0].name == 'a.md'  # Sorted
        assert files[1].name == 'b.md'

    def test_list_template_files_recursive(self, tmp_path: Path) -> None:
        """Test listing template files recursively."""
        # Create files in root
        (tmp_path / 'root.md').write_text('# Root')

        # Create files in subdirectory
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        (subdir / 'sub.md').write_text('# Sub')

        # Create files in nested subdirectory
        nested = subdir / 'nested'
        nested.mkdir()
        (nested / 'nested.md').write_text('# Nested')

        dir_path = DirectoryPath(tmp_path)
        files = dir_path.list_template_files(recursive=True)

        assert len(files) == 3
        # Verify all files are found
        file_names = {f.name for f in files}
        assert file_names == {'root.md', 'sub.md', 'nested.md'}

    def test_list_template_files_raises_error_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that list_template_files raises error for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()

        dir_path = DirectoryPath(subdir)

        # Delete the directory
        subdir.rmdir()

        with pytest.raises(TemplateDirectoryNotFoundError):
            dir_path.list_template_files()

    def test_list_subdirectories_returns_sorted_list(self, tmp_path: Path) -> None:
        """Test listing subdirectories returns sorted list."""
        # Create subdirectories out of order
        (tmp_path / 'c').mkdir()
        (tmp_path / 'a').mkdir()
        (tmp_path / 'b').mkdir()

        # Create a file (should be ignored)
        (tmp_path / 'file.md').write_text('# File')

        dir_path = DirectoryPath(tmp_path)
        subdirs = dir_path.list_subdirectories()

        assert len(subdirs) == 3
        assert subdirs[0].name == 'a'
        assert subdirs[1].name == 'b'
        assert subdirs[2].name == 'c'

    def test_list_subdirectories_raises_error_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that list_subdirectories raises error for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()

        dir_path = DirectoryPath(subdir)

        # Delete the directory
        subdir.rmdir()

        with pytest.raises(TemplateDirectoryNotFoundError):
            dir_path.list_subdirectories()

    def test_find_template_file_finds_existing_file(self, tmp_path: Path) -> None:
        """Test finding an existing template file."""
        template_path = tmp_path / 'my_template.md'
        template_path.write_text('# Template')

        dir_path = DirectoryPath(tmp_path)
        found = dir_path.find_template_file('my_template')

        assert found == template_path

    def test_find_template_file_finds_file_with_md_extension(self, tmp_path: Path) -> None:
        """Test finding template file when .md extension is provided."""
        template_path = tmp_path / 'my_template.md'
        template_path.write_text('# Template')

        dir_path = DirectoryPath(tmp_path)
        found = dir_path.find_template_file('my_template.md')

        assert found == template_path

    def test_find_template_file_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that find_template_file returns None for non-existent file."""
        dir_path = DirectoryPath(tmp_path)
        found = dir_path.find_template_file('nonexistent')

        assert found is None

    def test_find_template_file_returns_none_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that find_template_file returns None for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()

        dir_path = DirectoryPath(subdir)

        # Delete the directory
        subdir.rmdir()

        found = dir_path.find_template_file('template')
        assert found is None

    def test_find_subdirectory_finds_existing_subdirectory(self, tmp_path: Path) -> None:
        """Test finding an existing subdirectory."""
        subdir = tmp_path / 'my_subdir'
        subdir.mkdir()

        dir_path = DirectoryPath(tmp_path)
        found = dir_path.find_subdirectory('my_subdir')

        assert found == subdir

    def test_find_subdirectory_returns_none_for_nonexistent_subdirectory(self, tmp_path: Path) -> None:
        """Test that find_subdirectory returns None for non-existent subdirectory."""
        dir_path = DirectoryPath(tmp_path)
        found = dir_path.find_subdirectory('nonexistent')

        assert found is None

    def test_find_subdirectory_returns_none_for_deleted_directory(self, tmp_path: Path) -> None:
        """Test that find_subdirectory returns None for deleted directory."""
        subdir = tmp_path / 'temp_dir'
        subdir.mkdir()

        dir_path = DirectoryPath(subdir)

        # Delete the directory
        subdir.rmdir()

        found = dir_path.find_subdirectory('subdir')
        assert found is None

    def test_get_relative_path_to_for_contained_path(self, tmp_path: Path) -> None:
        """Test getting relative path to a contained path."""
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        file_path = subdir / 'file.md'
        file_path.write_text('# File')

        dir_path = DirectoryPath(tmp_path)
        relative = dir_path.get_relative_path_to(file_path)

        assert relative == Path('subdir/file.md')

    def test_get_relative_path_to_returns_none_for_unrelated_path(self, tmp_path: Path) -> None:
        """Test that get_relative_path_to returns None for unrelated path."""
        other_dir = tmp_path.parent / 'other_dir'
        other_dir.mkdir()
        other_file = other_dir / 'file.md'
        other_file.write_text('# File')

        try:
            dir_path = DirectoryPath(tmp_path)
            relative = dir_path.get_relative_path_to(other_file)

            assert relative is None
        finally:
            # Cleanup
            other_file.unlink()
            other_dir.rmdir()

    def test_contains_path_returns_true_for_contained_path(self, tmp_path: Path) -> None:
        """Test that contains_path returns True for contained path."""
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        file_path = subdir / 'file.md'
        file_path.write_text('# File')

        dir_path = DirectoryPath(tmp_path)
        assert dir_path.contains_path(file_path) is True

    def test_contains_path_returns_false_for_unrelated_path(self, tmp_path: Path) -> None:
        """Test that contains_path returns False for unrelated path."""
        other_dir = tmp_path.parent / 'other_dir'
        other_dir.mkdir()
        other_file = other_dir / 'file.md'
        other_file.write_text('# File')

        try:
            dir_path = DirectoryPath(tmp_path)
            assert dir_path.contains_path(other_file) is False
        finally:
            # Cleanup
            other_file.unlink()
            other_dir.rmdir()


class TestDirectoryPathClassMethods:
    """Tests for DirectoryPath class methods."""

    def test_create_if_not_exists_creates_new_directory(self, tmp_path: Path) -> None:
        """Test that create_if_not_exists creates a new directory."""
        new_dir = tmp_path / 'new_dir'
        assert not new_dir.exists()

        dir_path = DirectoryPath.create_if_not_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert dir_path.value == new_dir.resolve()

    def test_create_if_not_exists_with_string_path(self, tmp_path: Path) -> None:
        """Test create_if_not_exists with string path."""
        new_dir = tmp_path / 'new_dir'

        dir_path = DirectoryPath.create_if_not_exists(str(new_dir))

        assert new_dir.exists()
        assert dir_path.value == new_dir.resolve()

    def test_create_if_not_exists_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test that create_if_not_exists creates parent directories."""
        nested_dir = tmp_path / 'parent' / 'child' / 'grandchild'
        assert not nested_dir.exists()

        dir_path = DirectoryPath.create_if_not_exists(nested_dir)

        assert nested_dir.exists()
        assert dir_path.value == nested_dir.resolve()

    def test_create_if_not_exists_returns_existing_directory(self, tmp_path: Path) -> None:
        """Test that create_if_not_exists works with existing directory."""
        existing_dir = tmp_path / 'existing'
        existing_dir.mkdir()

        dir_path = DirectoryPath.create_if_not_exists(existing_dir)

        assert dir_path.value == existing_dir.resolve()

    def test_create_if_not_exists_raises_error_for_existing_file(self, tmp_path: Path) -> None:
        """Test that create_if_not_exists raises error when path is a file."""
        file_path = tmp_path / 'file.txt'
        file_path.write_text('content')

        with pytest.raises(TemplateValidationError) as exc_info:
            DirectoryPath.create_if_not_exists(file_path)

        assert 'exists but is not a directory' in str(exc_info.value)


class TestDirectoryPathDunderMethods:
    """Tests for DirectoryPath special methods."""

    def test_str_returns_path_string(self, tmp_path: Path) -> None:
        """Test that __str__ returns the path as a string."""
        dir_path = DirectoryPath(tmp_path)
        assert str(dir_path) == str(tmp_path.resolve())

    def test_repr_returns_developer_representation(self, tmp_path: Path) -> None:
        """Test that __repr__ returns developer representation."""
        dir_path = DirectoryPath(tmp_path)
        repr_str = repr(dir_path)

        assert 'DirectoryPath' in repr_str
        assert str(tmp_path.resolve()) in repr_str

    def test_eq_returns_true_for_same_path(self, tmp_path: Path) -> None:
        """Test equality for same path."""
        dir_path1 = DirectoryPath(tmp_path)
        dir_path2 = DirectoryPath(tmp_path)

        assert dir_path1 == dir_path2

    def test_eq_returns_false_for_different_paths(self, tmp_path: Path) -> None:
        """Test inequality for different paths."""
        subdir1 = tmp_path / 'dir1'
        subdir1.mkdir()
        subdir2 = tmp_path / 'dir2'
        subdir2.mkdir()

        dir_path1 = DirectoryPath(subdir1)
        dir_path2 = DirectoryPath(subdir2)

        assert dir_path1 != dir_path2

    def test_eq_returns_not_implemented_for_non_directory_path(self, tmp_path: Path) -> None:
        """Test that equality with non-DirectoryPath returns NotImplemented."""
        dir_path = DirectoryPath(tmp_path)

        result = dir_path.__eq__('not a DirectoryPath')
        assert result is NotImplemented

    def test_hash_is_consistent(self, tmp_path: Path) -> None:
        """Test that hash is consistent for same path."""
        dir_path1 = DirectoryPath(tmp_path)
        dir_path2 = DirectoryPath(tmp_path)

        assert hash(dir_path1) == hash(dir_path2)

    def test_hash_allows_use_in_set(self, tmp_path: Path) -> None:
        """Test that DirectoryPath can be used in a set."""
        subdir1 = tmp_path / 'dir1'
        subdir1.mkdir()
        subdir2 = tmp_path / 'dir2'
        subdir2.mkdir()

        dir_path1 = DirectoryPath(subdir1)
        dir_path2 = DirectoryPath(subdir2)
        dir_path3 = DirectoryPath(subdir1)  # Same as dir_path1

        path_set = {dir_path1, dir_path2, dir_path3}
        assert len(path_set) == 2  # dir_path1 and dir_path3 are duplicates

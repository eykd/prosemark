"""Unit tests for TemplateDirectory entity."""

from pathlib import Path
from unittest.mock import patch

import pytest

from prosemark.templates.domain.entities.placeholder import Placeholder
from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import (
    EmptyTemplateDirectoryError,
    InvalidPlaceholderValueError,
    InvalidTemplateDirectoryError,
    TemplateValidationError,
)
from prosemark.templates.domain.values.directory_path import DirectoryPath


class TestTemplateDirectoryInitialization:
    """Tests for TemplateDirectory initialization and validation."""

    def test_init_with_empty_templates_loads_from_path(self, tmp_path: Path) -> None:
        """Test that empty templates list triggers loading from path."""
        # Create directory with templates
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        # Create with empty templates - should trigger loading
        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
            templates=[],  # Empty list triggers _load_templates
        )

        # Should have loaded templates
        assert len(template_directory.templates) > 0
        assert template_directory.templates[0].name == 'test'

    def test_init_validates_empty_templates(self, tmp_path: Path) -> None:
        """Test that validation fails when no templates are loaded."""
        template_dir = tmp_path / 'empty-template'
        template_dir.mkdir()

        directory_path = DirectoryPath(template_dir)

        # Should raise EmptyTemplateDirectoryError during _validate
        with pytest.raises(EmptyTemplateDirectoryError) as exc_info:
            TemplateDirectory(
                name='empty-template',
                path=directory_path,
                templates=[],
            )

        assert 'empty-template' in str(exc_info.value)

    def test_init_with_structure_skips_rebuild(self, tmp_path: Path) -> None:
        """Test that providing structure skips _build_structure."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        # Load templates first
        template = Template.from_file(template_file)

        # Provide pre-built structure
        existing_structure = {
            'name': 'test-template',
            'path': str(template_dir),
            'template_count': 1,
            'templates': [],
            'subdirectories': {},
        }

        # Create with existing structure
        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
            templates=[template],
            structure=existing_structure,
        )

        # Should use provided structure
        assert template_directory.structure == existing_structure


class TestTemplateDirectoryLoading:
    """Tests for template loading from directory."""

    def test_load_templates_with_invalid_templates(self, tmp_path: Path) -> None:
        """Test that invalid templates are reported properly."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Create valid template
        valid_template = template_dir / 'valid.md'
        valid_template.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        # Create invalid template with bad YAML
        invalid_template = template_dir / 'invalid.md'
        invalid_template.write_text(
            '---\n'
            'title: {{title\n'  # Invalid YAML - missing closing brace
            '---\n\n'
            '# Content\n'
        )

        directory_path = DirectoryPath(template_dir)

        # Should raise InvalidTemplateDirectoryError with details
        with pytest.raises(InvalidTemplateDirectoryError) as exc_info:
            TemplateDirectory(
                name='test-template',
                path=directory_path,
            )

        error_message = str(exc_info.value)
        assert 'invalid.md' in error_message

    def test_load_templates_marks_as_directory_template(self, tmp_path: Path) -> None:
        """Test that loaded templates are marked as directory templates."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Templates should be marked as directory templates
        assert len(template_directory.templates) > 0
        assert template_directory.templates[0].is_directory_template is True


class TestTemplateDirectoryValidation:
    """Tests for template directory validation."""

    def test_validate_nonexistent_template_file(self, tmp_path: Path) -> None:
        """Test validation fails for nonexistent template files."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        # Load template
        template = Template.from_file(template_file)

        # Delete the file after loading
        template_file.unlink()

        # Should raise TemplateValidationError
        with pytest.raises(TemplateValidationError) as exc_info:
            TemplateDirectory(
                name='test-template',
                path=directory_path,
                templates=[template],
            )

        assert 'no longer exists' in str(exc_info.value)

    def test_validate_placeholder_consistency_required_mismatch(self, tmp_path: Path) -> None:
        """Test validation fails when shared placeholder has inconsistent required status."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Template 1: title is required (no default)
        template1 = template_dir / 'template1.md'
        template1.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        # Template 2: title is optional (has default)
        template2 = template_dir / 'template2.md'
        template2.write_text('---\ntitle: "{{title}}"\ntitle_default: "Default Title"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        # Should raise TemplateValidationError about inconsistent required status
        with pytest.raises(TemplateValidationError) as exc_info:
            TemplateDirectory(
                name='test-template',
                path=directory_path,
            )

        assert 'inconsistent required status' in str(exc_info.value)

    def test_validate_placeholder_consistency_default_value_mismatch(self, tmp_path: Path) -> None:
        """Test validation fails when shared placeholder has inconsistent default values."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Template 1: title with default "Default 1"
        template1 = template_dir / 'template1.md'
        template1.write_text('---\ntitle: "{{title}}"\ntitle_default: "Default 1"\n---\n\n# {{title}}\n')

        # Template 2: title with different default "Default 2"
        template2 = template_dir / 'template2.md'
        template2.write_text('---\ntitle: "{{title}}"\ntitle_default: "Default 2"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        # Should raise TemplateValidationError about inconsistent defaults
        with pytest.raises(TemplateValidationError) as exc_info:
            TemplateDirectory(
                name='test-template',
                path=directory_path,
            )

        assert 'inconsistent default values' in str(exc_info.value)


class TestTemplateDirectoryStructure:
    """Tests for directory structure building."""

    def test_build_structure_with_subdirectories(self, tmp_path: Path) -> None:
        """Test structure building with nested subdirectories."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Create nested subdirectories
        subdir1 = template_dir / 'level1'
        subdir1.mkdir()

        subdir2 = subdir1 / 'level2'
        subdir2.mkdir()

        # Create templates at different levels
        root_template = template_dir / 'root.md'
        root_template.write_text('---\ntitle: "{{title}}"\n---\n\n# Root\n')

        level1_template = subdir1 / 'level1.md'
        level1_template.write_text('---\ntitle: "{{title}}"\n---\n\n# Level 1\n')

        level2_template = subdir2 / 'level2.md'
        level2_template.write_text('---\ntitle: "{{title}}"\n---\n\n# Level 2\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Check structure contains subdirectories
        structure = template_directory.structure
        assert 'subdirectories' in structure
        assert 'level1' in structure['subdirectories']

        # Check nested level
        level1_struct = structure['subdirectories']['level1']
        assert 'subdirectories' in level1_struct
        assert 'level2' in level1_struct['subdirectories']

    def test_build_structure_initializes_templates_list(self, tmp_path: Path) -> None:
        """Test structure building initializes templates list when missing."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Create subdirectory
        subdir = template_dir / 'subdir'
        subdir.mkdir()

        # Create template in subdirectory
        sub_template = subdir / 'sub.md'
        sub_template.write_text('---\ntitle: "{{title}}"\n---\n\n# Sub\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Check that structure includes template in subdirectory
        structure = template_directory.structure
        assert 'subdir' in structure['subdirectories']
        subdir_struct = structure['subdirectories']['subdir']

        # Should have initialized templates list
        assert 'templates' in subdir_struct
        assert len(subdir_struct['templates']) > 0

    def test_build_structure_handles_missing_templates_list(self, tmp_path: Path) -> None:
        """Test structure building when templates list is not initialized."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)
        template = Template.from_file(template_file)

        # Mock get_relative_path_to to return None (no relative path)
        with patch.object(DirectoryPath, 'get_relative_path_to', return_value=None):
            template_directory = TemplateDirectory(
                name='test-template',
                path=directory_path,
                templates=[template],
            )

            # Structure should still be built with empty templates
            assert template_directory.structure['template_count'] == 1


class TestTemplateDirectoryProperties:
    """Tests for TemplateDirectory properties."""

    def test_directory_name_property(self, tmp_path: Path) -> None:
        """Test directory_name property returns name."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# Test\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        assert template_directory.directory_name == 'test-template'

    def test_directory_path_property(self, tmp_path: Path) -> None:
        """Test directory_path property returns Path."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# Test\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        assert template_directory.directory_path == template_dir

    def test_shared_placeholders_property(self, tmp_path: Path) -> None:
        """Test shared_placeholders property returns placeholders used by multiple templates."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Template 1 with title and author
        template1 = template_dir / 'template1.md'
        template1.write_text('---\ntitle: "{{title}}"\nauthor: "{{author}}"\n---\n\n# {{title}} by {{author}}\n')

        # Template 2 with title (shared) and content (not shared)
        template2 = template_dir / 'template2.md'
        template2.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n{{content}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Get shared placeholders
        shared = template_directory.shared_placeholders

        # title should be shared (used in both templates)
        shared_names = [p.name for p in shared]
        assert 'title' in shared_names
        assert 'author' not in shared_names  # only in template1
        assert 'content' not in shared_names  # only in template2


class TestTemplateDirectoryMethods:
    """Tests for TemplateDirectory methods."""

    def test_get_template_by_name_returns_template(self, tmp_path: Path) -> None:
        """Test get_template_by_name returns template when found."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# Test\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Should return template when found
        result = template_directory.get_template_by_name('test')
        assert result is not None
        assert result.name == 'test'

    def test_get_template_by_name_returns_none_for_missing(self, tmp_path: Path) -> None:
        """Test get_template_by_name returns None for non-existent template."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# Test\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Should return None for non-existent template
        result = template_directory.get_template_by_name('nonexistent')
        assert result is None

    def test_get_templates_in_subdirectory(self, tmp_path: Path) -> None:
        """Test get_templates_in_subdirectory filters by subdirectory."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        # Create subdirectory with template
        subdir = template_dir / 'subdir'
        subdir.mkdir()

        root_template = template_dir / 'root.md'
        root_template.write_text('---\ntitle: "{{title}}"\n---\n\n# Root\n')

        sub_template = subdir / 'sub.md'
        sub_template.write_text('---\ntitle: "{{title}}"\n---\n\n# Sub\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Get templates in subdirectory
        subdir_templates = template_directory.get_templates_in_subdirectory('subdir')

        # Should only return template from subdirectory
        assert len(subdir_templates) == 1
        assert subdir_templates[0].name == 'sub'

    def test_validate_placeholder_values_missing_required(self, tmp_path: Path) -> None:
        """Test validate_placeholder_values reports missing required placeholders."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\nauthor: "{{author}}"\n---\n\n# {{title}} by {{author}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Validate with missing required placeholder
        errors = template_directory.validate_placeholder_values({'title': 'Test'})

        # Should report missing 'author'
        assert len(errors) > 0
        assert any('author' in error for error in errors)

    def test_validate_placeholder_values_invalid_value(self, tmp_path: Path) -> None:
        """Test validate_placeholder_values reports invalid placeholder values."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Mock placeholder validation to raise error
        with patch.object(
            Placeholder,
            'validate_value',
            side_effect=InvalidPlaceholderValueError('title', 'Invalid value'),
        ):
            errors = template_directory.validate_placeholder_values({'title': 'bad-value'})

            # Should report validation error
            assert len(errors) > 0

    def test_replace_placeholders_in_all_success(self, tmp_path: Path) -> None:
        """Test replace_placeholders_in_all successfully replaces values."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Should successfully replace placeholders
        results = template_directory.replace_placeholders_in_all({'title': 'My Title'})

        # Should return dictionary with template name as key
        assert 'test' in results
        assert 'My Title' in results['test']

    def test_replace_placeholders_in_all_validation_errors(self, tmp_path: Path) -> None:
        """Test replace_placeholders_in_all raises on validation errors."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\nauthor: "{{author}}"\n---\n\n# {{title}} by {{author}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Should raise TemplateValidationError for missing required placeholder
        with pytest.raises(TemplateValidationError) as exc_info:
            template_directory.replace_placeholders_in_all({'title': 'Test'})

        assert 'validation failed' in str(exc_info.value)

    def test_replace_placeholders_in_all_replacement_error(self, tmp_path: Path) -> None:
        """Test replace_placeholders_in_all handles replacement errors."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Mock replace_placeholders to raise exception
        with patch.object(
            Template,
            'replace_placeholders',
            side_effect=ValueError('Replacement failed'),
        ):
            with pytest.raises(TemplateValidationError) as exc_info:
                template_directory.replace_placeholders_in_all({'title': 'Test'})

            assert 'Failed to replace placeholders' in str(exc_info.value)


class TestTemplateDirectoryClassMethods:
    """Tests for TemplateDirectory class methods."""

    def test_from_directory_creates_instance(self, tmp_path: Path) -> None:
        """Test from_directory creates TemplateDirectory instance."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\n---\n\n# Test\n')

        # Create from directory path
        template_directory = TemplateDirectory.from_directory(template_dir)

        assert template_directory.name == 'test-template'
        assert template_directory.path.value == template_dir
        assert len(template_directory.templates) > 0


class TestTemplateDirectoryToDict:
    """Tests for to_dict serialization."""

    def test_to_dict_includes_all_fields(self, tmp_path: Path) -> None:
        """Test to_dict includes all expected fields."""
        template_dir = tmp_path / 'test-template'
        template_dir.mkdir()

        template_file = template_dir / 'test.md'
        template_file.write_text('---\ntitle: "{{title}}"\ntitle_default: "Default"\n---\n\n# {{title}}\n')

        directory_path = DirectoryPath(template_dir)

        template_directory = TemplateDirectory(
            name='test-template',
            path=directory_path,
        )

        # Convert to dict
        result = template_directory.to_dict()

        # Check all fields are present
        assert 'name' in result
        assert 'path' in result
        assert 'template_count' in result
        assert 'templates' in result
        assert 'structure' in result
        assert 'all_placeholders' in result
        assert 'shared_placeholders' in result
        assert 'required_placeholders' in result
        assert 'optional_placeholders' in result

        # Check content
        assert result['name'] == 'test-template'
        assert result['template_count'] == 1
        assert 'title' in result['optional_placeholders']

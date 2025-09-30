"""Contract tests for TemplateRepositoryPort.

These tests verify that implementations of TemplateRepositoryPort
correctly implement the interface contract.
"""

from pathlib import Path
from typing import Protocol

import pytest

from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.entities.template_directory import TemplateDirectory
from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateDirectoryNotFoundError,
    TemplateNotFoundError,
)
from prosemark.templates.ports.template_repository_port import TemplateRepositoryPort


class TemplateRepositoryContract(Protocol):
    """Protocol that all TemplateRepositoryPort contract tests must implement."""

    @pytest.fixture
    def repository(self) -> TemplateRepositoryPort:
        """Return a TemplateRepositoryPort implementation to test."""
        ...

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with test templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create a simple template
        simple_template = templates_dir / 'simple.md'
        simple_template.write_text('---\ntitle: "{{title}}"\n---\n\n# {{title}}\n\nContent with {{placeholder}}')

        # Create a template directory
        project_dir = templates_dir / 'project'
        project_dir.mkdir()

        overview_template = project_dir / 'overview.md'
        overview_template.write_text('---\nname: "{{project_name}}"\n---\n\n# {{project_name}} Overview')

        tasks_template = project_dir / 'tasks.md'
        tasks_template.write_text('---\nproject: "{{project_name}}"\n---\n\n# Tasks for {{project_name}}')

        return templates_dir


class BaseTemplateRepositoryContract:
    """Contract tests that all TemplateRepositoryPort implementations must pass.

    This class should not be run directly - it should be inherited by concrete test classes.
    """

    def test_find_template_by_name_existing(self, repository: TemplateRepositoryPort, temp_templates_dir: Path) -> None:
        """Test finding an existing template by name."""
        template = repository.find_template_by_name('simple', temp_templates_dir)

        assert template is not None
        assert isinstance(template, Template)
        assert template.name == 'simple'
        assert template.path.value.name == 'simple.md'

    def test_find_template_by_name_non_existing(
        self, repository: TemplateRepositoryPort, temp_templates_dir: Path
    ) -> None:
        """Test finding a non-existing template by name."""
        template = repository.find_template_by_name('nonexistent', temp_templates_dir)

        assert template is None

    def test_find_template_by_name_invalid_directory(self, repository: TemplateRepositoryPort, tmp_path: Path) -> None:
        """Test finding template in non-existent directory."""
        non_existent_dir = tmp_path / 'nonexistent'

        with pytest.raises(TemplateDirectoryNotFoundError):
            repository.find_template_by_name('any', non_existent_dir)

    def test_find_template_directory_existing(
        self, repository: TemplateRepositoryPort, temp_templates_dir: Path
    ) -> None:
        """Test finding an existing template directory."""
        template_dir = repository.find_template_directory('project', temp_templates_dir)

        assert template_dir is not None
        assert isinstance(template_dir, TemplateDirectory)
        assert template_dir.name == 'project'
        assert len(template_dir.templates) >= 2

    def test_find_template_directory_non_existing(
        self, repository: TemplateRepositoryPort, temp_templates_dir: Path
    ) -> None:
        """Test finding a non-existing template directory."""
        template_dir = repository.find_template_directory('nonexistent', temp_templates_dir)

        assert template_dir is None

    def test_find_template_directory_invalid_search_path(
        self, repository: TemplateRepositoryPort, tmp_path: Path
    ) -> None:
        """Test finding template directory with invalid search path."""
        non_existent_dir = tmp_path / 'nonexistent'

        with pytest.raises(TemplateDirectoryNotFoundError):
            repository.find_template_directory('any', non_existent_dir)

    def test_list_templates(self, repository: TemplateRepositoryPort, temp_templates_dir: Path) -> None:
        """Test listing all individual templates."""
        templates = repository.list_templates(temp_templates_dir)

        assert isinstance(templates, list)
        assert len(templates) >= 1
        template_names = [t.name for t in templates]
        assert 'simple' in template_names

    def test_list_templates_invalid_directory(self, repository: TemplateRepositoryPort, tmp_path: Path) -> None:
        """Test listing templates in non-existent directory."""
        non_existent_dir = tmp_path / 'nonexistent'

        with pytest.raises(TemplateDirectoryNotFoundError):
            repository.list_templates(non_existent_dir)

    def test_list_template_directories(self, repository: TemplateRepositoryPort, temp_templates_dir: Path) -> None:
        """Test listing all template directories."""
        directories = repository.list_template_directories(temp_templates_dir)

        assert isinstance(directories, list)
        assert len(directories) >= 1
        directory_names = [d.name for d in directories]
        assert 'project' in directory_names

    def test_list_template_directories_invalid_directory(
        self, repository: TemplateRepositoryPort, tmp_path: Path
    ) -> None:
        """Test listing template directories in non-existent directory."""
        non_existent_dir = tmp_path / 'nonexistent'

        with pytest.raises(TemplateDirectoryNotFoundError):
            repository.list_template_directories(non_existent_dir)

    def test_load_template_content(self, repository: TemplateRepositoryPort, temp_templates_dir: Path) -> None:
        """Test loading template content."""
        template_path = temp_templates_dir / 'simple.md'
        content = repository.load_template_content(template_path)

        assert isinstance(content, str)
        assert '{{title}}' in content
        assert '{{placeholder}}' in content
        assert content.startswith('---')

    def test_load_template_content_non_existing(self, repository: TemplateRepositoryPort, tmp_path: Path) -> None:
        """Test loading content from non-existing template."""
        non_existent_file = tmp_path / 'nonexistent.md'

        with pytest.raises(TemplateNotFoundError):
            repository.load_template_content(non_existent_file)

    def test_validate_template_path_valid(self, repository: TemplateRepositoryPort, temp_templates_dir: Path) -> None:
        """Test validating a valid template path."""
        template_path = temp_templates_dir / 'simple.md'

        assert repository.validate_template_path(template_path) is True

    def test_validate_template_path_invalid(self, repository: TemplateRepositoryPort, tmp_path: Path) -> None:
        """Test validating an invalid template path."""
        invalid_path = tmp_path / 'nonexistent.md'

        assert repository.validate_template_path(invalid_path) is False

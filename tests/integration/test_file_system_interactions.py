from pathlib import Path

import pytest
from click.testing import CliRunner

from prosemark.adapters.markdown import MarkdownFileAdapter
from prosemark.cli import cli
from prosemark.domain.projects import Project
from prosemark.storages.repositories.exceptions import ProjectNotFoundError


class TestFileStructureTests:
    """Test file system structure creation and management."""

    def test_project_directory_structure(self, sample_project: Project, temp_dir: str) -> None:
        """Test that project directory structure is created correctly."""
        project_dir = Path(temp_dir) / 'sample-project'

        # Verify project directory exists
        assert project_dir.exists()
        assert project_dir.is_dir()

        # Verify project metadata file exists
        metadata_file = project_dir / 'project.md'
        assert metadata_file.exists()
        assert metadata_file.is_file()

        # Verify content of metadata file
        content = metadata_file.read_text()
        assert '# Sample Project' in content
        assert 'A test project' in content

        # Verify node files exist
        root_node_file = project_dir / f'{sample_project.root_node.id}.md' if sample_project.root_node else None
        assert root_node_file is not None
        assert root_node_file.exists()

        # Count the number of .md files (should be 1 project file + 6 node files)
        md_files = list(project_dir.glob('*.md'))
        assert len(md_files) == 7

    def test_special_characters_in_filenames(self, cli_runner: CliRunner, temp_dir: str) -> None:
        """Test handling of special characters in project and node names."""
        # Create a project with special characters
        result = cli_runner.invoke(
            cli, ['init', 'Special & Chars: Project!', '--description', 'Testing special characters'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Verify the directory name is sanitized
        project_dir = Path(temp_dir) / 'special-chars-project'
        assert project_dir.exists()

        # Get the root node ID
        adapter = MarkdownFileAdapter(temp_dir)
        project = adapter.load('special-chars-project')
        root_id = project.root_node.id if project.root_node else ''

        # Add a node with special characters
        result = cli_runner.invoke(
            cli, ['add', 'Special & Chars: Project!', root_id, 'Node with: * ? / \\ special chars'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Verify the node was created and can be loaded
        project = adapter.load('special-chars-project')
        assert len(project.root_node.children) == 1 if project.root_node else False
        assert project.root_node.children[0].title == 'Node with: * ? / \\ special chars' if project.root_node else False


class TestFileContentTests:
    """Test file content creation and parsing."""

    def test_markdown_file_content(self, sample_project: Project, temp_dir: str) -> None:
        """Test that Markdown files contain correct content and formatting."""
        project_dir = Path(temp_dir) / 'sample-project'

        # Check root node content
        if sample_project.root_node:
            root_file = project_dir / f'{sample_project.root_node.id}.md'
            content = root_file.read_text()

            # Verify title is in the content
            assert f'# {sample_project.root_node.title}' in content

            # Verify children references are in the content
            for child in sample_project.root_node.children:
                assert f'- [{child.title}]({child.id}.md)' in content

        # Check a leaf node content
        if sample_project.root_node and sample_project.root_node.children:
            node = sample_project.root_node.children[0].children[0]  # Section 1.1
            node_file = project_dir / f'{node.id}.md'
            content = node_file.read_text()

            # Verify title, notecard, content, and notes
            assert f'# {node.title}' in content
            assert node.notecard in content
            assert node.content in content
            assert node.notes in content

            # Verify parent reference
            assert f'Parent: [{node.parent.title}]({node.parent.id}.md)' in content

    def test_reading_writing_various_content(self, cli_runner: CliRunner, temp_dir: str) -> None:
        """Test reading and writing files with various content types."""
        # Create a project
        result = cli_runner.invoke(
            cli, ['init', 'Content Test', '--description', 'Testing various content'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Get the root node ID
        adapter = MarkdownFileAdapter(temp_dir)
        project = adapter.load('content-test')
        root_id = project.root_node.id if project.root_node else ''

        # Add a node with Markdown content
        markdown_content = """
# Markdown Header

This is **bold** and *italic* text.

- List item 1
- List item 2

```python
def hello_world():
    print("Hello, world!")
```

> This is a blockquote
"""

        result = cli_runner.invoke(
            cli, ['add', 'Content Test', root_id, 'Markdown Node',
                  '--content', markdown_content],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Verify the content was saved correctly
        project = adapter.load('content-test')
        node = project.root_node.children[0] if project.root_node else None
        assert node is not None
        assert '# Markdown Header' in node.content
        assert '**bold**' in node.content
        assert '```python' in node.content

        # Add a node with special characters
        special_content = "Line 1\nLine 2 & special chars: < > \" ' \\ / \n\nLine 4"

        node_id = node.id
        result = cli_runner.invoke(
            cli, ['add', 'Content Test', node_id, 'Special Chars Node',
                  '--content', special_content],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Verify the content was saved correctly
        project = adapter.load('content-test')
        special_node = project.get_node_by_id(project.root_node.children[0].children[0].id) if project.root_node else None
        assert special_node is not None
        assert special_node.content == special_content


class TestErrorHandlingTests:
    """Test error handling for file system operations."""

    def test_missing_project(self, cli_runner: CliRunner, temp_dir: str) -> None:
        """Test behavior when trying to access a non-existent project."""
        # Try to load a non-existent project
        result = cli_runner.invoke(
            cli, ['structure', 'NonExistentProject'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code != 0
        assert "Project 'NonExistentProject' not found" in result.output

        # Try to directly load a non-existent project with the adapter
        adapter = MarkdownFileAdapter(temp_dir)
        with pytest.raises(ProjectNotFoundError):
            adapter.load('non-existent-project')

    def test_corrupted_project(self, sample_project: Project, temp_dir: str) -> None:
        """Test behavior when project files are corrupted."""
        project_dir = Path(temp_dir) / 'sample-project'

        # Corrupt the project metadata file
        metadata_file = project_dir / 'project.md'
        metadata_file.write_text('This is not valid project metadata')

        # Try to load the project
        adapter = MarkdownFileAdapter(temp_dir)

        # This should not raise an exception but should log a warning
        # and try to recover as much as possible
        project = adapter.load('sample-project')

        # The project should still be loaded, but might have incomplete metadata
        assert project.name == 'Sample Project'  # Name from directory

        # Corrupt a node file
        if sample_project.root_node and sample_project.root_node.children:
            node_id = sample_project.root_node.children[0].id
            node_file = project_dir / f'{node_id}.md'
            node_file.write_text('This is not valid node content')

            # Try to load the project again
            project = adapter.load('sample-project')

            # The project should load, but the corrupted node might have default values
            corrupted_node = project.get_node_by_id(node_id)
            assert corrupted_node is not None
            assert corrupted_node.title != ''  # Should have some default title

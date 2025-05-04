from pathlib import Path

from click.testing import CliRunner

from prosemark.adapters.markdown import MarkdownFileAdapter


class TestProjectManagementWorkflow:
    """Test the complete project management workflow."""

    def test_create_list_delete_project(self, cli_runner: CliRunner, temp_dir: str) -> None:
        """Test creating, listing, and deleting a project."""
        # Create a new project
        result = cli_runner.invoke(
            args=['init', 'Test Project', '--description', 'A test project'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert "Project 'Test Project' created successfully" in result.output

        # List projects to verify creation
        result = cli_runner.invoke(
            args=['list-projects'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Test Project' in result.output
        assert 'A test project' in result.output

        # Verify project directory exists
        project_dir = Path(temp_dir) / 'test-project'
        assert project_dir.exists()
        assert project_dir.is_dir()

        # Delete the project
        result = cli_runner.invoke(
            args=['delete', 'Test Project'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert "Project 'Test Project' deleted successfully" in result.output

        # Verify project no longer exists in listing
        result = cli_runner.invoke(
            args=['list-projects'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Test Project' not in result.output

        # Verify project directory no longer exists
        assert not project_dir.exists()


class TestNodeManagementWorkflow:
    """Test the complete node management workflow."""

    def test_add_move_remove_nodes(self, cli_runner: CliRunner, temp_dir: str) -> None:
        """Test adding, moving, and removing nodes in a project."""
        # Create a new project
        result = cli_runner.invoke(
            args=['init', 'Node Test', '--description', 'Testing node operations'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Get the root node ID
        adapter = MarkdownFileAdapter(temp_dir)
        project = adapter.load('node-test')
        root_id = project.root_node.node_id if project.root_node else ''

        # Add nodes to the project
        result = cli_runner.invoke(
            args=['add', 'Node Test', root_id, 'Chapter 1', '--notecard', 'First chapter'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Node added successfully' in result.output

        result = cli_runner.invoke(
            args=['add', 'Node Test', root_id, 'Chapter 2', '--notecard', 'Second chapter'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Reload project to get node IDs
        project = adapter.load('node-test')
        ch1_id = project.root_node.children[0].node_id if project.root_node else ''
        ch2_id = project.root_node.children[1].node_id if project.root_node else ''

        # Add a section to Chapter 1
        result = cli_runner.invoke(
            args=['add', 'Node Test', ch1_id, 'Section 1.1', '--notecard', 'First section'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Verify structure
        result = cli_runner.invoke(
            args=['structure', 'Node Test'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Chapter 1' in result.output
        assert 'Chapter 2' in result.output
        assert 'Section 1.1' in result.output

        # Move Section 1.1 to be under Chapter 2
        project = adapter.load('node-test')
        section_id = project.root_node.children[0].children[0].node_id if project.root_node else ''

        result = cli_runner.invoke(
            args=['move', 'Node Test', section_id, ch2_id],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Node moved successfully' in result.output

        # Verify the new structure
        result = cli_runner.invoke(
            args=['structure', 'Node Test'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Check that Section 1.1 is now under Chapter 2
        project = adapter.load('node-test')
        assert len(project.root_node.children[0].children) == 0 if project.root_node else False
        assert len(project.root_node.children[1].children) == 1 if project.root_node else False
        assert project.root_node.children[1].children[0].title == 'Section 1.1' if project.root_node else False

        # Remove Chapter 1
        result = cli_runner.invoke(
            args=['remove', 'Node Test', ch1_id],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Node removed successfully' in result.output

        # Verify final structure
        result = cli_runner.invoke(
            args=['structure', 'Node Test'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Chapter 1' not in result.output
        assert 'Chapter 2' in result.output
        assert 'Section 1.1' in result.output


class TestContentEditingWorkflow:
    """Test the content editing workflow."""

    def test_edit_node_content(self, cli_runner: CliRunner, temp_dir: str) -> None:
        """Test editing node content using direct parameters."""
        # Create a new project
        result = cli_runner.invoke(
            args=['init', 'Edit Test', '--description', 'Testing content editing'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Get the root node ID
        adapter = MarkdownFileAdapter(temp_dir)
        project = adapter.load('edit-test')
        root_id = project.root_node.node_id if project.root_node else ''

        # Add a node to edit
        result = cli_runner.invoke(
            args=['add', 'Edit Test', root_id, 'Chapter 1',
                  '--notecard', 'Original notecard',
                  '--content', 'Original content',
                  '--notes', 'Original notes'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0

        # Get the node ID
        project = adapter.load('edit-test')
        node_id = project.root_node.children[0].node_id if project.root_node else ''

        # Edit the node with direct parameters
        result = cli_runner.invoke(
            args=['edit', 'Edit Test', node_id,
                  '--title', 'Updated Chapter 1',
                  '--notecard', 'Updated notecard',
                  '--content', 'Updated content',
                  '--notes', 'Updated notes',
                  '--editor', 'false'],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Node updated successfully' in result.output

        # Verify the changes
        result = cli_runner.invoke(
            args=['show', 'Edit Test', node_id],
            env={'PROSEMARK_DATA_DIR': temp_dir}
        )
        assert result.exit_code == 0
        assert 'Updated Chapter 1' in result.output
        assert 'Updated notecard' in result.output
        assert 'Updated content' in result.output
        assert 'Updated notes' in result.output

        # Verify the changes in the loaded project
        project = adapter.load('edit-test')
        node = project.get_node_by_id(node_id)
        assert node is not None
        assert node.title == 'Updated Chapter 1'
        assert node.notecard == 'Updated notecard'
        assert node.content == 'Updated content'
        assert node.notes == 'Updated notes'

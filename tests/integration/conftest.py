import shutil
import tempfile
from collections.abc import Generator

import pytest
from click.testing import CliRunner

from prosemark.adapters.markdown import MarkdownFileAdapter
from prosemark.domain.projects import Project


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing.
    
    Returns:
        A path to a temporary directory that will be cleaned up after the test.

    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def cli_runner(temp_dir: str) -> CliRunner:
    """Create a Click CLI runner with a temporary directory.
    
    Args:
        temp_dir: A temporary directory path.
        
    Returns:
        A configured CLI runner for testing commands.

    """
    runner = CliRunner()
    runner.env = {'PROSEMARK_DATA_DIR': temp_dir}
    return runner


@pytest.fixture
def markdown_adapter(temp_dir: str) -> MarkdownFileAdapter:
    """Create a MarkdownFileAdapter with a temporary directory.
    
    Args:
        temp_dir: A temporary directory path.
        
    Returns:
        A configured MarkdownFileAdapter for testing.

    """
    return MarkdownFileAdapter(temp_dir)


@pytest.fixture
def sample_project(markdown_adapter: MarkdownFileAdapter) -> Project:
    """Create a sample project with a basic structure.
    
    Args:
        markdown_adapter: The adapter to use for creating the project.
        
    Returns:
        A Project object with a predefined structure.

    """
    project = markdown_adapter.create_project('Sample Project', 'A test project')

    # Create a simple structure
    root_node = project.root_node
    if root_node:
        # Add first level nodes
        node1 = project.create_node(root_node.id, 'Chapter 1', 'First chapter', 'Chapter 1 content', 'Notes for chapter 1')
        node2 = project.create_node(root_node.id, 'Chapter 2', 'Second chapter', 'Chapter 2 content', 'Notes for chapter 2')

        # Add second level nodes
        project.create_node(node1.id, 'Section 1.1', 'First section', 'Section 1.1 content', 'Notes for section 1.1')
        project.create_node(node1.id, 'Section 1.2', 'Second section', 'Section 1.2 content', 'Notes for section 1.2')
        project.create_node(node2.id, 'Section 2.1', 'First section', 'Section 2.1 content', 'Notes for section 2.1')

    # Save the project
    markdown_adapter.save(project)

    return project


@pytest.fixture
def complex_project_name() -> str:
    """Return a name for a complex project.
    
    Returns:
        A string with the project name.

    """
    return 'Complex Project'


@pytest.fixture
def complex_project(markdown_adapter: MarkdownFileAdapter, complex_project_name: str) -> Project:
    """Create a more complex project with a deeper structure.
    
    Args:
        markdown_adapter: The adapter to use for creating the project.
        complex_project_name: The name to use for the project.
        
    Returns:
        A Project object with a complex structure.

    """
    project = markdown_adapter.create_project(complex_project_name, 'A complex test project')

    # Create a more complex structure
    root_node = project.root_node
    if root_node:
        # Add first level nodes
        part1 = project.create_node(root_node.id, 'Part I', 'Introduction', 'Part I content', 'Notes for Part I')
        part2 = project.create_node(root_node.id, 'Part II', 'Main content', 'Part II content', 'Notes for Part II')
        part3 = project.create_node(root_node.id, 'Part III', 'Conclusion', 'Part III content', 'Notes for Part III')

        # Add second level nodes to Part I
        ch1 = project.create_node(part1.id, 'Chapter 1', 'Introduction chapter', 'Chapter 1 content', 'Notes for chapter 1')
        ch2 = project.create_node(part1.id, 'Chapter 2', 'Background chapter', 'Chapter 2 content', 'Notes for chapter 2')

        # Add second level nodes to Part II
        ch3 = project.create_node(part2.id, 'Chapter 3', 'First main chapter', 'Chapter 3 content', 'Notes for chapter 3')
        ch4 = project.create_node(part2.id, 'Chapter 4', 'Second main chapter', 'Chapter 4 content', 'Notes for chapter 4')
        ch5 = project.create_node(part2.id, 'Chapter 5', 'Third main chapter', 'Chapter 5 content', 'Notes for chapter 5')

        # Add second level nodes to Part III
        ch6 = project.create_node(part3.id, 'Chapter 6', 'Summary chapter', 'Chapter 6 content', 'Notes for chapter 6')

        # Add third level nodes
        project.create_node(ch1.id, 'Section 1.1', 'Introduction section', 'Section 1.1 content', 'Notes for section 1.1')
        project.create_node(ch1.id, 'Section 1.2', 'Purpose section', 'Section 1.2 content', 'Notes for section 1.2')

        project.create_node(ch3.id, 'Section 3.1', 'Theory section', 'Section 3.1 content', 'Notes for section 3.1')
        project.create_node(ch3.id, 'Section 3.2', 'Method section', 'Section 3.2 content', 'Notes for section 3.2')

        project.create_node(ch4.id, 'Section 4.1', 'Results section', 'Section 4.1 content', 'Notes for section 4.1')

        project.create_node(ch6.id, 'Section 6.1', 'Conclusion section', 'Section 6.1 content', 'Notes for section 6.1')
        project.create_node(ch6.id, 'Section 6.2', 'Future work section', 'Section 6.2 content', 'Notes for section 6.2')

    # Save the project
    markdown_adapter.save(project)

    return project

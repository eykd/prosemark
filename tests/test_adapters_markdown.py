"""Tests for the MarkdownFileAdapter."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from prosemark.adapters.markdown import MarkdownFileAdapter
from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_markdown_adapter_initialization(temp_dir: str) -> None:
    """Test that the adapter can be initialized with a directory."""
    # Test with string path
    adapter1 = MarkdownFileAdapter(temp_dir)
    assert adapter1.base_path == Path(temp_dir)

    # Test with Path object
    adapter2 = MarkdownFileAdapter(Path(temp_dir))
    assert adapter2.base_path == Path(temp_dir)

    # Test with non-existent directory (should create it)
    new_dir = os.path.join(temp_dir, 'new_dir')
    adapter3 = MarkdownFileAdapter(new_dir)
    assert adapter3.base_path == Path(new_dir)
    assert os.path.exists(new_dir)

    # Test with a file path (should raise ValueError)
    test_file = os.path.join(temp_dir, 'test_file')
    with open(test_file, 'w') as f:
        f.write('test')

    with pytest.raises(ValueError):
        MarkdownFileAdapter(test_file)


def test_save_and_load_project(temp_dir: str) -> None:
    """Test saving and loading a project."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create a project with some nodes
    project = Project(name='Test Project', description='A test project')
    node1 = project.create_node(project.root_node.id, title='Node 1', content='Content 1')
    assert node1 is not None  # Type assertion for mypy
    node2 = project.create_node(project.root_node.id, title='Node 2', content='Content 2')
    assert node2 is not None  # Type assertion for mypy
    node3 = project.create_node(node1.id, title='Node 3', content='Content 3')
    assert node3 is not None  # Type assertion for mypy

    # Save the project
    adapter.save(project)

    # Verify files were created
    project_dir = Path(temp_dir) / 'Test Project'
    assert project_dir.exists()
    assert (project_dir / 'project.json').exists()
    assert (project_dir / f'{project.root_node.id}.md').exists()
    assert (project_dir / f'{node1.id}.md').exists()
    assert (project_dir / f'{node2.id}.md').exists()
    assert (project_dir / f'{node3.id}.md').exists()

    # Load the project
    loaded_project = adapter.load('Test Project')

    # Verify project metadata
    assert loaded_project.name == 'Test Project'
    assert loaded_project.description == 'A test project'

    # Verify node structure
    assert loaded_project.root_node.title == 'Test Project'
    assert len(loaded_project.root_node.children) == 2

    # Find the loaded nodes by title
    loaded_node1 = next((n for n in loaded_project.root_node.children if n.title == 'Node 1'), None)
    loaded_node2 = next((n for n in loaded_project.root_node.children if n.title == 'Node 2'), None)

    assert loaded_node1 is not None
    assert loaded_node2 is not None
    assert loaded_node1.content == 'Content 1'
    assert loaded_node2.content == 'Content 2'

    # Verify child node
    assert len(loaded_node1.children) == 1
    loaded_node3 = loaded_node1.children[0]
    assert loaded_node3.title == 'Node 3'
    assert loaded_node3.content == 'Content 3'


def test_node_to_markdown_conversion(temp_dir: str) -> None:
    """Test conversion between Node and Markdown format."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create a node with all fields populated
    node = Node(
        title='Test Node',
        notecard='This is a notecard\nwith multiple lines',
        content='# Main Content\n\nThis is the main content.',
        notes='These are some notes about the node.',
        metadata={'key1': 'value1', 'key2': 42},
    )

    # Convert to Markdown
    markdown = adapter._node_to_markdown(node)

    # Write to a file
    test_file = os.path.join(temp_dir, f'{node.id}.md')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Convert back to a Node
    converted_node = adapter._markdown_to_node(Path(test_file))

    # Verify all fields were preserved
    assert converted_node.id == node.id
    assert converted_node.title == 'Test Node'
    assert converted_node.notecard == 'This is a notecard\nwith multiple lines'
    assert '# Main Content' in converted_node.content
    assert 'This is the main content.' in converted_node.content
    assert converted_node.notes == 'These are some notes about the node.'
    assert converted_node.metadata['key1'] == 'value1'
    assert converted_node.metadata['key2'] == 42


def test_list_projects(temp_dir: str) -> None:
    """Test listing projects in the repository."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create some projects
    project1 = adapter.create_project('Project 1', 'First project')
    project2 = adapter.create_project('Project 2', 'Second project')

    # List projects
    projects = adapter.list_projects()

    # Verify the list
    assert len(projects) == 2
    assert {'id': 'Project 1', 'name': 'Project 1'} in projects
    assert {'id': 'Project 2', 'name': 'Project 2'} in projects


def test_create_project(temp_dir: str) -> None:
    """Test creating a new project."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create a project
    project = adapter.create_project('New Project', 'A new project')

    # Verify the project was created
    assert project.name == 'New Project'
    assert project.description == 'A new project'
    assert project.root_node is not None

    # Verify it was saved to disk
    project_dir = Path(temp_dir) / 'New Project'
    assert project_dir.exists()
    assert (project_dir / 'project.json').exists()

    # Verify project.json content
    with open(project_dir / 'project.json', encoding='utf-8') as f:
        project_data = json.load(f)
        assert project_data['name'] == 'New Project'
        assert project_data['description'] == 'A new project'
        assert project_data['root_node_id'] == project.root_node.id

    # Try to create a project with the same name (should raise ValueError)
    with pytest.raises(ValueError):
        adapter.create_project('New Project')


def test_delete_project(temp_dir: str) -> None:
    """Test deleting a project."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create a project
    adapter.create_project('Temporary Project', 'A project to delete')

    # Verify it exists
    project_dir = Path(temp_dir) / 'Temporary Project'
    assert project_dir.exists()

    # Delete the project
    adapter.delete_project('Temporary Project')

    # Verify it was deleted
    assert not project_dir.exists()

    # Try to delete a non-existent project (should raise ValueError)
    with pytest.raises(ValueError):
        adapter.delete_project('Non-existent Project')


def test_project_with_complex_structure(temp_dir: str) -> None:
    """Test saving and loading a project with a complex structure."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create a project with a complex structure
    project = Project(name='Complex Project')

    # Add some top-level nodes
    chapter1 = project.create_node(project.root_node.id, title='Chapter 1')
    assert chapter1 is not None  # Type assertion for mypy
    chapter2 = project.create_node(project.root_node.id, title='Chapter 2')
    assert chapter2 is not None  # Type assertion for mypy

    # Add some child nodes
    scene1 = project.create_node(chapter1.id, title='Scene 1.1')
    assert scene1 is not None  # Type assertion for mypy
    scene2 = project.create_node(chapter1.id, title='Scene 1.2')
    assert scene2 is not None  # Type assertion for mypy
    scene3 = project.create_node(chapter2.id, title='Scene 2.1')
    assert scene3 is not None  # Type assertion for mypy

    # Add some content and metadata
    scene1.content = 'This is scene 1.1 content.'
    scene1.metadata['status'] = 'draft'
    scene2.content = 'This is scene 1.2 content.'
    scene2.metadata['status'] = 'final'
    scene3.content = 'This is scene 2.1 content.'
    scene3.metadata['status'] = 'revision'

    # Save the project
    adapter.save(project)

    # Load the project
    loaded_project = adapter.load('Complex Project')

    # Verify the structure
    assert loaded_project.get_node_count() == 6  # root + 2 chapters + 3 scenes

    # Get the loaded chapters
    loaded_chapter1 = next((n for n in loaded_project.root_node.children if n.title == 'Chapter 1'), None)
    loaded_chapter2 = next((n for n in loaded_project.root_node.children if n.title == 'Chapter 2'), None)

    assert loaded_chapter1 is not None
    assert loaded_chapter2 is not None
    assert len(loaded_chapter1.children) == 2
    assert len(loaded_chapter2.children) == 1

    # Verify scene content and metadata
    loaded_scene1 = next((n for n in loaded_chapter1.children if n.title == 'Scene 1.1'), None)
    loaded_scene2 = next((n for n in loaded_chapter1.children if n.title == 'Scene 1.2'), None)
    loaded_scene3 = next((n for n in loaded_chapter2.children if n.title == 'Scene 2.1'), None)

    assert loaded_scene1 is not None
    assert loaded_scene2 is not None
    assert loaded_scene3 is not None

    assert loaded_scene1.content == 'This is scene 1.1 content.'
    assert loaded_scene1.metadata['status'] == 'draft'
    assert loaded_scene2.content == 'This is scene 1.2 content.'
    assert loaded_scene2.metadata['status'] == 'final'
    assert loaded_scene3.content == 'This is scene 2.1 content.'
    assert loaded_scene3.metadata['status'] == 'revision'


def test_load_nonexistent_project(temp_dir: str) -> None:
    """Test loading a non-existent project."""
    adapter = MarkdownFileAdapter(temp_dir)

    with pytest.raises(ValueError):
        adapter.load('Non-existent Project')


def test_node_with_all_fields(temp_dir: str) -> None:
    """Test saving and loading a node with all fields populated."""
    adapter = MarkdownFileAdapter(temp_dir)

    # Create a project
    project = Project(name='Test Project')

    # Create a node with all fields populated
    node = project.create_node(
        project.root_node.id,
        title='Complete Node',
        notecard='This is a detailed notecard\nwith multiple lines',
        content='# Main Content\n\nThis is the main content with *formatting*.',
        notes='These are some detailed notes about the node.\n\n- Point 1\n- Point 2',
    )
    assert node is not None  # Type assertion for mypy
    node.metadata['status'] = 'draft'
    node.metadata['tags'] = ['important', 'review']
    node.metadata['word_count'] = 150

    # Save the project
    adapter.save(project)

    # Load the project
    loaded_project = adapter.load('Test Project')

    # Find the loaded node
    loaded_node = loaded_project.get_node_by_id(node.id)
    assert loaded_node is not None

    # Verify all fields were preserved
    assert loaded_node.title == 'Complete Node'
    assert loaded_node.notecard == 'This is a detailed notecard\nwith multiple lines'
    assert '# Main Content' in loaded_node.content
    assert 'This is the main content with *formatting*.' in loaded_node.content
    assert 'These are some detailed notes about the node.' in loaded_node.notes
    assert '- Point 1' in loaded_node.notes
    assert '- Point 2' in loaded_node.notes
    assert loaded_node.metadata['status'] == 'draft'
    assert loaded_node.metadata['tags'] == ['important', 'review']
    assert loaded_node.metadata['word_count'] == 150

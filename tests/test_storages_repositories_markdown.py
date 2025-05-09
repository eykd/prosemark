"""Tests for the MarkdownFileAdapter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project
from prosemark.storages.repositories.exceptions import ProjectExistsError, ProjectNotFoundError
from prosemark.storages.repositories.markdown import MarkdownFilesystemProjectRepository


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_markdown_adapter_initialization(temp_dir: str) -> None:
    """Test that the adapter can be initialized with a directory."""
    # Test with string path
    adapter1 = MarkdownFilesystemProjectRepository(temp_dir)
    assert adapter1.base_path == Path(temp_dir)

    # Test with Path object
    adapter2 = MarkdownFilesystemProjectRepository(Path(temp_dir))
    assert adapter2.base_path == Path(temp_dir)

    # Test with non-existent directory (should create it)
    new_dir = Path(temp_dir) / 'new_dir'
    adapter3 = MarkdownFilesystemProjectRepository(str(new_dir))
    assert adapter3.base_path == new_dir
    assert new_dir.exists()

    # Test with a file path (should raise ValueError)
    test_file = Path(temp_dir) / 'test_file'
    test_file.write_text('test')

    with pytest.raises(ValueError, match=r'.*file.*'):
        MarkdownFilesystemProjectRepository(str(test_file))

    # Test creating the base directory when it doesn't exist
    non_existent_dir = Path(temp_dir) / 'does_not_exist'
    if non_existent_dir.exists():
        non_existent_dir.rmdir()
    MarkdownFilesystemProjectRepository(non_existent_dir)
    assert non_existent_dir.exists()


def test_save_and_load_project(temp_dir: str) -> None:
    """Test saving and loading a project."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

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
    project_dir = Path(temp_dir)
    assert (project_dir / '_binder.md').exists()
    assert (project_dir / f'{project.root_node.id}.md').exists()
    assert (project_dir / f'{node1.id}.md').exists()
    assert (project_dir / f'{node2.id}.md').exists()
    assert (project_dir / f'{node3.id}.md').exists()

    # Load the project
    loaded_project = adapter.load()

    # Verify project metadata
    assert loaded_project.name == 'Test Project'
    assert loaded_project.description == 'A test project'

    # Verify node structure
    assert loaded_project.root_node.title == 'Test Project'
    assert len(loaded_project.root_node.children) == 2 or len(loaded_project.root_node.children) == 3

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
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

    # Create a node with all fields populated
    node = Node(
        title='Test Node',
        notecard='This is a notecard\nwith multiple lines',
        content='# Main Content\n\nThis is the main content.',
        notes='These are some notes about the node.',
        metadata={'key1': 'value1', 'key2': 42},
    )

    # Convert to Markdown
    markdown = adapter._node_to_markdown(node)  # noqa: SLF001  # Intentionally testing internal conversion

    # Write to a file
    test_file = Path(temp_dir) / f'{node.id}.md'
    test_file.write_text(markdown, encoding='utf-8')

    # Write notes to a separate file if they exist
    if node.notes:
        notes_file = Path(temp_dir) / f'{node.id} notes.md'
        notes_file.write_text(node.notes, encoding='utf-8')

    # Write notecard to a separate file if it exists
    if node.notecard:
        notecard_file = Path(temp_dir) / f'{node.id} notecard.md'
        notecard_file.write_text(node.notecard, encoding='utf-8')

    # Convert back to a Node
    converted_node = adapter._markdown_to_node(test_file)  # noqa: SLF001  # Intentionally testing internal conversion

    # Verify all fields were preserved
    assert converted_node is not None  # Add type check for mypy
    assert converted_node.id == node.id
    assert converted_node.title == 'Test Node'
    assert converted_node.notecard == 'This is a notecard\nwith multiple lines'
    assert '# Main Content' in converted_node.content
    assert 'This is the main content.' in converted_node.content
    assert converted_node.notes == 'These are some notes about the node.'
    assert converted_node.metadata['key1'] == 'value1'
    assert converted_node.metadata['key2'] == 42

    # Test invalid markdown file format
    invalid_file = Path(temp_dir) / 'invalid.md'
    invalid_file.write_text('This is not a valid markdown file with frontmatter', encoding='utf-8')

    # Now should return None instead of raising ValueError
    result = adapter._markdown_to_node(invalid_file)  # noqa: SLF001  # Intentionally testing internal conversion
    assert result is None

    # Test with metadata parsing
    metadata_file = Path(temp_dir) / 'metadata.md'
    metadata_content = """---
id: test-id
title: Test Title
metadata:
  key1: "value1"
  key2: 42
  invalid: invalid json
---
Content"""
    metadata_file.write_text(metadata_content, encoding='utf-8')
    node_with_metadata = adapter._markdown_to_node(metadata_file)  # noqa: SLF001
    assert node_with_metadata is not None  # Add type check for mypy
    assert node_with_metadata.metadata['key1'] == 'value1'
    assert node_with_metadata.metadata['key2'] == 42
    assert 'invalid' in node_with_metadata.metadata


def test_exists(temp_dir: str) -> None:
    """Test checking if a project exists."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

    # Initially no project exists
    assert not adapter.exists()

    # Create a project
    adapter.create('Project 1', 'First project')

    # Now a project exists
    assert adapter.exists()


def test_create(temp_dir: str) -> None:
    """Test creating a new project."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

    # Create a project
    project = adapter.create('New Project', 'A new project')

    # Verify the project was created
    assert project.name == 'New Project'
    assert project.description == 'A new project'
    assert project.root_node is not None

    # Verify it was saved to disk
    project_dir = Path(temp_dir)
    assert (project_dir / '_binder.md').exists()

    # Verify _binder.md frontmatter content
    binder_path = project_dir / '_binder.md'
    content = binder_path.read_text(encoding='utf-8')
    import re

    frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
    assert frontmatter_match
    frontmatter = frontmatter_match.group(1)
    lines = {
        line.split(':', 1)[0].strip(): line.split(':', 1)[1].strip() for line in frontmatter.split('\n') if ':' in line
    }
    assert lines['title'] == 'New Project'

    # Try to create another project in the same directory (should raise ProjectExistsError)
    with pytest.raises(ProjectExistsError):
        adapter.create('Another Project')


def test_delete(temp_dir: str) -> None:
    """Test deleting a project."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

    # Create a project
    adapter.create('Temporary Project', 'A project to delete')

    # Verify it exists
    project_dir = Path(temp_dir)
    assert (project_dir / '_binder.md').exists()

    # Delete the project
    adapter.delete()

    # Verify it was deleted
    assert not (project_dir / '_binder.md').exists()

    # Try to delete a non-existent project (should raise ProjectNotFoundError)
    with pytest.raises(ProjectNotFoundError):
        adapter.delete()


def test_project_with_complex_structure(temp_dir: str) -> None:
    """Test saving and loading a project with a complex structure."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

    # Test loading a project with no root_node_id specified
    project_dir = Path(temp_dir)
    # Write a minimal _binder.md file
    binder_content = """---
id: _binder
title: Simple Project
---
"""
    (project_dir / '_binder.md').write_text(binder_content, encoding='utf-8')

    simple_project = adapter.load()
    assert simple_project.name == 'Simple Project'
    assert simple_project.root_node.title == 'Simple Project'

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
    loaded_project = adapter.load()

    # Verify the structure
    assert loaded_project.get_node_count() == 6  # root + 2 chapters + 3 scenes

    # Get the loaded chapters
    loaded_chapter1 = next((n for n in loaded_project.root_node.children if n.title == 'Chapter 1'), None)
    loaded_chapter2 = next((n for n in loaded_project.root_node.children if n.title == 'Chapter 2'), None)

    assert loaded_chapter1 is not None
    assert loaded_chapter2 is not None
    assert len(loaded_chapter1.children) == 2 or len(loaded_chapter1.children) == 0
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


def test_load_nonexistent_project_returns_empty(temp_dir: str) -> None:
    """Test loading a non-existent project returns an empty Project, not an error."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

    # Test non-existent project (no _binder.md)
    # First make sure _binder.md doesn't exist
    binder_md = Path(temp_dir) / '_binder.md'
    if binder_md.exists():
        binder_md.unlink()

    project = adapter.load()
    assert isinstance(project, Project)
    assert project.name == ''
    assert project.description == ''
    assert project.root_node.id == '_binder'
    assert project.root_node.title == ''
    assert project.get_node_count() == 1


def test_load_malformed_binder_returns_empty(temp_dir: str) -> None:
    """Test loading a project with a malformed _binder.md returns an empty Project."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)
    binder_md = Path(temp_dir) / '_binder.md'
    # Write malformed content (no valid frontmatter)
    binder_md.write_text('This is not valid frontmatter', encoding='utf-8')

    project = adapter.load()
    assert isinstance(project, Project)
    assert project.name == ''
    assert project.description == ''
    assert project.root_node.id == '_binder'
    assert project.root_node.title == ''
    assert project.get_node_count() == 1


def test_node_with_all_fields(temp_dir: str) -> None:
    """Test saving and loading a node with all fields populated."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)

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
    loaded_project = adapter.load()

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

    # Test with empty title but other sections
    markdown = """// Title:

// Notecard (brief summary):
This is a notecard

// Content (main text):
This is the content

// Notes (additional information):
These are notes
"""
    sections = adapter.parse_edit_markdown(markdown)
    assert 'title' in sections
    assert sections['title'] == ''
    assert sections['notecard'] == 'This is a notecard'


def test_parse_id_line_and_title_line() -> None:
    adapter = MarkdownFilesystemProjectRepository('.')
    data: dict[str, str] = {}
    adapter._parse_id_line('id: test-id', data)  # noqa: SLF001
    assert data['id'] == 'test-id'
    adapter._parse_title_line('title: Test Title', data)  # noqa: SLF001
    assert data['name'] == 'Test Title'


def test_parse_children_line() -> None:
    adapter = MarkdownFilesystemProjectRepository('.')
    data: dict[str, list[str]] = {}
    adapter._parse_children_line('children: [id1, id2, id3]', data)  # noqa: SLF001
    assert data['children'] == ['id1', 'id2', 'id3']
    # Test with extra spaces
    data2: dict[str, list[str]] = {}
    adapter._parse_children_line('children: [ id1 , id2 , id3 ]', data2)  # noqa: SLF001
    assert data2['children'] == ['id1', 'id2', 'id3']


def test_parse_notes_and_notecard_file_line() -> None:
    adapter = MarkdownFilesystemProjectRepository('.')
    data: dict[str, str] = {}
    adapter._parse_notes_file_line('notes_file: notes.md', data)  # noqa: SLF001
    assert data['notes_file'] == 'notes.md'
    adapter._parse_notecard_file_line('notecard_file: notecard.md', data)  # noqa: SLF001
    assert data['notecard_file'] == 'notecard.md'


def test_parse_metadata_line_and_item_line() -> None:
    adapter = MarkdownFilesystemProjectRepository('.')
    data: dict[str, dict[str, object]] = {}
    adapter._parse_metadata_line(data)  # noqa: SLF001
    assert 'metadata' in data
    assert data['metadata'] == {}
    # Add a metadata item (valid JSON)
    adapter._parse_metadata_item_line('  key1: "value1"', data)  # noqa: SLF001
    assert data['metadata']['key1'] == 'value1'
    # Add a metadata item (int)
    adapter._parse_metadata_item_line('  key2: 42', data)  # noqa: SLF001
    assert data['metadata']['key2'] == 42
    # Add a metadata item (invalid JSON)
    adapter._parse_metadata_item_line('  key3: notjson', data)  # noqa: SLF001
    assert data['metadata']['key3'] == 'notjson'


def test_parse_frontmatter_lines() -> None:
    adapter = MarkdownFilesystemProjectRepository('.')
    frontmatter = (
        'id: test-id\n'
        'title: Test Title\n'
        'description: "A description"\n'
        'children: [id1, id2]\n'
        'notes_file: notes.md\n'
        'notecard_file: notecard.md\n'
        'metadata:\n'
        '  key1: "value1"\n'
        '  key2: 42\n'
    )
    data: dict[str, Any] = adapter._parse_frontmatter_lines(frontmatter)  # noqa: SLF001
    assert data['id'] == 'test-id'
    assert data['name'] == 'Test Title'
    assert data['description'] == 'A description'
    assert data['children'] == ['id1', 'id2']
    assert data['notes_file'] == 'notes.md'
    assert data['notecard_file'] == 'notecard.md'
    assert data['metadata']['key1'] == 'value1'
    assert data['metadata']['key2'] == 42


def test_root_node_notes_and_notecard(temp_dir: str) -> None:
    """Test saving and loading a project where the root node has notes and a notecard."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)
    # Create a project with notes and notecard on the root node
    project = Project(name='Root Notes Project', description='Project with root notes')
    project.root_node.notes = 'Root node notes content.'
    project.root_node.notecard = 'Root node notecard content.'
    adapter.save(project)
    project_dir = Path(temp_dir)
    # Check that notes and notecard files exist for _binder
    notes_path = project_dir / '_binder notes.md'
    notecard_path = project_dir / '_binder notecard.md'
    assert notes_path.exists()
    assert notecard_path.exists()
    # Check that the YAML frontmatter in _binder.md includes notes_file and notecard_file
    binder_path = project_dir / '_binder.md'
    content = binder_path.read_text(encoding='utf-8')
    assert 'notes_file: _binder notes.md' in content
    assert 'notecard_file: _binder notecard.md' in content
    # Load the project and verify notes and notecard are loaded
    loaded_project = adapter.load()
    assert loaded_project.root_node.notes == 'Root node notes content.'
    assert loaded_project.root_node.notecard == 'Root node notecard content.'


def test_load_project_with_empty_frontmatter(temp_dir: str) -> None:
    """Test loading a project with an empty frontmatter block in _binder.md."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)
    binder_path = Path(temp_dir) / '_binder.md'
    binder_path.write_text('---\n---\n', encoding='utf-8')
    project = adapter.load()
    assert isinstance(project, Project)
    assert project.name == ''
    assert project.root_node.id == '_binder'


def test_node_notes_file_loading(temp_dir: str) -> None:
    """Test that a node with a notes_file loads the notes from the file."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)
    # Create a node and manually write a notes file
    node = Node(title='Node with Notes', content='Some content')
    node.notes = 'Node notes content.'
    markdown = adapter._node_to_markdown(node)  # noqa: SLF001
    node_file = Path(temp_dir) / f'{node.id}.md'
    node_file.write_text(markdown, encoding='utf-8')
    notes_file = Path(temp_dir) / f'{node.id} notes.md'
    notes_file.write_text(node.notes, encoding='utf-8')
    # Now load the node
    loaded_node = adapter._markdown_to_node(node_file)  # noqa: SLF001
    assert loaded_node is not None
    assert loaded_node.notes == 'Node notes content.'


def test_load_project_metadata_no_frontmatter(temp_dir: str) -> None:
    """Test _load_project_metadata returns empty dict if frontmatter is missing (no --- at all or empty file)."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)
    binder_path = Path(temp_dir) / '_binder.md'
    # Case 1: File with no frontmatter at all
    binder_path.write_text('no frontmatter here', encoding='utf-8')
    result = adapter._load_project_metadata(Path(temp_dir))  # noqa: SLF001
    assert result == {}
    # Case 2: Empty file
    binder_path.write_text('', encoding='utf-8')
    result = adapter._load_project_metadata(Path(temp_dir))  # noqa: SLF001
    assert result == {}


def test_node_notes_file_missing_file(temp_dir: str) -> None:
    """Test that a node with a notes_file specified but missing file results in empty notes."""
    adapter = MarkdownFilesystemProjectRepository(temp_dir)
    # Create a node and write a markdown file with notes_file, but do not create the notes file
    node = Node(title='Node with Missing Notes', content='Some content')
    node.notes = 'Should not be loaded'  # This will not be written to file
    markdown = adapter._node_to_markdown(node)  # noqa: SLF001
    # Remove the notes file reference from the file system
    node_file = Path(temp_dir) / f'{node.id}.md'
    node_file.write_text(markdown, encoding='utf-8')
    notes_file = Path(temp_dir) / f'{node.id} notes.md'
    if notes_file.exists():
        notes_file.unlink()
    # Now load the node
    loaded_node = adapter._markdown_to_node(node_file)  # noqa: SLF001
    assert loaded_node is not None
    assert loaded_node.notes == ''

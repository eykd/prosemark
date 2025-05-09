"""Tests for the ProjectRepository class."""

from __future__ import annotations

import json
from unittest.mock import ANY, MagicMock, patch

from prosemark.domain.nodes import Node
from prosemark.domain.projects import Project
from prosemark.parsers.outlines import OutlineNode, OutlineNodeType
from prosemark.repositories.project import ProjectRepository


class TestProjectRepository:
    """Tests for the ProjectRepository class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_storage = MagicMock()
        self.repo = ProjectRepository(self.mock_storage)

    def test_init(self) -> None:
        """Test initialization of ProjectRepository."""
        assert self.repo.storage == self.mock_storage

    def test_load_project_empty_binder(self) -> None:
        """Test loading a project with an empty binder."""
        # Setup
        self.mock_storage.get_binder.return_value = ''

        # Execute
        project = self.repo.load_project()

        # Verify
        assert project.name == 'New Project'
        assert len(project.root_node.children) == 0
        self.mock_storage.get_binder.assert_called_once()

    def test_load_project_with_binder(self) -> None:
        """Test loading a project with a binder."""
        # Setup
        binder_content = '# Test Project\n\n- node1: First Node\n  - node2: Second Node\n'
        self.mock_storage.get_binder.return_value = binder_content

        # Execute
        project = self.repo.load_project()

        # Verify
        assert project.name == 'Project'  # Default name
        assert len(project.root_node.children) == 1
        child = project.root_node.children[0]
        assert child.id == 'node1'
        assert child.title == 'First Node'
        assert len(child.children) == 1
        grandchild = child.children[0]
        assert grandchild.id == 'node2'
        assert grandchild.title == 'Second Node'

    def test_save_project(self) -> None:
        """Test saving a project."""
        # Setup
        project = Project(name='Test Project')
        node1 = Node(node_id='node1', title='First Node')
        node2 = Node(node_id='node2', title='Second Node')
        project.root_node.add_child(node1)
        node1.add_child(node2)

        # Execute
        self.repo.save_project(project)

        # Verify
        # Use a more flexible verification approach
        self.mock_storage.write.assert_any_call('_binder', ANY)
        binder_content = self.mock_storage.write.call_args_list[0][0][1]
        assert '# Test Project' in binder_content
        assert 'node1: First Node' in binder_content
        assert 'node2: Second Node' in binder_content
        self.mock_storage.write.assert_any_call(
            project.root_node.id, self.repo.serialize_node_content(project.root_node)
        )
        self.mock_storage.write.assert_any_call('node1', self.repo.serialize_node_content(node1))
        self.mock_storage.write.assert_any_call('node2', self.repo.serialize_node_content(node2))

    def test_load_node_content(self) -> None:
        """Test loading node content."""
        # Setup
        node = Node(node_id='test_node', title='Test Node')
        node_content = json.dumps({
            'id': 'test_node',
            'title': 'Updated Title',
            'notecard': 'Test notecard',
            'content': 'Test content',
            'notes': 'Test notes',
            'metadata': {'key': 'value'},
        })
        self.mock_storage.read.return_value = node_content

        # Execute
        self.repo.load_node_content(node)

        # Verify
        self.mock_storage.read.assert_called_once_with('test_node')
        assert node.title == 'Updated Title'
        assert node.notecard == 'Test notecard'
        assert node.content == 'Test content'
        assert node.notes == 'Test notes'
        assert node.metadata == {'key': 'value'}

    def test_load_node_content_empty(self) -> None:
        """Test loading node content when storage returns empty string."""
        # Setup
        node = Node(node_id='test_node', title='Test Node')
        self.mock_storage.read.return_value = ''

        # Execute
        self.repo.load_node_content(node)

        # Verify
        self.mock_storage.read.assert_called_once_with('test_node')
        assert node.title == 'Test Node'  # Unchanged

    def test_load_node_content_invalid_json(self) -> None:
        """Test loading node content with invalid JSON."""
        # Setup
        node = Node(node_id='test_node', title='Test Node')
        self.mock_storage.read.return_value = 'Not valid JSON'

        # Execute
        self.repo.load_node_content(node)

        # Verify
        self.mock_storage.read.assert_called_once_with('test_node')
        assert node.title == 'Test Node'  # Unchanged
        assert node.content == 'Not valid JSON'  # Raw content used

    def test_save_node(self) -> None:
        """Test saving a node."""
        # Setup
        node = Node(
            node_id='test_node',
            title='Test Node',
            notecard='Test notecard',
            content='Test content',
            notes='Test notes',
            metadata={'key': 'value'},
        )

        # Execute
        self.repo.save_node(node)

        # Verify
        expected_content = json.dumps(
            {
                'id': 'test_node',
                'title': 'Test Node',
                'notecard': 'Test notecard',
                'content': 'Test content',
                'notes': 'Test notes',
                'metadata': {'key': 'value'},
            },
            indent=2,
        )
        self.mock_storage.write.assert_called_once_with('test_node', expected_content)

    def test_build_node_structure(self) -> None:
        """Test building node structure from outline."""
        # Setup
        project = Project(name='Test Project')
        doc_node = OutlineNode(type=OutlineNodeType.DOCUMENT)
        list_node = OutlineNode(type=OutlineNodeType.LIST)
        item1 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- node1: First Node')
        item2 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- node2: Second Node')
        nested_list = OutlineNode(type=OutlineNodeType.LIST)
        nested_item = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- node3: Nested Node')

        # Build structure
        doc_node.add_child(list_node)
        list_node.add_child(item1)
        list_node.add_child(item2)
        item1.add_child(nested_list)
        nested_list.add_child(nested_item)

        # Execute
        self.repo.build_node_structure(project, doc_node)

        # Verify
        assert len(project.root_node.children) == 2
        assert project.root_node.children[0].id == 'node1'
        assert project.root_node.children[0].title == 'First Node'
        assert project.root_node.children[1].id == 'node2'
        assert project.root_node.children[1].title == 'Second Node'
        assert len(project.root_node.children[0].children) == 1
        assert project.root_node.children[0].children[0].id == 'node3'
        assert project.root_node.children[0].children[0].title == 'Nested Node'

    def test_process_list_items(self) -> None:
        """Test processing list items."""
        # Setup
        parent_node = Node(node_id='parent', title='Parent')
        list_node = OutlineNode(type=OutlineNodeType.LIST)
        item1 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- node1: First Node')
        item2 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- node2: Second Node')
        list_node.add_child(item1)
        list_node.add_child(item2)

        # Execute
        self.repo.process_list_items(parent_node, list_node)

        # Verify
        assert len(parent_node.children) == 2
        assert parent_node.children[0].id == 'node1'
        assert parent_node.children[0].title == 'First Node'
        assert parent_node.children[1].id == 'node2'
        assert parent_node.children[1].title == 'Second Node'

    def test_parse_list_item(self) -> None:
        """Test parsing list item content."""
        # Test with standard format
        result = self.repo.parse_list_item('- node1: First Node')
        assert result == {'id': 'node1', 'title': 'First Node'}

        # Test with different list marker
        result = self.repo.parse_list_item('* node2: Second Node')
        assert result == {'id': 'node2', 'title': 'Second Node'}

        # Test with + marker
        result = self.repo.parse_list_item('+ node3: Third Node')
        assert result == {'id': 'node3', 'title': 'Third Node'}

        # Test without colon
        result = self.repo.parse_list_item('- Just a title')
        assert result == {'title': 'Just a title'}

    def test_generate_binder_content(self) -> None:
        """Test generating binder content."""
        # Setup
        project = Project(name='Test Project', description='Project description')
        node1 = Node(node_id='node1', title='First Node')
        node2 = Node(node_id='node2', title='Second Node')
        node3 = Node(node_id='node3', title='Nested Node')
        project.root_node.add_child(node1)
        project.root_node.add_child(node2)
        node1.add_child(node3)

        # Execute
        result = self.repo.generate_binder_content(project)

        # Verify
        expected = '# Test Project\n\nProject description\n\n- node1: First Node\n  - node3: Nested Node\n- node2: Second Node\n'
        assert result == expected

    def test_generate_binder_content_no_description(self) -> None:
        """Test generating binder content without description."""
        # Setup
        project = Project(name='Test Project')
        node1 = Node(node_id='node1', title='First Node')
        project.root_node.add_child(node1)

        # Execute
        result = self.repo.generate_binder_content(project)

        # Verify
        expected = '# Test Project\n\n- node1: First Node\n'
        assert result == expected

    def test_append_node_to_binder(self) -> None:
        """Test appending node to binder content."""
        # Setup
        lines: list[str] = []
        node = Node(node_id='node1', title='First Node')
        child = Node(node_id='node2', title='Child Node')
        node.add_child(child)

        # Execute
        self.repo.append_node_to_binder(node, lines, 0)

        # Verify
        assert lines == ['- node1: First Node\n', '  - node2: Child Node\n']

    def test_save_node_recursive(self) -> None:
        """Test saving node recursively."""
        # Setup
        node = Node(node_id='node1', title='First Node')
        child = Node(node_id='node2', title='Child Node')
        node.add_child(child)

        # Mock save_node to track calls
        with patch.object(self.repo, 'save_node') as mock_save:
            # Execute
            self.repo.save_node_recursive(node)

            # Verify
            assert mock_save.call_count == 2
            mock_save.assert_any_call(node)
            mock_save.assert_any_call(child)

    def test_serialize_node_content(self) -> None:
        """Test serializing node content."""
        # Setup
        node = Node(
            node_id='test_node',
            title='Test Node',
            notecard='Test notecard',
            content='Test content',
            notes='Test notes',
            metadata={'key': 'value'},
        )

        # Execute
        result = self.repo.serialize_node_content(node)

        # Verify
        expected_data = {
            'id': 'test_node',
            'title': 'Test Node',
            'notecard': 'Test notecard',
            'content': 'Test content',
            'notes': 'Test notes',
            'metadata': {'key': 'value'},
        }
        assert json.loads(result) == expected_data

    def test_parse_node_content(self) -> None:
        """Test parsing node content."""
        # Setup
        node = Node(node_id='test_node', title='Original Title')
        content = json.dumps({
            'title': 'Updated Title',
            'notecard': 'Test notecard',
            'content': 'Test content',
            'notes': 'Test notes',
            'metadata': {'key': 'value'},
        })

        # Execute
        self.repo.parse_node_content(node, content)

        # Verify
        assert node.title == 'Updated Title'
        assert node.notecard == 'Test notecard'
        assert node.content == 'Test content'
        assert node.notes == 'Test notes'
        assert node.metadata == {'key': 'value'}

    def test_parse_node_content_partial_data(self) -> None:
        """Test parsing node content with partial data."""
        # Setup
        node = Node(node_id='test_node', title='Original Title')
        content = json.dumps({
            'title': 'Updated Title',
            # Missing other fields
        })

        # Execute
        self.repo.parse_node_content(node, content)

        # Verify
        assert node.title == 'Updated Title'
        assert node.notecard == ''  # Default value preserved
        assert node.content == ''  # Default value preserved
        assert node.notes == ''  # Default value preserved
        assert node.metadata == {}  # Default value preserved

    def test_parse_node_content_invalid_metadata(self) -> None:
        """Test parsing node content with invalid metadata."""
        # Setup
        node = Node(node_id='test_node', title='Original Title')
        content = json.dumps({
            'title': 'Updated Title',
            'metadata': 'not a dict',  # Invalid metadata
        })

        # Execute
        self.repo.parse_node_content(node, content)

        # Verify
        assert node.title == 'Updated Title'
        assert node.metadata == {}  # Default value preserved

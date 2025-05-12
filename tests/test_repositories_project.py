"""Tests for the ProjectRepository class."""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

from prosemark.domain.factories import NodeFactory, ProjectFactory, RootNodeFactory
from prosemark.domain.nodes import Node
from prosemark.parsers.nodes import NodeParser
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
        assert project.title == 'New Project'
        assert len(project.root_node.children) == 0
        self.mock_storage.get_binder.assert_called_once()

    def test_load_project_with_binder(self) -> None:
        """Test loading a project with a binder."""
        # Setup
        binder_content = '# Test Project\n\n- [First Node](node1.md)\n  - [Second Node](node2.md)\n'
        self.mock_storage.get_binder.return_value = binder_content

        # Execute
        project = self.repo.load_project()

        # Verify
        assert project.title == 'New Project'  # Default name
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
        project = ProjectFactory.build()
        project.root_node.title = 'Test Project'
        node1 = NodeFactory.build(id='node1', title='First Node')
        node2 = NodeFactory.build(id='node2', title='Second Node')
        project.root_node.add_child(node1)
        node1.add_child(node2)

        # Execute
        self.repo.save_project(project)

        # Verify
        # Use a more flexible verification approach
        self.mock_storage.write.assert_any_call('_binder', ANY)
        binder_content = self.mock_storage.write.call_args_list[0][0][1]
        assert '# Test Project' in binder_content
        assert '[First Node](node1.md)' in binder_content
        assert '[Second Node](node2.md)' in binder_content
        self.mock_storage.write.assert_any_call(
            project.root_node.id, self.repo.serialize_node_content(project.root_node)
        )
        self.mock_storage.write.assert_any_call(node1.id, self.repo.serialize_node_content(node1))
        self.mock_storage.write.assert_any_call(node2.id, self.repo.serialize_node_content(node2))

    def test_load_node_content(self) -> None:
        """Test loading node content."""
        # Setup
        project = ProjectFactory.build()
        project.root_node.title = 'Test Project'
        node = Node(id='test_node', title='Test Node')
        node_content = """---
id: test_node
title: Updated Title
key: value
---
// Notecard: Test notecard
// Notes: Test notes

Test content"""
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
        project = ProjectFactory.build()
        project.root_node.title = 'Test Project'
        node = NodeFactory.build(id='test_node', title='Test Node')
        self.mock_storage.read.return_value = ''

        # Execute
        self.repo.load_node_content(node)

        # Verify
        self.mock_storage.read.assert_called_once_with('test_node')
        assert node.title == 'Test Node'  # Unchanged

    def test_load_node_content_invalid_format(self) -> None:
        """Test loading node content with invalid format."""
        # Setup
        project = ProjectFactory.build()
        project.root_node.title = 'Test Project'
        node = NodeFactory.build(id='test_node', title='Test Node')
        self.mock_storage.read.return_value = 'Not valid format'

        # Execute
        self.repo.load_node_content(node)

        # Verify
        self.mock_storage.read.assert_called_once_with('test_node')
        assert node.title == 'Test Node'  # Unchanged
        assert node.content == 'Not valid format'  # Raw content used

    def test_save_node(self) -> None:
        """Test saving a node."""
        # Setup
        project = ProjectFactory.build()
        project.root_node.title = 'Test Project'
        project.root_node.notecard = 'Project description'
        node = NodeFactory.build(
            id='test_node',
            title='Test Node',
            notecard='Test notecard',
            content='Test content',
            notes='Test notes',
            metadata={'key': 'value'},
        )

        # Mock NodeParser.serialize to return a predictable string
        with patch.object(NodeParser, 'serialize', return_value='serialized content') as mock_serialize:
            # Execute
            self.repo.save_node(node)

            # Verify
            mock_serialize.assert_called_once_with({
                'id': 'test_node',
                'title': 'Test Node',
                'notecard': 'Test notecard',
                'content': 'Test content',
                'notes': 'Test notes',
                'metadata': {'key': 'value'},
            })
            self.mock_storage.write.assert_called_once_with('test_node', 'serialized content')

    def test_build_node_structure(self) -> None:
        """Test building node structure from outline."""
        # Setup
        project = ProjectFactory.build()
        doc_node = OutlineNode(type=OutlineNodeType.DOCUMENT)
        list_node = OutlineNode(type=OutlineNodeType.LIST)
        item1 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- [First Node](node1.md)')
        item2 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- [Second Node](node2.md)')
        nested_list = OutlineNode(type=OutlineNodeType.LIST)
        nested_item = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- [Nested Node](node3.md)')

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
        parent_node = Node(id='parent', title='Parent')
        list_node = OutlineNode(type=OutlineNodeType.LIST)
        item1 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- [First Node](node1.md)')
        item2 = OutlineNode(type=OutlineNodeType.LIST_ITEM, content='- [Second Node](node2.md)')
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
        result = self.repo.parse_list_item('- [First Node](node1.md)')
        assert result == {'id': 'node1', 'title': 'First Node'}

        # Test with different list marker
        result = self.repo.parse_list_item('* [Second Node](node2.md)')
        assert result == {'id': 'node2', 'title': 'Second Node'}

        # Test with + marker
        result = self.repo.parse_list_item('+ [Third Node](node3.md)')
        assert result == {'id': 'node3', 'title': 'Third Node'}

        # Test without markdown link format
        result = self.repo.parse_list_item('- Just a title')
        assert result == {'title': 'Just a title'}

    def test_generate_binder_content(self) -> None:
        """Test generating binder content."""
        # Setup
        project = ProjectFactory.build(
            root_node=RootNodeFactory.build(
                title='Test Project',
                notecard='Project description',
            )
        )
        node1 = NodeFactory.build(id='node1', title='First Node')
        node2 = NodeFactory.build(id='node2', title='Second Node')
        node3 = NodeFactory.build(id='node3', title='Nested Node')
        project.root_node.add_child(node1)
        project.root_node.add_child(node2)
        node1.add_child(node3)

        # Execute
        result = self.repo.generate_binder_content(project)

        # Verify
        expected = '# Test Project\n\nProject description\n\n- [First Node](node1.md)\n  - [Nested Node](node3.md)\n- [Second Node](node2.md)\n'
        assert result == expected

    def test_generate_binder_content_no_description(self) -> None:
        """Test generating binder content without description."""
        # Setup
        project = ProjectFactory.build(
            root_node=RootNodeFactory.build(
                title='New Project',
                notecard='Test description',
            )
        )
        node1 = NodeFactory.build(id='node1', title='First Node')
        project.root_node.add_child(node1)

        # Execute
        result = self.repo.generate_binder_content(project)

        # Verify
        expected = '# New Project\n\nTest description\n\n- [First Node](node1.md)\n'
        assert result == expected

    def test_append_node_to_binder(self) -> None:
        """Test appending node to binder content."""
        # Setup
        lines: list[str] = []
        node = Node(id='node1', title='First Node')
        child = Node(id='node2', title='Child Node')
        node.add_child(child)

        # Execute
        self.repo.append_node_to_binder(node, lines, 0)

        # Verify
        assert lines == ['- [First Node](node1.md)\n', '  - [Child Node](node2.md)\n']

    def test_save_node_recursive(self) -> None:
        """Test saving node recursively."""
        # Setup
        node = Node(id='node1', title='First Node')
        child = Node(id='node2', title='Child Node')
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
            id='test_node',
            title='Test Node',
            notecard='Test notecard',
            content='Test content',
            notes='Test notes',
            metadata={'key': 'value'},
        )

        # Mock NodeParser.serialize
        with patch.object(NodeParser, 'serialize', return_value='serialized content') as mock_serialize:
            # Execute
            result = self.repo.serialize_node_content(node)

            # Verify
            mock_serialize.assert_called_once_with({
                'id': 'test_node',
                'title': 'Test Node',
                'notecard': 'Test notecard',
                'content': 'Test content',
                'notes': 'Test notes',
                'metadata': {'key': 'value'},
            })
            assert result == 'serialized content'

    def test_parse_node_content(self) -> None:
        """Test parsing node content."""
        # Setup
        node = Node(id='test_node', title='Original Title')
        content = 'Some content'

        # Mock NodeParser.parse
        parsed_data = {
            'id': 'test_node',
            'title': 'Updated Title',
            'notecard': 'Test notecard',
            'content': 'Test content',
            'notes': 'Test notes',
            'metadata': {'key': 'value'},
        }

        with patch.object(NodeParser, 'parse', return_value=parsed_data) as mock_parse:
            # Execute
            self.repo.parse_node_content(node, content)

            # Verify
            mock_parse.assert_called_once_with(content, 'test_node')
            assert node.title == 'Updated Title'
            assert node.notecard == 'Test notecard'
            assert node.content == 'Test content'
            assert node.notes == 'Test notes'
            assert node.metadata == {'key': 'value'}

    def test_parse_node_content_partial_data(self) -> None:
        """Test parsing node content with partial data."""
        # Setup
        node = Node(id='test_node', title='Original Title')
        content = 'Some content'

        # Mock NodeParser.parse with partial data
        parsed_data = {
            'id': 'test_node',
            'title': 'Updated Title',
            # Missing other fields
        }

        with patch.object(NodeParser, 'parse', return_value=parsed_data) as mock_parse:
            # Execute
            self.repo.parse_node_content(node, content)

            # Verify
            mock_parse.assert_called_once_with(content, 'test_node')
            assert node.title == 'Updated Title'
            assert node.notecard == ''  # Default value preserved
            assert node.content == ''  # Default value preserved
            assert node.notes == ''  # Default value preserved
            assert node.metadata == {}  # Default value preserved

    def test_parse_node_content_invalid_metadata(self) -> None:
        """Test parsing node content with invalid metadata."""
        # Setup
        node = Node(id='test_node', title='Original Title')
        content = 'Some content'

        # Mock NodeParser.parse with invalid metadata
        parsed_data = {
            'id': 'test_node',
            'title': 'Updated Title',
            'metadata': 'not a dict',  # Invalid metadata
        }

        with patch.object(NodeParser, 'parse', return_value=parsed_data) as mock_parse:
            # Execute
            self.repo.parse_node_content(node, content)

            # Verify
            mock_parse.assert_called_once_with(content, 'test_node')
            assert node.title == 'Updated Title'
            assert node.metadata == {}  # Default value preserved

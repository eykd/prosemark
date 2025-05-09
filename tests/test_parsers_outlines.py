"""Tests for the outline parser module."""

from enum import Enum, auto

from prosemark.parsers.outlines import Node, NodeType, OutlineParser


class TestNode:
    """Tests for the Node class."""

    def test_node_initialization(self) -> None:
        """Test that a node can be initialized with the correct properties."""
        node = Node(type=NodeType.DOCUMENT)
        assert node.type == NodeType.DOCUMENT
        assert node.content == ''
        assert node.children == []
        assert node.parent is None

        node_with_content = Node(type=NodeType.TEXT, content='Hello world')
        assert node_with_content.type == NodeType.TEXT
        assert node_with_content.content == 'Hello world'

    def test_add_child(self) -> None:
        """Test adding a child node."""
        parent = Node(type=NodeType.DOCUMENT)
        child = Node(type=NodeType.TEXT, content='Child')

        parent.add_child(child)

        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent == parent

    def test_add_child_with_position(self) -> None:
        """Test adding a child node at a specific position."""
        parent = Node(type=NodeType.DOCUMENT)
        child1 = Node(type=NodeType.TEXT, content='Child 1')
        child2 = Node(type=NodeType.TEXT, content='Child 2')
        child3 = Node(type=NodeType.TEXT, content='Child 3')

        parent.add_child(child1)
        parent.add_child(child3)
        parent.add_child(child2, position=1)

        assert len(parent.children) == 3
        assert parent.children[0] == child1
        assert parent.children[1] == child2
        assert parent.children[2] == child3

    def test_add_child_with_existing_parent(self) -> None:
        """Test adding a child that already has a parent."""
        parent1 = Node(type=NodeType.DOCUMENT)
        parent2 = Node(type=NodeType.DOCUMENT)
        child = Node(type=NodeType.TEXT, content='Child')

        parent1.add_child(child)
        assert len(parent1.children) == 1

        parent2.add_child(child)
        assert len(parent1.children) == 0
        assert len(parent2.children) == 1
        assert child.parent == parent2

    def test_remove_child(self) -> None:
        """Test removing a child node."""
        parent = Node(type=NodeType.DOCUMENT)
        child = Node(type=NodeType.TEXT, content='Child')

        parent.add_child(child)
        assert len(parent.children) == 1

        removed = parent.remove_child(child)
        assert len(parent.children) == 0
        assert removed == child
        assert child.parent is None

    def test_remove_nonexistent_child(self) -> None:
        """Test removing a child that doesn't exist."""
        parent = Node(type=NodeType.DOCUMENT)
        child = Node(type=NodeType.TEXT, content='Child')

        removed = parent.remove_child(child)
        assert removed is None

    def test_add_sibling(self) -> None:
        """Test adding a sibling node."""
        parent = Node(type=NodeType.DOCUMENT)
        child1 = Node(type=NodeType.TEXT, content='Child 1')
        child2 = Node(type=NodeType.TEXT, content='Child 2')

        parent.add_child(child1)
        child1.add_sibling_after(child2)

        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2
        assert child2.parent == parent

    def test_add_sibling_before(self) -> None:
        """Test adding a sibling node before the current node."""
        parent = Node(type=NodeType.DOCUMENT)
        child1 = Node(type=NodeType.TEXT, content='Child 1')
        child2 = Node(type=NodeType.TEXT, content='Child 2')

        parent.add_child(child1)
        child1.add_sibling_before(child2)

        assert len(parent.children) == 2
        assert parent.children[0] == child2
        assert parent.children[1] == child1

    def test_add_sibling_no_parent(self) -> None:
        """Test adding a sibling to a node without a parent."""
        node1 = Node(type=NodeType.TEXT, content='Node 1')
        node2 = Node(type=NodeType.TEXT, content='Node 2')

        result = node1.add_sibling_after(node2)
        assert result is False

    def test_add_sibling_with_existing_parent(self) -> None:
        """Test adding a sibling that already has a parent."""
        parent1 = Node(type=NodeType.DOCUMENT)
        parent2 = Node(type=NodeType.DOCUMENT)
        child1 = Node(type=NodeType.TEXT, content='Child 1')
        child2 = Node(type=NodeType.TEXT, content='Child 2')

        parent1.add_child(child1)
        parent2.add_child(child2)

        # Now child2 has a parent (parent2)
        child1.add_sibling_after(child2)

        # child2 should be moved from parent2 to parent1
        assert len(parent1.children) == 2
        assert len(parent2.children) == 0
        assert child2.parent == parent1

    def test_remove_sibling(self) -> None:
        """Test removing a sibling node."""
        parent = Node(type=NodeType.DOCUMENT)
        child1 = Node(type=NodeType.TEXT, content='Child 1')
        child2 = Node(type=NodeType.TEXT, content='Child 2')

        parent.add_child(child1)
        parent.add_child(child2)

        removed = child1.remove_sibling(child2)
        assert len(parent.children) == 1
        assert removed == child2
        assert child2.parent is None

    def test_remove_nonexistent_sibling(self) -> None:
        """Test removing a sibling that doesn't exist."""
        parent = Node(type=NodeType.DOCUMENT)
        child1 = Node(type=NodeType.TEXT, content='Child 1')
        child2 = Node(type=NodeType.TEXT, content='Child 2')

        parent.add_child(child1)

        removed = child1.remove_sibling(child2)
        assert removed is None

    def test_remove_sibling_no_parent(self) -> None:
        """Test removing a sibling when the node has no parent."""
        node1 = Node(type=NodeType.TEXT, content='Node 1')
        node2 = Node(type=NodeType.TEXT, content='Node 2')

        removed = node1.remove_sibling(node2)
        assert removed is None

    def test_add_parent(self) -> None:
        """Test adding a new parent between a node and its current parent."""
        original_parent = Node(type=NodeType.DOCUMENT)
        new_parent = Node(type=NodeType.LIST)
        child = Node(type=NodeType.TEXT, content='Child')

        original_parent.add_child(child)
        result = child.add_parent(new_parent)

        assert result is True
        assert len(original_parent.children) == 1
        assert original_parent.children[0] == new_parent
        assert len(new_parent.children) == 1
        assert new_parent.children[0] == child
        assert child.parent == new_parent
        assert new_parent.parent == original_parent

    def test_add_child_with_position_beyond_length(self) -> None:
        """Test adding a child at a position beyond the current length of children."""
        parent = Node(type=NodeType.DOCUMENT)
        child = Node(type=NodeType.TEXT, content='Child')

        # Position is beyond current length (0), should add at the end
        parent.add_child(child, position=5)

        assert len(parent.children) == 1
        assert parent.children[0] == child

    def test_add_parent_no_parent(self) -> None:
        """Test adding a parent to a node without a parent."""
        node = Node(type=NodeType.TEXT, content='Node')
        new_parent = Node(type=NodeType.LIST)

        result = node.add_parent(new_parent)
        assert result is False


class TestOutlineParser:
    """Tests for the OutlineParser class."""

    def test_parse_empty_document(self) -> None:
        """Test parsing an empty document."""
        text = ''
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 0

    def test_parse_text_only(self) -> None:
        """Test parsing a document with only text."""
        text = 'This is a paragraph.\n\nThis is another paragraph.'
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 1
        assert root.children[0].type == NodeType.TEXT
        assert root.children[0].content == text

    def test_parse_simple_list(self) -> None:
        """Test parsing a document with a simple list."""
        text = '- Item 1\n- Item 2\n- Item 3\n'
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 1

        list_node = root.children[0]
        assert list_node.type == NodeType.LIST
        assert len(list_node.children) == 3

        assert list_node.children[0].type == NodeType.LIST_ITEM
        assert list_node.children[0].content == '- Item 1'
        assert list_node.children[1].content == '- Item 2'
        assert list_node.children[2].content == '- Item 3'

    def test_parse_nested_list(self) -> None:
        """Test parsing a document with a nested list."""
        text = '- Item 1\n  - Nested 1\n  - Nested 2\n- Item 2\n'
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 1

        list_node = root.children[0]
        assert list_node.type == NodeType.LIST
        assert len(list_node.children) == 2

        item1 = list_node.children[0]
        assert item1.type == NodeType.LIST_ITEM
        assert item1.content == '- Item 1'
        assert len(item1.children) == 2

        # The parser creates separate list nodes for each nested item
        assert item1.children[0].type == NodeType.LIST
        assert len(item1.children[0].children) == 1
        assert item1.children[1].type == NodeType.LIST
        assert len(item1.children[1].children) == 1
        assert item1.children[0].children[0].content == '  - Nested 1'
        assert item1.children[1].children[0].content == '  - Nested 2'

        item2 = list_node.children[1]
        assert item2.type == NodeType.LIST_ITEM
        assert item2.content == '- Item 2'

    def test_parse_mixed_content(self) -> None:
        """Test parsing a document with mixed content."""
        text = 'This is a paragraph.\n\n- Item 1\n- Item 2\n\nAnother paragraph.'
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 3

        assert root.children[0].type == NodeType.TEXT
        assert root.children[0].content == 'This is a paragraph.\n\n'

        assert root.children[1].type == NodeType.LIST
        assert len(root.children[1].children) == 2

        assert root.children[2].type == NodeType.TEXT
        assert root.children[2].content == '\nAnother paragraph.'

    def test_parse_different_markers(self) -> None:
        """Test parsing a list with different markers."""
        text = '* Item 1\n+ Item 2\n- Item 3\n'
        root = OutlineParser.parse(text)

        list_node = root.children[0]
        assert list_node.children[0].content == '* Item 1'
        assert list_node.children[1].content == '+ Item 2'
        assert list_node.children[2].content == '- Item 3'

    def test_to_text_empty_document(self) -> None:
        """Test converting an empty document back to text."""
        root = Node(type=NodeType.DOCUMENT)
        text = OutlineParser.to_text(root)

        assert text == ''

    def test_to_text_simple_document(self) -> None:
        """Test converting a simple document back to text."""
        root = Node(type=NodeType.DOCUMENT)
        root.add_child(Node(type=NodeType.TEXT, content='This is a paragraph.\n\n'))

        list_node = Node(type=NodeType.LIST)
        root.add_child(list_node)

        list_node.add_child(Node(type=NodeType.LIST_ITEM, content='- Item 1'))
        list_node.add_child(Node(type=NodeType.LIST_ITEM, content='- Item 2'))

        root.add_child(Node(type=NodeType.TEXT, content='\nAnother paragraph.'))

        text = OutlineParser.to_text(root)
        expected = 'This is a paragraph.\n\n- Item 1\n- Item 2\n\nAnother paragraph.'
        assert text == expected

    def test_to_text_nested_list(self) -> None:
        """Test converting a document with a nested list back to text."""
        root = Node(type=NodeType.DOCUMENT)
        list_node = Node(type=NodeType.LIST)
        root.add_child(list_node)

        item1 = Node(type=NodeType.LIST_ITEM, content='- Item 1')
        list_node.add_child(item1)

        nested_list = Node(type=NodeType.LIST)
        item1.add_child(nested_list)

        nested_list.add_child(Node(type=NodeType.LIST_ITEM, content='  - Nested 1'))
        nested_list.add_child(Node(type=NodeType.LIST_ITEM, content='  - Nested 2'))

        list_node.add_child(Node(type=NodeType.LIST_ITEM, content='- Item 2'))

        text = OutlineParser.to_text(root)
        expected = '- Item 1\n  - Nested 1\n  - Nested 2\n- Item 2\n'
        assert text == expected

    def test_round_trip(self) -> None:
        """Test that parsing and then converting back to text preserves the original document."""
        original_texts = [
            '',
            'This is a paragraph.',
            '- Item 1\n- Item 2\n- Item 3',
            '- Item 1\n  - Nested 1\n  - Nested 2\n- Item 2',
            'This is a paragraph.\n\n- Item 1\n- Item 2\n\nAnother paragraph.',
            '* Item 1\n+ Item 2\n- Item 3',
            '# Heading\n\n- List item\n  - Nested item\n\nParagraph after list.',
        ]

        for original in original_texts:
            root = OutlineParser.parse(original)
            result = OutlineParser.to_text(root)
            # Strip any trailing newline for comparison
            assert result.rstrip('\n') == original.rstrip('\n')

    def test_to_text_list_item_without_newline(self) -> None:
        """Test converting a list item without a newline back to text."""
        root = Node(type=NodeType.DOCUMENT)
        list_node = Node(type=NodeType.LIST)
        root.add_child(list_node)

        # Create a list item without a newline at the end
        list_node.add_child(Node(type=NodeType.LIST_ITEM, content='- Item 1'))

        text = OutlineParser.to_text(root)
        assert text == '- Item 1\n'

    def test_to_text_unknown_node_type(self) -> None:
        """Test converting a node with an unknown type."""

        # Create a custom NodeType that's not handled in to_text
        class CustomNodeType(Enum):
            UNKNOWN = auto()

        # Create a node with the unknown type
        node = Node(type=CustomNodeType.UNKNOWN)

        # Should return empty string for unknown node types
        text = OutlineParser.to_text(node)
        assert text == ''

    def test_parse_list_with_multiple_indentation_levels(self) -> None:
        """Test parsing a list with multiple indentation levels."""
        text = '- Item 1\n  - Nested 1\n    - Deeply nested\n  - Nested 2\n- Item 2\n'
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 1

        list_node = root.children[0]
        assert list_node.type == NodeType.LIST
        assert len(list_node.children) == 2

        item1 = list_node.children[0]
        assert item1.type == NodeType.LIST_ITEM
        assert item1.content == '- Item 1'

        # Check the deeply nested structure
        nested1 = item1.children[0].children[0]  # First nested list item
        assert nested1.content == '  - Nested 1'
        assert len(nested1.children) == 1

        deeply_nested = nested1.children[0].children[0]
        assert deeply_nested.content == '    - Deeply nested'

    def test_parse_list_with_text_between_items(self) -> None:
        """Test parsing a list with text between list items."""
        text = '- Item 1\nSome text\n- Item 2\n'
        root = OutlineParser.parse(text)

        assert root.type == NodeType.DOCUMENT
        assert len(root.children) == 3

        # First list with one item
        assert root.children[0].type == NodeType.LIST
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].content == '- Item 1'

        # Text in between
        assert root.children[1].type == NodeType.TEXT
        assert root.children[1].content == 'Some text\n'

        # Second list with one item
        assert root.children[2].type == NodeType.LIST
        assert len(root.children[2].children) == 1
        assert root.children[2].children[0].content == '- Item 2'

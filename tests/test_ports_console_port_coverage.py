"""Tests for the ConsolePort abstract base class."""

from unittest.mock import Mock

import pytest

from prosemark.ports.console_port import ConsolePort


class ConcreteConsolePort(ConsolePort):
    """Concrete implementation of ConsolePort for testing."""

    def __init__(self) -> None:
        """Initialize with a list to capture printed messages."""
        self.messages: list[str] = []

    def print(self, msg: str) -> None:
        """Store messages in a list for testing."""
        self.messages.append(msg)


class TestConsolePort:
    """Test the ConsolePort abstract base class."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that ConsolePort cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ConsolePort()  # type: ignore[abstract]

    def test_concrete_implementation_works(self) -> None:
        """Test that concrete implementations work correctly."""
        console = ConcreteConsolePort()
        console.print('Test message')

        assert console.messages == ['Test message']

    def test_print_tree_default_implementation(self) -> None:
        """Test the default print_tree implementation."""
        console = ConcreteConsolePort()

        # Mock binder with project title and children
        mock_binder = Mock()
        mock_binder.project_title = 'Test Project'

        # Mock child item
        mock_child = Mock()
        mock_child.display_title = 'Child Item'
        mock_child.node_id = 'test-node-123'
        mock_child.children = []

        mock_binder.children = [mock_child]

        console.print_tree(mock_binder)

        assert len(console.messages) == 2
        assert console.messages[0] == 'Binder: Test Project'
        assert console.messages[1] == '- Child Item (test-node-123)'

    def test_print_tree_with_nested_items(self) -> None:
        """Test print_tree with nested items."""
        console = ConcreteConsolePort()

        # Mock deeply nested structure
        mock_grandchild = Mock()
        mock_grandchild.display_title = 'Grandchild Item'
        mock_grandchild.node_id = 'grandchild-456'
        mock_grandchild.children = []

        mock_child = Mock()
        mock_child.display_title = 'Child Item'
        mock_child.node_id = 'child-123'
        mock_child.children = [mock_grandchild]

        mock_binder = Mock()
        mock_binder.project_title = 'Nested Project'
        mock_binder.children = [mock_child]

        console.print_tree(mock_binder)

        assert len(console.messages) == 3
        assert console.messages[0] == 'Binder: Nested Project'
        assert console.messages[1] == '- Child Item (child-123)'
        assert console.messages[2] == '  - Grandchild Item (grandchild-456)'

    def test_print_tree_with_multiple_children(self) -> None:
        """Test print_tree with multiple children at same level."""
        console = ConcreteConsolePort()

        # Mock multiple children
        mock_child1 = Mock()
        mock_child1.display_title = 'First Child'
        mock_child1.node_id = 'child-001'
        mock_child1.children = []

        mock_child2 = Mock()
        mock_child2.display_title = 'Second Child'
        mock_child2.node_id = 'child-002'
        mock_child2.children = []

        mock_binder = Mock()
        mock_binder.project_title = 'Multi-Child Project'
        mock_binder.children = [mock_child1, mock_child2]

        console.print_tree(mock_binder)

        assert len(console.messages) == 3
        assert console.messages[0] == 'Binder: Multi-Child Project'
        assert console.messages[1] == '- First Child (child-001)'
        assert console.messages[2] == '- Second Child (child-002)'

    def test_print_tree_with_no_children(self) -> None:
        """Test print_tree with no children."""
        console = ConcreteConsolePort()

        mock_binder = Mock()
        mock_binder.project_title = 'Empty Project'
        mock_binder.children = []

        console.print_tree(mock_binder)

        assert len(console.messages) == 1
        assert console.messages[0] == 'Binder: Empty Project'

    def test_print_item_without_node_id(self) -> None:
        """Test _print_item with item that has no node_id."""
        console = ConcreteConsolePort()

        mock_item = Mock()
        mock_item.display_title = 'Title Only Item'
        mock_item.node_id = None
        mock_item.children = []

        console._print_item(mock_item, indent=0)

        assert len(console.messages) == 1
        assert console.messages[0] == '- Title Only Item'

    def test_print_item_with_node_id(self) -> None:
        """Test _print_item with item that has node_id."""
        console = ConcreteConsolePort()

        mock_item = Mock()
        mock_item.display_title = 'Item With ID'
        mock_item.node_id = 'item-789'
        mock_item.children = []

        console._print_item(mock_item, indent=0)

        assert len(console.messages) == 1
        assert console.messages[0] == '- Item With ID (item-789)'

    def test_print_item_with_indentation(self) -> None:
        """Test _print_item with different indentation levels."""
        console = ConcreteConsolePort()

        mock_item = Mock()
        mock_item.display_title = 'Indented Item'
        mock_item.node_id = 'indent-123'
        mock_item.children = []

        # Test different indentation levels
        console._print_item(mock_item, indent=0)
        console._print_item(mock_item, indent=1)
        console._print_item(mock_item, indent=2)

        assert len(console.messages) == 3
        assert console.messages[0] == '- Indented Item (indent-123)'
        assert console.messages[1] == '  - Indented Item (indent-123)'
        assert console.messages[2] == '    - Indented Item (indent-123)'

    def test_print_item_with_children(self) -> None:
        """Test _print_item recursively handles children."""
        console = ConcreteConsolePort()

        # Create child item
        mock_child = Mock()
        mock_child.display_title = 'Child of Parent'
        mock_child.node_id = 'child-999'
        mock_child.children = []

        # Create parent item
        mock_parent = Mock()
        mock_parent.display_title = 'Parent Item'
        mock_parent.node_id = 'parent-888'
        mock_parent.children = [mock_child]

        console._print_item(mock_parent, indent=0)

        assert len(console.messages) == 2
        assert console.messages[0] == '- Parent Item (parent-888)'
        assert console.messages[1] == '  - Child of Parent (child-999)'

    def test_print_info_default_implementation(self) -> None:
        """Test print_info default implementation (line 65)."""
        console = ConcreteConsolePort()
        console.print_info('Test info message')

        assert len(console.messages) == 1
        assert console.messages[0] == 'INFO: Test info message'

    def test_print_success_default_implementation(self) -> None:
        """Test print_success default implementation (line 74)."""
        console = ConcreteConsolePort()
        console.print_success('Operation completed')

        assert len(console.messages) == 1
        assert console.messages[0] == 'SUCCESS: Operation completed'

    def test_print_warning_default_implementation(self) -> None:
        """Test print_warning default implementation (line 83)."""
        console = ConcreteConsolePort()
        console.print_warning('Potential issue detected')

        assert len(console.messages) == 1
        assert console.messages[0] == 'WARNING: Potential issue detected'

    def test_print_error_default_implementation(self) -> None:
        """Test print_error default implementation (line 92)."""
        console = ConcreteConsolePort()
        console.print_error('Something went wrong')

        assert len(console.messages) == 1
        assert console.messages[0] == 'ERROR: Something went wrong'

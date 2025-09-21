"""Tests for FakeConsolePort adapter."""

import pytest

from prosemark.adapters.fake_console import FakeConsolePort
from prosemark.domain.models import Binder


class TestFakeConsolePort:
    """Test FakeConsolePort adapter methods."""

    @pytest.fixture
    def console(self) -> FakeConsolePort:
        """Create a fresh FakeConsolePort instance."""
        return FakeConsolePort()

    @pytest.fixture
    def sample_binder(self) -> Binder:
        """Create a sample binder for testing."""
        return Binder(roots=[])

    def test_print_tree_stores_binder_call(self, console: FakeConsolePort, sample_binder: Binder) -> None:
        """Test print_tree method stores binder for later verification."""
        # Act
        console.print_tree(sample_binder)

        # Assert
        tree_calls = console.get_tree_calls()
        assert len(tree_calls) == 1
        assert tree_calls[0] is sample_binder

    def test_get_tree_calls_returns_copy_of_stored_calls(self, console: FakeConsolePort, sample_binder: Binder) -> None:
        """Test get_tree_calls returns a copy of stored binder calls."""
        # Arrange
        console.print_tree(sample_binder)

        # Act
        tree_calls = console.get_tree_calls()

        # Assert - returns a copy (modifying returned list doesn't affect internal state)
        tree_calls.append(Binder(roots=[]))
        assert len(console.get_tree_calls()) == 1

    def test_tree_call_count_returns_number_of_calls(self, console: FakeConsolePort, sample_binder: Binder) -> None:
        """Test tree_call_count returns count of print_tree calls."""
        # Assert initial count
        assert console.tree_call_count() == 0

        # Act - make some calls
        console.print_tree(sample_binder)
        console.print_tree(sample_binder)

        # Assert count updated
        assert console.tree_call_count() == 2

    def test_multiple_tree_calls_stored_in_order(self, console: FakeConsolePort) -> None:
        """Test multiple print_tree calls are stored in correct order."""
        # Arrange
        binder1 = Binder(roots=[])
        binder2 = Binder(roots=[])

        # Act
        console.print_tree(binder1)
        console.print_tree(binder2)

        # Assert
        tree_calls = console.get_tree_calls()
        assert len(tree_calls) == 2
        assert tree_calls[0] is binder1
        assert tree_calls[1] is binder2
        assert console.tree_call_count() == 2

"""Tests for the IdGenerator abstract base class."""

from abc import ABC
from typing import get_type_hints
from unittest.mock import Mock

import pytest

from prosemark.domain.models import NodeId
from prosemark.ports.id_generator import IdGenerator


class TestIdGeneratorAbstractBaseClass:
    """Test the IdGenerator abstract base class behavior."""

    def test_cannot_instantiate_abstract_base_class(self) -> None:
        """Test that IdGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class IdGenerator"):
            IdGenerator()  # type: ignore[abstract]

    def test_inherits_from_abc(self) -> None:
        """Test that IdGenerator inherits from ABC."""
        assert issubclass(IdGenerator, ABC)

    def test_new_method_is_abstract(self) -> None:
        """Test that the new method is marked as abstract."""
        assert hasattr(IdGenerator.new, '__isabstractmethod__')
        assert IdGenerator.new.__isabstractmethod__ is True

    def test_minimal_interface_only_new_method(self) -> None:
        """Test that IdGenerator only defines the new method as abstract."""
        abstract_methods = IdGenerator.__abstractmethods__
        assert len(abstract_methods) == 1
        assert 'new' in abstract_methods


class TestIdGeneratorMethodSignature:
    """Test the method signatures of the IdGenerator class."""

    def test_new_method_signature(self) -> None:
        """Test that new method has correct signature."""
        import inspect

        sig = inspect.signature(IdGenerator.new)
        assert len(sig.parameters) == 1  # Only 'self'
        assert 'self' in sig.parameters

    def test_new_method_return_annotation(self) -> None:
        """Test that new method returns NodeId type annotation."""
        # Get type hints for the IdGenerator class, providing the module globals
        # so that forward references like 'NodeId' can be resolved
        import sys

        type_hints = get_type_hints(IdGenerator.new, globalns=sys.modules[NodeId.__module__].__dict__)
        assert 'return' in type_hints
        # The return type should be NodeId (resolved from forward reference)
        assert type_hints['return'] is NodeId


class TestConcreteImplementation:
    """Test that concrete implementations work correctly."""

    def test_concrete_implementation_can_be_instantiated(self) -> None:
        """Test that a concrete implementation can be instantiated."""

        class ConcreteIdGenerator(IdGenerator):
            def new(self) -> NodeId:
                return NodeId('0192f0c1-2345-7123-8abc-def012345678')

        generator = ConcreteIdGenerator()
        assert isinstance(generator, IdGenerator)
        node_id = generator.new()
        assert isinstance(node_id, NodeId)
        assert str(node_id) == '0192f0c1-2345-7123-8abc-def012345678'

    def test_concrete_implementation_without_new_fails(self) -> None:
        """Test that concrete class without new method cannot be instantiated."""

        class IncompleteIdGenerator(IdGenerator):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteIdGenerator()  # type: ignore[abstract]


class TestMockImplementation:
    """Test that IdGenerator ABC supports mocking for tests."""

    def test_mock_implementation_supports_testing(self) -> None:
        """Test that a mock IdGenerator implementation works for testing."""
        # Create a mock that implements the IdGenerator interface
        mock_generator = Mock(spec=IdGenerator)
        test_node_id = NodeId('0192f0c1-2345-7123-8abc-def012345678')
        mock_generator.new.return_value = test_node_id

        # Test that the mock works as expected
        result = mock_generator.new()
        assert result == test_node_id
        assert isinstance(result, NodeId)
        mock_generator.new.assert_called_once()

    def test_mock_enables_predictable_id_generation(self) -> None:
        """Test that mock IdGenerator enables predictable ID generation for tests."""
        # Create multiple predictable NodeIds for testing
        test_ids = [
            NodeId('0192f0c1-2345-7123-8abc-def012345678'),
            NodeId('0192f0c2-3456-7234-9cde-f123456789ab'),
            NodeId('0192f0c3-4567-7345-acef-23456789abcd'),
        ]

        mock_generator = Mock(spec=IdGenerator)
        mock_generator.new.side_effect = test_ids

        # Test that we get predictable, sequential IDs
        for expected_id in test_ids:
            result = mock_generator.new()
            assert result == expected_id
            assert isinstance(result, NodeId)

        assert mock_generator.new.call_count == len(test_ids)

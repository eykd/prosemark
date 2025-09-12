"""Tests for the IdGenerator abstract base class."""

from abc import ABC
from typing import Any
from unittest.mock import Mock

import pytest

from prosemark.ports.id_generator import IdGenerator, IdGeneratorProtocol


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
        """Test that new method has Any return type annotation."""
        assert IdGenerator.new.__annotations__['return'] is Any


class TestConcreteImplementation:
    """Test that concrete implementations work correctly."""

    def test_concrete_implementation_can_be_instantiated(self) -> None:
        """Test that a concrete implementation can be instantiated."""

        class ConcreteIdGenerator(IdGenerator):
            def new(self) -> str:
                return 'test-id'

        generator = ConcreteIdGenerator()
        assert isinstance(generator, IdGenerator)
        assert generator.new() == 'test-id'

    def test_concrete_implementation_without_new_fails(self) -> None:
        """Test that concrete class without new method cannot be instantiated."""

        class IncompleteIdGenerator(IdGenerator):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteIdGenerator()  # type: ignore[abstract]


class TestIdGeneratorProtocol:
    """Test the IdGeneratorProtocol runtime checkable protocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """Test that IdGeneratorProtocol is runtime checkable."""
        assert hasattr(IdGeneratorProtocol, '__instancecheck__')

    def test_mock_satisfies_protocol(self) -> None:
        """Test that a mock with new method satisfies the protocol."""
        mock_generator = Mock()
        mock_generator.new = Mock(return_value='mock-id')

        assert isinstance(mock_generator, IdGeneratorProtocol)
        assert mock_generator.new() == 'mock-id'

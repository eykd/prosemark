"""Tests for DailyRepo abstract base class."""

from unittest.mock import Mock

import pytest

from prosemark.ports.daily_repo import DailyRepo


class TestDailyRepo:
    """Test suite for DailyRepo abstract base class."""

    def test_daily_repo_write_freeform_signature(self) -> None:
        """Test that DailyRepo defines write_freeform with correct signature."""
        # Arrange: Check method exists on abstract base class
        assert hasattr(DailyRepo, 'write_freeform')

        # Act: Get the method
        method = DailyRepo.write_freeform

        assert hasattr(method, '__isabstractmethod__')
        assert method.__isabstractmethod__ is True

        # Assert: Check annotations
        annotations = method.__annotations__
        assert 'title' in annotations
        assert annotations['title'] == str | None
        assert 'return' in annotations
        assert annotations['return'] is str

    def test_daily_repo_accepts_optional_title(self) -> None:
        """Test that write_freeform accepts optional title parameter."""

        # Arrange: Create concrete implementation for testing
        class TestRepo(DailyRepo):
            def write_freeform(self, title: str | None = None) -> str:
                return 'test.md'

        repo = TestRepo()

        # Act & Assert: Both calls should work
        assert repo.write_freeform() == 'test.md'
        assert repo.write_freeform(None) == 'test.md'
        assert repo.write_freeform('Test Title') == 'test.md'

    def test_daily_repo_returns_filename(self) -> None:
        """Test that write_freeform returns a string filename."""

        # Arrange: Create concrete implementation
        class TestRepo(DailyRepo):
            def write_freeform(self, title: str | None = None) -> str:
                return '20250911T1230_abc123.md'

        repo = TestRepo()

        # Act
        result = repo.write_freeform()

        # Assert: Returns string
        assert isinstance(result, str)
        assert result.endswith('.md')

    def test_daily_repo_supports_mocking(self) -> None:
        """Test that DailyRepo can be mocked for dependency injection."""
        # Arrange: Create mock
        mock_repo = Mock(spec=DailyRepo)
        mock_repo.write_freeform.return_value = 'mock_file.md'

        # Act: Use mock as if it were a DailyRepo
        def application_layer_function(repo: DailyRepo) -> str:
            return repo.write_freeform('Test Title')

        result = application_layer_function(mock_repo)

        # Assert: Mock works correctly
        assert result == 'mock_file.md'
        mock_repo.write_freeform.assert_called_once_with('Test Title')

    def test_daily_repo_is_abstract_base_class(self) -> None:
        """Test that DailyRepo cannot be instantiated directly."""
        # Act & Assert: Cannot instantiate abstract class
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            DailyRepo()  # type: ignore[abstract]

    def test_daily_repo_requires_implementation(self) -> None:
        """Test that concrete classes must implement write_freeform."""

        # Arrange: Create incomplete implementation
        class IncompleteRepo(DailyRepo):
            pass

        # Act & Assert: Cannot instantiate without implementing abstract method
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteRepo()  # type: ignore[abstract]

    def test_daily_repo_inheritance(self) -> None:
        """Test that concrete implementations inherit from DailyRepo."""

        # Arrange: Create concrete implementation
        class ConcreteRepo(DailyRepo):
            def write_freeform(self, title: str | None = None) -> str:
                return 'concrete.md'

        repo = ConcreteRepo()

        # Assert: Instance check works
        assert isinstance(repo, DailyRepo)
        assert issubclass(ConcreteRepo, DailyRepo)

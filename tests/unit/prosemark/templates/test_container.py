"""Unit tests for TemplatesContainer."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from prosemark.templates.container import TemplatesContainer
from prosemark.templates.ports.template_repository_port import TemplateRepositoryPort
from prosemark.templates.ports.template_validator_port import TemplateValidatorPort
from prosemark.templates.ports.user_prompter_port import UserPrompterPort


class TestTemplatesContainer:
    """Test TemplatesContainer dependency injection."""

    @pytest.fixture
    def templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()
        return templates_dir

    def test_container_initialization(self, templates_dir: Path) -> None:
        """Test container initialization with templates root."""
        container = TemplatesContainer(templates_dir)

        assert container._templates_root == templates_dir
        assert container._repository is None
        assert container._validator is None
        assert container._prompter is None

    def test_repository_lazy_loading(self, templates_dir: Path) -> None:
        """Test repository is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the repository
        repo1 = container.repository
        assert repo1 is not None

        # Second access returns same instance
        repo2 = container.repository
        assert repo1 is repo2

    def test_validator_lazy_loading(self, templates_dir: Path) -> None:
        """Test validator is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the validator
        validator1 = container.validator
        assert validator1 is not None

        # Second access returns same instance
        validator2 = container.validator
        assert validator1 is validator2

    def test_prompter_lazy_loading(self, templates_dir: Path) -> None:
        """Test prompter is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the prompter
        prompter1 = container.prompter
        assert prompter1 is not None

        # Second access returns same instance
        prompter2 = container.prompter
        assert prompter1 is prompter2

    def test_template_service_lazy_loading(self, templates_dir: Path) -> None:
        """Test template service is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the service
        service1 = container.template_service
        assert service1 is not None

        # Second access returns same instance
        service2 = container.template_service
        assert service1 is service2

    def test_placeholder_service_lazy_loading(self, templates_dir: Path) -> None:
        """Test placeholder service is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the service
        service1 = container.placeholder_service
        assert service1 is not None

        # Second access returns same instance
        service2 = container.placeholder_service
        assert service1 is service2

    def test_create_from_template_use_case_lazy_loading(self, templates_dir: Path) -> None:
        """Test create from template use case is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the use case
        use_case1 = container.create_from_template_use_case
        assert use_case1 is not None

        # Second access returns same instance
        use_case2 = container.create_from_template_use_case
        assert use_case1 is use_case2

    def test_list_templates_use_case_lazy_loading(self, templates_dir: Path) -> None:
        """Test list templates use case is lazy-loaded."""
        container = TemplatesContainer(templates_dir)

        # First access creates the use case
        use_case1 = container.list_templates_use_case
        assert use_case1 is not None

        # Second access returns same instance
        use_case2 = container.list_templates_use_case
        assert use_case1 is use_case2

    def test_configure_custom_repository(self, templates_dir: Path) -> None:
        """Test configuring custom repository (covers lines 106-110)."""
        container = TemplatesContainer(templates_dir)

        # Create some services to ensure they get reset
        _ = container.template_service
        _ = container.create_from_template_use_case
        _ = container.list_templates_use_case

        # Configure custom repository
        custom_repo = Mock(spec=TemplateRepositoryPort)
        container.configure_custom_repository(custom_repo)

        # Verify repository is set
        assert container._repository is custom_repo

        # Verify dependent services are reset
        assert container._template_service is None
        assert container._create_from_template_use_case is None
        assert container._list_templates_use_case is None

    def test_configure_custom_validator(self, templates_dir: Path) -> None:
        """Test configuring custom validator (covers lines 119-123)."""
        container = TemplatesContainer(templates_dir)

        # Create some services to ensure they get reset
        _ = container.template_service
        _ = container.create_from_template_use_case
        _ = container.list_templates_use_case

        # Configure custom validator
        custom_validator = Mock(spec=TemplateValidatorPort)
        container.configure_custom_validator(custom_validator)

        # Verify validator is set
        assert container._validator is custom_validator

        # Verify dependent services are reset
        assert container._template_service is None
        assert container._create_from_template_use_case is None
        assert container._list_templates_use_case is None

    def test_configure_custom_prompter(self, templates_dir: Path) -> None:
        """Test configuring custom prompter (covers lines 132-136)."""
        container = TemplatesContainer(templates_dir)

        # Create some services to ensure they get reset
        _ = container.template_service
        _ = container.create_from_template_use_case
        _ = container.list_templates_use_case

        # Configure custom prompter
        custom_prompter = Mock(spec=UserPrompterPort)
        container.configure_custom_prompter(custom_prompter)

        # Verify prompter is set
        assert container._prompter is custom_prompter

        # Verify dependent services are reset
        assert container._template_service is None
        assert container._create_from_template_use_case is None
        assert container._list_templates_use_case is None

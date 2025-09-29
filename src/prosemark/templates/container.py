"""Dependency injection container for template module."""

from pathlib import Path

from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
from prosemark.templates.adapters.file_template_repository import FileTemplateRepository
from prosemark.templates.adapters.prosemark_template_validator import ProsemarkTemplateValidator
from prosemark.templates.application.use_cases.create_from_template_use_case import (
    CreateFromTemplateUseCase,
)
from prosemark.templates.application.use_cases.list_templates_use_case import (
    ListTemplatesUseCase,
)
from prosemark.templates.domain.services.placeholder_service import PlaceholderService
from prosemark.templates.domain.services.template_service import TemplateService
from prosemark.templates.ports.template_repository_port import TemplateRepositoryPort
from prosemark.templates.ports.template_validator_port import TemplateValidatorPort
from prosemark.templates.ports.user_prompter_port import UserPrompterPort


class TemplatesContainer:
    """Dependency injection container for templates module."""

    def __init__(self, templates_root: Path | str) -> None:
        """Initialize container with templates root directory.

        Args:
            templates_root: Path to the root templates directory

        """
        self._templates_root = Path(templates_root)

        # Adapters - lazy-loaded singletons
        self._repository: TemplateRepositoryPort | None = None
        self._validator: TemplateValidatorPort | None = None
        self._prompter: UserPrompterPort | None = None

        # Services - lazy-loaded singletons
        self._template_service: TemplateService | None = None
        self._placeholder_service: PlaceholderService | None = None

        # Use cases (singletons)
        self._create_from_template_use_case: CreateFromTemplateUseCase | None = None
        self._list_templates_use_case: ListTemplatesUseCase | None = None

    @property
    def repository(self) -> TemplateRepositoryPort:
        """Get template repository instance."""
        if self._repository is None:
            self._repository = FileTemplateRepository(self._templates_root)
        return self._repository

    @property
    def validator(self) -> TemplateValidatorPort:
        """Get template validator instance."""
        if self._validator is None:
            self._validator = ProsemarkTemplateValidator()
        return self._validator

    @property
    def prompter(self) -> UserPrompterPort:
        """Get user prompter instance."""
        if self._prompter is None:
            self._prompter = CLIUserPrompter()
        return self._prompter

    @property
    def template_service(self) -> TemplateService:
        """Get template service instance."""
        if self._template_service is None:
            self._template_service = TemplateService(
                repository=self.repository,
                validator=self.validator,
                prompter=self.prompter,
            )
        return self._template_service

    @property
    def placeholder_service(self) -> PlaceholderService:
        """Get placeholder service instance."""
        if self._placeholder_service is None:
            self._placeholder_service = PlaceholderService()
        return self._placeholder_service

    @property
    def create_from_template_use_case(self) -> CreateFromTemplateUseCase:
        """Get create from template use case instance."""
        if self._create_from_template_use_case is None:
            self._create_from_template_use_case = CreateFromTemplateUseCase(template_service=self.template_service)
        return self._create_from_template_use_case

    @property
    def list_templates_use_case(self) -> ListTemplatesUseCase:
        """Get list templates use case instance."""
        if self._list_templates_use_case is None:
            self._list_templates_use_case = ListTemplatesUseCase(template_service=self.template_service)
        return self._list_templates_use_case

    def configure_custom_repository(self, repository: TemplateRepositoryPort) -> None:
        """Configure a custom template repository.

        Args:
            repository: Custom repository implementation

        """
        self._repository = repository
        # Reset dependent services
        self._template_service = None
        self._create_from_template_use_case = None
        self._list_templates_use_case = None

    def configure_custom_validator(self, validator: TemplateValidatorPort) -> None:
        """Configure a custom template validator.

        Args:
            validator: Custom validator implementation

        """
        self._validator = validator
        # Reset dependent services
        self._template_service = None
        self._create_from_template_use_case = None
        self._list_templates_use_case = None

    def configure_custom_prompter(self, prompter: UserPrompterPort) -> None:
        """Configure a custom user prompter.

        Args:
            prompter: Custom prompter implementation

        """
        self._prompter = prompter
        # Reset dependent services
        self._template_service = None
        self._create_from_template_use_case = None
        self._list_templates_use_case = None

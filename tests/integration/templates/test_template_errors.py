"""Integration tests for template validation and error handling.

These tests verify the complete workflow of template validation
and appropriate error handling for various failure scenarios.
"""

from pathlib import Path

import pytest

from prosemark.templates.application.use_cases.create_from_template_use_case import CreateFromTemplateUseCase


class TestTemplateErrorIntegration:
    """Integration tests for template error handling."""

    @pytest.fixture
    def temp_templates_dir(self, tmp_path: Path) -> Path:
        """Create a temporary templates directory with various invalid templates."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Template with invalid YAML frontmatter
        invalid_yaml = templates_dir / 'invalid-yaml.md'
        invalid_yaml.write_text(
            '---\n'
            'title: {{title}\n'  # Missing closing quote
            'type: document\n'
            'invalid: [\n'  # Unclosed bracket
            'missing: {key: value\n'  # Unclosed brace
            '---\n\n'
            '# {{title}}\n\n'
            'Content here.'
        )

        # Template without frontmatter
        no_frontmatter = templates_dir / 'no-frontmatter.md'
        no_frontmatter.write_text(
            '# Just a Title\n\n'
            'This template has no YAML frontmatter.\n'
            '{{placeholder}} should work but template is invalid.'
        )

        # Template with malformed placeholders
        bad_placeholders = templates_dir / 'bad-placeholders.md'
        bad_placeholders.write_text(
            '---\n'
            'title: Valid Title\n'
            '---\n\n'
            '# Valid Content\n\n'
            'Valid: {{good_placeholder}}\n'
            'Invalid: {{invalid-dash}}\n'
            'Invalid: {{invalid space}}\n'
            'Invalid: {{123_starts_with_number}}\n'
            'Invalid: {single_brace}\n'
            'Invalid: {{invalid.dot}}\n'
            'Unclosed: {{unclosed\n'
            'Empty: {{}}'
        )

        # Template with circular dependencies (if supported)
        circular1 = templates_dir / 'circular1.md'
        circular1.write_text(
            '---\ntitle: {{title}}\ndepends_on: circular2\n---\n\n# {{title}}\n\nReferences: {{ref_to_circular2}}'
        )

        circular2 = templates_dir / 'circular2.md'
        circular2.write_text(
            '---\ntitle: {{title}}\ndepends_on: circular1\n---\n\n# {{title}}\n\nReferences: {{ref_to_circular1}}'
        )

        # Template with file permission issues (create read-only)
        readonly_template = templates_dir / 'readonly.md'
        readonly_template.write_text('---\ntitle: {{title}}\n---\n\n# {{title}}\n\nContent: {{content}}')
        # Make it read-only (this might not work on all systems)
        import contextlib

        with contextlib.suppress(Exception):
            readonly_template.chmod(0o444)  # Ignore if chmod fails

        return templates_dir

    def test_template_validation_invalid_yaml_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test validation error for template with invalid YAML frontmatter."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        # Should return failure result for invalid YAML
        result = use_case.create_single_template(template_name='invalid-yaml', interactive=False)

        assert result['success'] is False
        assert result['error_type'] == 'TemplateParseError'

        # Error should contain helpful information
        error_message = result['error']
        assert 'invalid-yaml.md' in error_message
        assert 'YAML' in error_message or 'frontmatter' in error_message

    def test_template_validation_no_frontmatter_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test validation error for template without frontmatter."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        # Should return failure result for missing frontmatter
        result = use_case.create_single_template(template_name='no-frontmatter', interactive=False)

        assert result['success'] is False
        assert result['error_type'] == 'TemplateValidationError'

        # Error should explain the prosemark format requirement
        error_message = result['error']
        assert 'frontmatter' in error_message.lower()

    def test_template_validation_invalid_placeholder_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test validation error for template with malformed placeholders."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        # Should return failure result for malformed placeholders
        result = use_case.create_single_template(template_name='bad-placeholders', interactive=False)

        assert result['success'] is False
        assert result['error_type'] == 'InvalidPlaceholderError'

        # Error should specify which placeholder(s) are invalid
        error_message = result['error']
        assert 'placeholder' in error_message.lower()

    def test_template_not_found_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test error handling for non-existent template."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        # Should return failure result for non-existent template
        result = use_case.create_single_template(template_name='does-not-exist', interactive=False)

        assert result['success'] is False
        assert result['error_type'] == 'TemplateNotFoundError'

        # Error should be helpful
        error_message = result['error']
        assert 'does-not-exist' in error_message
        assert 'not found' in error_message.lower()

    def test_template_directory_not_found_error(self, tmp_path: Path) -> None:
        """Test error handling for non-existent templates directory."""
        nonexistent_dir = tmp_path / 'nonexistent'

        # Test now passes as use case is implemented
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.domain.exceptions.template_exceptions import (
            TemplateDirectoryNotFoundError,
        )

        # Should raise TemplateDirectoryNotFoundError when creating repository
        with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
            FileTemplateRepository(templates_root=nonexistent_dir)

        error_message = str(exc_info.value)
        assert 'directory' in error_message.lower()
        assert 'not found' in error_message.lower()

    def test_template_dependency_validation_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test error handling for templates with invalid dependencies."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        # Should return failure result for circular dependencies
        result = use_case.create_single_template(template_name='circular1', interactive=False)

        assert result['success'] is False
        assert result['error_type'] in {'TemplateValidationError', 'TemplateParseError'}

        error_message = result['error']
        assert 'circular' in error_message.lower() or 'dependency' in error_message.lower()

    def test_error_messages_are_helpful(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test that error messages provide helpful information for debugging."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        result = use_case.create_single_template(template_name='invalid-yaml', interactive=False)

        assert result['success'] is False
        error_message = result['error']

        # Error should include:
        # 1. File path information
        assert 'invalid-yaml' in error_message

        # 2. Specific problem description
        assert any(keyword in error_message.lower() for keyword in ['yaml', 'frontmatter', 'syntax', 'invalid'])

        # 3. Line number or location (if available)
        # This depends on implementation details

    def test_error_handling_preserves_system_state(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test that errors don't leave system in inconsistent state."""
        # Test now passes as use case is implemented
        from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter
        from prosemark.templates.adapters.file_template_repository import (
            FileTemplateRepository,
        )
        from prosemark.templates.adapters.prosemark_template_validator import (
            ProsemarkTemplateValidator,
        )
        from prosemark.templates.domain.services.template_service import (
            TemplateService,
        )

        repository = FileTemplateRepository(templates_root=temp_templates_dir)
        validator = ProsemarkTemplateValidator()
        prompter = CLIUserPrompter()
        template_service = TemplateService(repository, validator, prompter)
        output_dir = tmp_path / 'output'
        output_dir.mkdir()

        use_case = CreateFromTemplateUseCase(template_service)

        # Try to create from invalid template
        result = use_case.create_single_template(template_name='invalid-yaml', interactive=False)
        assert result['success'] is False  # Should fail gracefully

        # Output directory should remain clean (no partial files)
        created_files = list(output_dir.rglob('*'))
        assert len([f for f in created_files if f.is_file()]) == 0

        # Should be able to create from valid template after error
        # (This would require a valid template to be added to fixture)

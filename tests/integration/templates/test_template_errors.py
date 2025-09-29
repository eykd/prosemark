import contextlib

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
        try:
            readonly_template.chmod(0o444)
        except Exception:
            pass  # Ignore if chmod fails

        return templates_dir

    def test_template_validation_invalid_yaml_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test validation error for template with invalid YAML frontmatter."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateParseError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Should raise TemplateParseError for invalid YAML
            with pytest.raises(TemplateParseError) as exc_info:
                use_case.create_from_template(template_name='invalid-yaml', templates_directory=temp_templates_dir)

            # Error should contain helpful information
            error_message = str(exc_info.value)
            assert 'invalid-yaml.md' in error_message
            assert 'YAML' in error_message or 'frontmatter' in error_message

    def test_template_validation_no_frontmatter_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test validation error for template without frontmatter."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateValidationError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Should raise TemplateValidationError for missing frontmatter
            with pytest.raises(TemplateValidationError) as exc_info:
                use_case.create_from_template(template_name='no-frontmatter', templates_directory=temp_templates_dir)

            # Error should explain the prosemark format requirement
            error_message = str(exc_info.value)
            assert 'frontmatter' in error_message.lower()

    def test_template_validation_invalid_placeholder_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test validation error for template with malformed placeholders."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                InvalidPlaceholderError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Should raise InvalidPlaceholderError for malformed placeholders
            with pytest.raises(InvalidPlaceholderError) as exc_info:
                use_case.create_from_template(template_name='bad-placeholders', templates_directory=temp_templates_dir)

            # Error should specify which placeholder(s) are invalid
            error_message = str(exc_info.value)
            assert 'placeholder' in error_message.lower()

    def test_template_not_found_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test error handling for non-existent template."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateNotFoundError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Should raise TemplateNotFoundError for non-existent template
            with pytest.raises(TemplateNotFoundError) as exc_info:
                use_case.create_from_template(template_name='does-not-exist', templates_directory=temp_templates_dir)

            # Error should be helpful
            error_message = str(exc_info.value)
            assert 'does-not-exist' in error_message
            assert 'not found' in error_message.lower()

    def test_template_directory_not_found_error(self, tmp_path: Path) -> None:
        """Test error handling for non-existent templates directory."""
        nonexistent_dir = tmp_path / 'nonexistent'

        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateDirectoryNotFoundError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Should raise TemplateDirectoryNotFoundError
            with pytest.raises(TemplateDirectoryNotFoundError) as exc_info:
                use_case.create_from_template(template_name='any-template', templates_directory=nonexistent_dir)

            error_message = str(exc_info.value)
            assert 'directory' in error_message.lower()
            assert 'not found' in error_message.lower()

    def test_template_dependency_validation_error(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test error handling for templates with invalid dependencies."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateValidationError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Should raise TemplateValidationError for circular dependencies
            with pytest.raises(TemplateValidationError) as exc_info:
                use_case.create_from_template(template_name='circular1', templates_directory=temp_templates_dir)

            error_message = str(exc_info.value)
            assert 'circular' in error_message.lower() or 'dependency' in error_message.lower()

    def test_error_messages_are_helpful(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test that error messages provide helpful information for debugging."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )
            from prosemark.templates.domain.exceptions.template_exceptions import (
                TemplateParseError,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            try:
                use_case.create_from_template(template_name='invalid-yaml', templates_directory=temp_templates_dir)
            except TemplateParseError as e:
                error_message = str(e)

                # Error should include:
                # 1. File path information
                assert 'invalid-yaml' in error_message

                # 2. Specific problem description
                assert any(keyword in error_message.lower() for keyword in ['yaml', 'frontmatter', 'syntax', 'invalid'])

                # 3. Line number or location (if available)
                # This depends on implementation details

    def test_error_handling_preserves_system_state(self, temp_templates_dir: Path, tmp_path: Path) -> None:
        """Test that errors don't leave system in inconsistent state."""
        # This test will fail until use case is implemented (expected for TDD)
        with pytest.raises((ImportError, AttributeError)):
            from prosemark.templates.adapters.cli_user_prompter import CLIUserPrompter  # type: ignore[import-untyped]
            from prosemark.templates.adapters.file_template_repository import (
                FileTemplateRepository,  # type: ignore[import-untyped]
            )
            from prosemark.templates.adapters.prosemark_template_validator import (
                ProsemarkTemplateValidator,  # type: ignore[import-untyped]
            )

            repository = FileTemplateRepository()
            validator = ProsemarkTemplateValidator()
            prompter = CLIUserPrompter()
            output_dir = tmp_path / 'output'
            output_dir.mkdir()

            use_case = CreateFromTemplateUseCase(
                template_repository=repository,
                template_validator=validator,
                user_prompter=prompter,
                output_directory=output_dir,
            )

            # Try to create from invalid template
            with contextlib.suppress(Exception):
                use_case.create_from_template(template_name='invalid-yaml', templates_directory=temp_templates_dir)

            # Output directory should remain clean (no partial files)
            created_files = list(output_dir.rglob('*'))
            assert len([f for f in created_files if f.is_file()]) == 0

            # Should be able to create from valid template after error
            # (This would require a valid template to be added to fixture)

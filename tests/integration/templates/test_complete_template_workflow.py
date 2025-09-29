from typing import Any

"""Integration test for complete template workflow."""

from pathlib import Path

from prosemark.templates.container import TemplatesContainer


class TestCompleteTemplateWorkflow:
    """Test complete template workflow with real file system."""

    def test_single_template_workflow(self, tmp_path: Path) -> None:
        """Test creating content from a single template."""
        # Create templates directory
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create test template
        template_content = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Unknown"
---

# {{title}}

Written by: {{author}}

{{content}}
"""
        template_file = templates_dir / 'test-template.md'
        template_file.write_text(template_content)

        # Initialize container
        container = TemplatesContainer(templates_dir)

        # Mock user prompter to simulate user input
        class MockPrompter:
            def prompt_for_placeholder_value(self, placeholder: Any) -> str:
                if placeholder.name == 'title':
                    return 'Test Title'
                if placeholder.name == 'author':
                    return 'Test Author'  # Provide explicit value for author
                if placeholder.name == 'content':
                    return 'This is test content.'
                return placeholder.get_effective_value()

        container.configure_custom_prompter(MockPrompter())

        # Use the create from template use case
        use_case = container.create_from_template_use_case
        result = use_case.create_single_template('test-template')

        # Verify result
        assert result['success'] is True, f'Expected success, got error: {result.get("error", "Unknown")}'
        assert result['template_name'] == 'test-template'
        assert result['template_type'] == 'single'

        content = result['content']
        assert '# Test Title' in content
        assert 'Written by: Test Author' in content  # Explicit value provided
        assert 'This is test content.' in content

    def test_directory_template_workflow(self, tmp_path: Path) -> None:
        """Test creating content from a directory template."""
        # Create templates directory structure
        templates_dir = tmp_path / 'templates'
        project_dir = templates_dir / 'project-setup'
        project_dir.mkdir(parents=True)

        # Create template files
        overview_content = """---
title: "{{project_name}} - Overview"
lead: "{{project_lead}}"
---

# {{project_name}} - Project Overview

**Lead:** {{project_lead}}

## Objective

{{objective}}
"""
        (project_dir / 'overview.md').write_text(overview_content)

        readme_content = """---
title: "{{project_name}} - README"
---

# {{project_name}}

{{description}}

**Maintainer:** {{project_lead}}
"""
        (project_dir / 'readme.md').write_text(readme_content)

        # Initialize container
        container = TemplatesContainer(templates_dir)

        # Mock user prompter
        class MockPrompter:
            def prompt_for_placeholder_value(self, placeholder: Any) -> str:
                values = {
                    'project_name': 'My Project',
                    'project_lead': 'John Doe',
                    'objective': 'Build something awesome',
                    'description': 'A great project',
                }
                return values.get(placeholder.name, placeholder.get_effective_value())

        container.configure_custom_prompter(MockPrompter())

        # Use the create from template use case
        use_case = container.create_from_template_use_case
        result = use_case.create_directory_template('project-setup')

        # Verify result
        assert result['success'] is True
        assert result['template_name'] == 'project-setup'
        assert result['template_type'] == 'directory'
        assert result['file_count'] == 2

        content_map = result['content']
        assert len(content_map) == 2

        # Check overview content
        overview_content = content_map['overview.md']
        assert '# My Project - Project Overview' in overview_content
        assert '**Lead:** John Doe' in overview_content
        assert 'Build something awesome' in overview_content

        # Check readme content
        readme_content = content_map['readme.md']
        assert '# My Project' in readme_content
        assert 'A great project' in readme_content
        assert '**Maintainer:** John Doe' in readme_content

    def test_list_templates_workflow(self, tmp_path: Path) -> None:
        """Test listing available templates."""
        # Create templates directory
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create single templates
        (templates_dir / 'template1.md').write_text('---\ntitle: test\n---\n# Test')
        (templates_dir / 'template2.md').write_text('---\ntitle: test\n---\n# Test')

        # Create directory template
        project_dir = templates_dir / 'project'
        project_dir.mkdir()
        (project_dir / 'file1.md').write_text('---\ntitle: test\n---\n# Test')

        # Initialize container
        container = TemplatesContainer(templates_dir)

        # Use the list templates use case
        use_case = container.list_templates_use_case
        result = use_case.list_all_templates()

        # Verify result
        assert result['success'] is True
        assert result['total_templates'] == 3

        # Check single templates
        single_templates = result['single_templates']
        assert single_templates['count'] == 2
        assert set(single_templates['names']) == {'template1', 'template2'}

        # Check directory templates
        directory_templates = result['directory_templates']
        assert directory_templates['count'] == 1
        assert directory_templates['names'] == ['project']

    def test_template_not_found_error(self, tmp_path: Path) -> None:
        """Test error handling when template is not found."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        container = TemplatesContainer(templates_dir)
        use_case = container.create_from_template_use_case

        result = use_case.create_single_template('nonexistent-template')

        assert result['success'] is False
        assert result['template_name'] == 'nonexistent-template'
        assert 'error' in result
        assert 'TemplateNotFoundError' in result['error_type']

    def test_template_validation_workflow(self, tmp_path: Path) -> None:
        """Test template validation workflow."""
        # Create templates directory
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        # Create valid template
        valid_template = """---
title: "{{title}}"
---

# {{title}}

Valid content here.
"""
        (templates_dir / 'valid.md').write_text(valid_template)

        # Create invalid template (no frontmatter)
        invalid_template = '# No Frontmatter\n\nThis is invalid.'
        (templates_dir / 'invalid.md').write_text(invalid_template)

        container = TemplatesContainer(templates_dir)
        use_case = container.create_from_template_use_case

        # Mock prompter
        class MockPrompter:
            def prompt_for_placeholder_value(self, placeholder: Any) -> str:
                return 'Test Title'

        container.configure_custom_prompter(MockPrompter())

        # Test valid template
        result = use_case.create_single_template('valid')
        assert result['success'] is True

        # Test invalid template
        result = use_case.create_single_template('invalid')
        assert result['success'] is False
        assert 'TemplateValidationError' in result['error_type']

    def test_placeholder_consistency_in_directory(self, tmp_path: Path) -> None:
        """Test placeholder consistency validation in directory templates."""
        templates_dir = tmp_path / 'templates'
        project_dir = templates_dir / 'inconsistent-project'
        project_dir.mkdir(parents=True)

        # Create templates with inconsistent placeholder requirements
        template1 = """---
title: "{{project_name}}"
project_name_default: "Default Project"
---

# {{project_name}}

Optional placeholder usage.
"""
        (project_dir / 'template1.md').write_text(template1)

        template2 = """---
title: "{{project_name}}"
---

# {{project_name}}

Required placeholder usage.
"""
        (project_dir / 'template2.md').write_text(template2)

        container = TemplatesContainer(templates_dir)
        use_case = container.create_from_template_use_case

        # This should fail due to inconsistent placeholder requirements
        result = use_case.create_directory_template('inconsistent-project')
        assert result['success'] is False
        assert 'TemplateValidationError' in result['error_type']

    def test_non_interactive_mode(self, tmp_path: Path) -> None:
        """Test non-interactive mode with predefined values."""
        templates_dir = tmp_path / 'templates'
        templates_dir.mkdir()

        template_content = """---
title: "{{title}}"
---

# {{title}}

{{content}}
"""
        (templates_dir / 'test.md').write_text(template_content)

        container = TemplatesContainer(templates_dir)
        use_case = container.create_from_template_use_case

        # Test with all required values provided
        result = use_case.create_single_template(
            'test',
            placeholder_values={'title': 'Non-Interactive Title', 'content': 'Non-interactive content'},
            interactive=False,
        )

        assert result['success'] is True
        content = result['content']
        assert '# Non-Interactive Title' in content
        assert 'Non-interactive content' in content

        # Test with missing required values
        result = use_case.create_single_template(
            'test', placeholder_values={'title': 'Partial Title'}, interactive=False
        )

        assert result['success'] is False
        assert 'InvalidPlaceholderValueError' in result['error_type']

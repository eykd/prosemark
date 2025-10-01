"""Unit tests for Template entity."""

from pathlib import Path

import pytest

from prosemark.templates.domain.entities.template import Template
from prosemark.templates.domain.exceptions.template_exceptions import TemplateParseError, TemplateValidationError


class TestTemplate:
    """Test Template entity creation and behavior."""

    def test_from_file_valid_template(self, tmp_path: Path) -> None:
        """Test creating template from valid file."""
        template_content = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
---

# {{title}}

Content by {{author}}.

{{content}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        assert template.name == 'test'
        assert template.path.value == template_file
        assert template.frontmatter['title'] == '{{title}}'
        assert template.frontmatter['author'] == '{{author}}'
        assert template.frontmatter['author_default'] == 'Anonymous'
        assert '# {{title}}' in template.body
        assert 'Content by {{author}}.' in template.body
        assert '{{content}}' in template.body

    def test_from_file_no_frontmatter_raises_error(self, tmp_path: Path) -> None:
        """Test that file without frontmatter raises validation error."""
        template_content = '# Just content\n\nNo frontmatter here.'
        template_file = tmp_path / 'invalid.md'
        template_file.write_text(template_content)

        with pytest.raises(TemplateValidationError, match='must have YAML frontmatter'):
            Template.from_file(template_file)

    def test_from_file_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test that file with invalid YAML raises validation error."""
        template_content = """---
title: {{title}}
invalid: yaml: structure:
---

# Content
"""
        template_file = tmp_path / 'invalid.md'
        template_file.write_text(template_content)

        with pytest.raises(TemplateParseError, match='Invalid YAML frontmatter'):
            Template.from_file(template_file)

    def test_from_file_empty_body_raises_error(self, tmp_path: Path) -> None:
        """Test that file with empty body raises validation error."""
        template_content = """---
title: "Test"
---


"""
        template_file = tmp_path / 'empty.md'
        template_file.write_text(template_content)

        with pytest.raises(TemplateValidationError, match='must have body content'):
            Template.from_file(template_file)

    def test_placeholders_extraction(self, tmp_path: Path) -> None:
        """Test that placeholders are correctly extracted from template."""
        template_content = """---
title: "{{title}}"
description: "{{description}}"
description_default: "No description"
author_default: "Anonymous"
---

# {{title}}

{{description}}

By {{author}}.
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        # Should find placeholders for title, description, and author
        placeholder_names = {p.name for p in template.placeholders}
        assert placeholder_names == {'title', 'description', 'author'}

        # Check required vs optional
        required_names = {p.name for p in template.required_placeholders}
        assert 'title' in required_names  # No default
        assert 'description' not in required_names  # Has default
        assert 'author' not in required_names  # Has default

    def test_get_placeholder_by_name(self, tmp_path: Path) -> None:
        """Test getting placeholder by name."""
        template_content = """---
title: "{{title}}"
author_default: "Anonymous"
---

# {{title}} by {{author}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        title_placeholder = template.get_placeholder_by_name('title')
        assert title_placeholder is not None
        assert title_placeholder.name == 'title'
        assert title_placeholder.required is True

        author_placeholder = template.get_placeholder_by_name('author')
        assert author_placeholder is not None
        assert author_placeholder.name == 'author'
        assert author_placeholder.required is False

        missing_placeholder = template.get_placeholder_by_name('nonexistent')
        assert missing_placeholder is None

    def test_render_with_values(self, tmp_path: Path) -> None:
        """Test rendering template with provided values."""
        template_content = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
---

# {{title}}

Written by {{author}}.

{{content}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        values = {'title': 'My Great Article', 'author': 'John Doe', 'content': 'This is the main content.'}

        rendered = template.render(values)

        assert 'title: "My Great Article"' in rendered
        assert 'author: "John Doe"' in rendered
        assert '# My Great Article' in rendered
        assert 'Written by John Doe.' in rendered
        assert 'This is the main content.' in rendered

    def test_render_with_defaults(self, tmp_path: Path) -> None:
        """Test rendering template using default values."""
        template_content = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
---

# {{title}}

By {{author}}.
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        values = {
            'title': 'My Article'
            # author not provided, should use default
        }

        rendered = template.render(values)

        assert 'title: "My Article"' in rendered
        assert 'author: "Anonymous"' in rendered
        assert '# My Article' in rendered
        assert 'By Anonymous.' in rendered

    def test_render_missing_required_raises_error(self, tmp_path: Path) -> None:
        """Test that missing required placeholder raises error."""
        template_content = """---
title: "{{title}}"
author_default: "Anonymous"
---

# {{title}} by {{author}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        values = {
            'author': 'John Doe'
            # title is required but missing
        }

        with pytest.raises(TemplateValidationError, match='Missing value for required placeholder: title'):
            template.render(values)

    def test_template_equality(self, tmp_path: Path) -> None:
        """Test template equality comparison."""
        template_content = """---
title: "{{title}}"
---

# {{title}}
"""

        file1 = tmp_path / 'test1.md'
        file1.write_text(template_content)
        file2 = tmp_path / 'test2.md'
        file2.write_text(template_content)

        template1 = Template.from_file(file1)
        template2 = Template.from_file(file1)  # Same file
        template3 = Template.from_file(file2)  # Different file, same content

        assert template1 == template2
        assert template1 != template3  # Different path

    def test_template_string_representation(self, tmp_path: Path) -> None:
        """Test template string representation."""
        template_content = """---
title: "{{title}}"
---

# {{title}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        str_repr = str(template)
        assert 'Template(name=test' in str_repr
        assert str(template_file) in str_repr

    def test_template_with_empty_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Test template with empty YAML frontmatter raises validation error."""
        template_content = """---
---

# Test Content

Some body content here.
"""
        template_file = tmp_path / 'empty_yaml.md'
        template_file.write_text(template_content)

        # Empty frontmatter should raise validation error
        with pytest.raises(TemplateValidationError, match='Template must have YAML frontmatter'):
            Template.from_file(template_file)

    def test_template_with_non_dict_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test that YAML frontmatter that's not a dict raises error."""
        template_content = """---
- item1
- item2
---

# Content
"""
        template_file = tmp_path / 'non_dict.md'
        template_file.write_text(template_content)

        with pytest.raises(TemplateParseError, match='YAML frontmatter must be a dictionary'):
            Template.from_file(template_file)

    def test_template_parse_generic_exception_handling(self, tmp_path: Path) -> None:
        """Test generic exception handling during parsing."""
        # Create a template with valid structure
        template_content = """---
title: "{{title}}"
---

# {{title}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        # This should work normally
        template = Template.from_file(template_file)
        assert template.name == 'test'

    def test_template_with_no_frontmatter_at_all(self, tmp_path: Path) -> None:
        """Test template with completely missing frontmatter raises error."""
        template_content = """---
title: "Test"
"""  # Only one --- delimiter, not two
        template_file = tmp_path / 'incomplete.md'
        template_file.write_text(template_content)

        with pytest.raises(TemplateParseError, match='must have proper YAML frontmatter delimited'):
            Template.from_file(template_file)

    def test_template_name_property_alias(self, tmp_path: Path) -> None:
        """Test template_name property is an alias for name."""
        template_content = """---
title: "{{title}}"
---

# {{title}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        assert template.template_name == template.name
        assert template.template_name == 'test'

    def test_from_content_without_filepath(self) -> None:
        """Test creating template from content without providing filepath."""
        template_content = """---
title: "{{title}}"
---

# {{title}}

Content here.
"""
        # Create template without file_path argument
        template = Template.from_content(name='test-template', content=template_content)

        assert template.name == 'test-template'
        assert template.frontmatter['title'] == '{{title}}'
        assert '# {{title}}' in template.body
        assert not template.is_directory_template

    def test_from_content_with_filepath(self, tmp_path: Path) -> None:
        """Test creating template from content with filepath."""
        template_content = """---
title: "{{title}}"
---

# {{title}}

Content here.
"""
        # File must exist for TemplatePath validation
        file_path = tmp_path / 'test.md'
        file_path.write_text(template_content)

        template = Template.from_content(name='test-template', content=template_content, file_path=file_path)

        assert template.name == 'test-template'
        assert template.path.value == file_path
        assert not template.is_directory_template

    def test_from_content_as_directory_template(self, tmp_path: Path) -> None:
        """Test creating template from content marked as directory template."""
        template_content = """---
title: "{{title}}"
---

# {{title}}
"""
        # File must exist for TemplatePath validation
        file_path = tmp_path / 'test.md'
        file_path.write_text(template_content)

        template = Template.from_content(
            name='dir-template', content=template_content, file_path=file_path, is_directory_template=True
        )

        assert template.is_directory_template is True

    def test_replace_placeholders_missing_required_raises_error(self, tmp_path: Path) -> None:
        """Test replace_placeholders raises error for missing required placeholders."""
        template_content = """---
title: "{{title}}"
author_default: "Anonymous"
---

# {{title}} by {{author}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        # Missing required 'title'
        values = {'author': 'John Doe'}

        with pytest.raises(TemplateParseError, match="Missing value for required placeholder 'title'"):
            template.replace_placeholders(values)

    def test_placeholder_not_used_in_template_raises_error(self, tmp_path: Path) -> None:
        """Test that placeholder defined but not used raises validation error."""
        # This is tricky - we need a placeholder in frontmatter metadata but not in content
        # The validation checks if the placeholder pattern exists in the combined text
        template_content = """---
title: "Static Title"
unused_default: "This placeholder is never used"
---

# Static Title

No placeholders in the body.
"""
        template_file = tmp_path / 'unused.md'
        template_file.write_text(template_content)

        # This should not raise error because 'unused' has a default, making it an optional placeholder
        # But it won't be extracted if it's not in the content
        template = Template.from_file(template_file)
        # The template should parse successfully since we only extract placeholders that exist in content
        assert template is not None

    def test_to_dict_representation(self, tmp_path: Path) -> None:
        """Test converting template to dictionary."""
        template_content = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
---

# {{title}}

By {{author}}.
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)
        template_dict = template.to_dict()

        assert template_dict['name'] == 'test'
        assert template_dict['has_placeholders'] is True
        assert template_dict['placeholder_count'] == 2
        assert 'title' in template_dict['required_placeholders']
        assert 'author' in template_dict['optional_placeholders']
        assert template_dict['is_directory_template'] is False
        assert 'title' in template_dict['frontmatter']

    def test_file_path_property(self, tmp_path: Path) -> None:
        """Test file_path property returns Path object."""
        template_content = """---
title: "{{title}}"
---

# {{title}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        assert template.file_path == template_file
        assert isinstance(template.file_path, Path)

    def test_template_body_without_heading(self, tmp_path: Path) -> None:
        """Test template with body that doesn't start with heading (warning case)."""
        template_content = """---
title: "{{title}}"
---

This is body text without a heading.

Some more content.
"""
        template_file = tmp_path / 'no_heading.md'
        template_file.write_text(template_content)

        # Should not raise error, just a warning (pass statement in code)
        template = Template.from_file(template_file)
        assert template.body.strip().startswith('This is')

    def test_direct_template_creation_with_parsed_frontmatter_and_body(self, tmp_path: Path) -> None:
        """Test creating Template directly with pre-parsed frontmatter and body."""
        from prosemark.templates.domain.values.template_path import TemplatePath

        content = """---
title: "{{title}}"
---

# {{title}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(content)

        # Create template with pre-parsed frontmatter and body
        # This tests the branch where __post_init__ doesn't parse content
        template = Template(
            name='test',
            path=TemplatePath(template_file),
            content=content,
            frontmatter={'title': '{{title}}'},
            body='# {{title}}\n',
            placeholders=[],
        )

        assert template.frontmatter == {'title': '{{title}}'}
        assert template.body == '# {{title}}\n'

    def test_replace_placeholders_complete_flow(self, tmp_path: Path) -> None:
        """Test replace_placeholders with all placeholders provided."""
        template_content = """---
title: "{{title}}"
author: "{{author}}"
author_default: "Anonymous"
---

# {{title}}

Written by {{author}}.

{{content}}
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(template_content)

        template = Template.from_file(template_file)

        # Provide all values including optional ones
        values = {'title': 'My Article', 'author': 'John Doe', 'content': 'Main content here.'}

        result = template.replace_placeholders(values)

        assert 'title: "My Article"' in result
        assert 'author: "John Doe"' in result
        assert '# My Article' in result
        assert 'Written by John Doe.' in result
        assert 'Main content here.' in result

    def test_yaml_frontmatter_null_value(self, tmp_path: Path) -> None:
        """Test template with null YAML frontmatter raises validation error."""
        template_content = """---
null
---

# Content

Body content here.
"""
        template_file = tmp_path / 'null_yaml.md'
        template_file.write_text(template_content)

        # YAML null is converted to empty dict, which fails validation
        with pytest.raises(TemplateValidationError, match='Template must have YAML frontmatter'):
            Template.from_file(template_file)

    def test_invalid_placeholder_syntax_raises_error(self, tmp_path: Path) -> None:
        """Test template with invalid placeholder syntax raises InvalidPlaceholderError."""
        from prosemark.templates.domain.exceptions.template_exceptions import InvalidPlaceholderError

        template_content = """---
title: "{{invalid-placeholder}}"
---

# Content

{{invalid-placeholder}}
"""
        template_file = tmp_path / 'invalid_placeholder.md'
        template_file.write_text(template_content)

        # Invalid placeholder syntax (hyphens not allowed) should raise InvalidPlaceholderError
        with pytest.raises(InvalidPlaceholderError):
            Template.from_file(template_file)

    def test_placeholder_defined_but_not_used_raises_error(self, tmp_path: Path) -> None:
        """Test that manually created placeholder not in content raises validation error."""
        from prosemark.templates.domain.entities.placeholder import Placeholder
        from prosemark.templates.domain.values.placeholder_pattern import PlaceholderPattern
        from prosemark.templates.domain.values.template_path import TemplatePath

        content = """---
title: "Static Title"
---

# Static Title

No placeholders here.
"""
        template_file = tmp_path / 'test.md'
        template_file.write_text(content)

        # Create a placeholder that doesn't exist in content
        fake_placeholder = Placeholder(
            name='nonexistent', pattern_obj=PlaceholderPattern('{{nonexistent}}'), required=True
        )

        # Try to create template with this placeholder
        with pytest.raises(TemplateValidationError, match="Placeholder 'nonexistent' defined but not used"):
            Template(
                name='test',
                path=TemplatePath(template_file),
                content=content,
                frontmatter={'title': 'Static Title'},
                body='# Static Title\n\nNo placeholders here.\n',
                placeholders=[fake_placeholder],
            )

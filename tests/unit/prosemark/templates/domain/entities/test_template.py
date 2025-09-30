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

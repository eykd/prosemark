"""Use case for listing available templates."""

from typing import Any

from prosemark.templates.domain.exceptions.template_exceptions import (
    TemplateDirectoryNotFoundError,
    TemplateError,
    TemplateNotFoundError,
)
from prosemark.templates.domain.services.template_service import TemplateService


class ListTemplatesUseCase:
    """Use case for listing and discovering available templates."""

    def __init__(self, template_service: TemplateService) -> None:
        """Initialize use case with template service.

        Args:
            template_service: Service providing template operations

        """
        self._template_service = template_service

    def list_all_templates(self) -> dict[str, Any]:
        """List all available templates (both single and directory).

        Returns:
            Dictionary containing all available templates organized by type

        """
        try:
            # Get single templates
            single_templates = self._template_service.list_templates()

            # Get directory templates
            directory_templates = self._template_service.list_template_directories()

            # Get detailed info for each single template
            single_template_details = []
            for template_name in single_templates:
                try:
                    info = self._template_service.get_template_info(template_name)
                    single_template_details.append(info)
                except TemplateError:
                    # Skip templates that can't be loaded
                    continue

            # Get detailed info for each directory template
            directory_template_details = []
            for directory_name in directory_templates:
                try:
                    info = self._template_service.get_directory_template_info(directory_name)
                    directory_template_details.append(info)
                except TemplateError:
                    # Skip directories that can't be loaded
                    continue

            return {
                'success': True,
                'single_templates': {
                    'count': len(single_template_details),
                    'names': single_templates,
                    'details': single_template_details,
                },
                'directory_templates': {
                    'count': len(directory_template_details),
                    'names': directory_templates,
                    'details': directory_template_details,
                },
                'total_templates': len(single_templates) + len(directory_templates),
                'summary': ListTemplatesUseCase._create_templates_summary(
                    single_template_details, directory_template_details
                ),
            }

        except TemplateError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }

    def list_single_templates(self) -> dict[str, Any]:
        """List only single templates.

        Returns:
            Dictionary containing single template information

        """
        try:
            template_names = self._template_service.list_templates()

            # Get detailed info for each template
            template_details = []
            failed_templates = []

            for template_name in template_names:
                try:
                    info = self._template_service.get_template_info(template_name)
                    template_details.append(info)
                except TemplateError as e:
                    failed_templates.append({
                        'name': template_name,
                        'error': str(e),
                        'error_type': type(e).__name__,
                    })

            return {
                'success': True,
                'template_type': 'single',
                'count': len(template_details),
                'names': [detail['name'] for detail in template_details],
                'details': template_details,
                'failed': failed_templates,
                'summary': ListTemplatesUseCase._create_single_templates_summary(template_details),
            }

        except TemplateError as e:
            return {
                'success': False,
                'template_type': 'single',
                'error': str(e),
                'error_type': type(e).__name__,
            }

    def list_directory_templates(self) -> dict[str, Any]:
        """List only directory templates.

        Returns:
            Dictionary containing directory template information

        """
        try:
            directory_names = self._template_service.list_template_directories()

            # Get detailed info for each directory
            directory_details = []
            failed_directories = []

            for directory_name in directory_names:
                try:
                    info = self._template_service.get_directory_template_info(directory_name)
                    directory_details.append(info)
                except TemplateError as e:
                    failed_directories.append({
                        'name': directory_name,
                        'error': str(e),
                        'error_type': type(e).__name__,
                    })

            return {
                'success': True,
                'template_type': 'directory',
                'count': len(directory_details),
                'names': [detail['name'] for detail in directory_details],
                'details': directory_details,
                'failed': failed_directories,
                'summary': ListTemplatesUseCase._create_directory_templates_summary(directory_details),
            }

        except TemplateError as e:
            return {
                'success': False,
                'template_type': 'directory',
                'error': str(e),
                'error_type': type(e).__name__,
            }

    def search_templates(self, query: str, *, search_in_descriptions: bool = True) -> dict[str, Any]:
        """Search for templates by name or description.

        Args:
            query: Search query string
            search_in_descriptions: Whether to search in template descriptions

        Returns:
            Dictionary containing search results

        """
        try:
            query_lower = query.lower()

            # Get all templates
            all_templates_result = self.list_all_templates()
            if not all_templates_result['success']:
                return all_templates_result

            single_templates = all_templates_result['single_templates']['details']
            directory_templates = all_templates_result['directory_templates']['details']

            # Search single templates
            matching_single = [
                template
                for template in single_templates
                if self._template_matches_query(template, query_lower, search_in_descriptions=search_in_descriptions)
            ]

            # Search directory templates
            matching_directory = [
                template
                for template in directory_templates
                if self._template_matches_query(template, query_lower, search_in_descriptions=search_in_descriptions)
            ]

            return {
                'success': True,
                'query': query,
                'search_in_descriptions': search_in_descriptions,
                'single_templates': {
                    'count': len(matching_single),
                    'results': matching_single,
                },
                'directory_templates': {
                    'count': len(matching_directory),
                    'results': matching_directory,
                },
                'total_matches': len(matching_single) + len(matching_directory),
            }

        except TemplateError as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'error_type': type(e).__name__,
            }

    def get_template_details(self, template_name: str) -> dict[str, Any]:
        """Get detailed information about a specific template.

        Args:
            template_name: Name of template to get details for

        Returns:
            Dictionary containing detailed template information

        """
        # Try as single template first
        try:
            template_info = self._template_service.get_template_info(template_name)
        except TemplateNotFoundError:
            pass
        else:
            return {
                'success': True,
                'template_name': template_name,
                'template_type': 'single',
                'found': True,
                'details': template_info,
            }

        # Try as directory template
        try:
            directory_info = self._template_service.get_directory_template_info(template_name)
        except TemplateDirectoryNotFoundError:
            pass
        else:
            return {
                'success': True,
                'template_name': template_name,
                'template_type': 'directory',
                'found': True,
                'details': directory_info,
            }

        # Template not found in either location
        return {
            'success': True,
            'template_name': template_name,
            'template_type': 'unknown',
            'found': False,
            'error': f"Template '{template_name}' not found as single template or directory template",
        }

    def get_templates_with_placeholders(self) -> dict[str, Any]:
        """List templates that require placeholder values.

        Returns:
            Dictionary containing templates with placeholders

        """
        try:
            all_templates_result = self.list_all_templates()
            if not all_templates_result['success']:  # pragma: no cover
                return all_templates_result

            single_templates = all_templates_result['single_templates']['details']
            directory_templates = all_templates_result['directory_templates']['details']

            # Filter templates with placeholders
            single_with_placeholders = [t for t in single_templates if t.get('placeholder_count', 0) > 0]

            directory_with_placeholders = [
                t
                for t in directory_templates
                if len(t.get('required_placeholders', [])) > 0 or len(t.get('optional_placeholders', [])) > 0
            ]

            return {
                'success': True,
                'single_templates': {
                    'count': len(single_with_placeholders),
                    'templates': single_with_placeholders,
                },
                'directory_templates': {
                    'count': len(directory_with_placeholders),
                    'templates': directory_with_placeholders,
                },
                'total_with_placeholders': len(single_with_placeholders) + len(directory_with_placeholders),
            }

        except TemplateError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }

    @staticmethod
    def _create_templates_summary(
        single_templates: list[dict[str, Any]],
        directory_templates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create summary statistics for all templates.

        Args:
            single_templates: List of single template details
            directory_templates: List of directory template details

        Returns:
            Summary statistics dictionary

        """
        single_summary = ListTemplatesUseCase._create_single_templates_summary(single_templates)
        directory_summary = ListTemplatesUseCase._create_directory_templates_summary(directory_templates)

        return {
            'total_templates': len(single_templates) + len(directory_templates),
            'single_templates': single_summary,
            'directory_templates': directory_summary,
            'templates_with_placeholders': (
                single_summary['with_placeholders'] + directory_summary['with_placeholders']
            ),
            'templates_without_placeholders': (
                single_summary['without_placeholders'] + directory_summary['without_placeholders']
            ),
        }

    @staticmethod
    def _create_single_templates_summary(templates: list[dict[str, Any]]) -> dict[str, Any]:
        """Create summary statistics for single templates.

        Args:
            templates: List of single template details

        Returns:
            Summary statistics dictionary

        """
        if not templates:
            return {
                'count': 0,
                'with_placeholders': 0,
                'without_placeholders': 0,
                'total_placeholders': 0,
                'avg_placeholders_per_template': 0.0,
            }

        with_placeholders = sum(1 for t in templates if t.get('placeholder_count', 0) > 0)
        without_placeholders = len(templates) - with_placeholders
        total_placeholders = sum(t.get('placeholder_count', 0) for t in templates)

        return {
            'count': len(templates),
            'with_placeholders': with_placeholders,
            'without_placeholders': without_placeholders,
            'total_placeholders': total_placeholders,
            'avg_placeholders_per_template': total_placeholders / len(templates),
        }

    @staticmethod
    def _create_directory_templates_summary(directories: list[dict[str, Any]]) -> dict[str, Any]:
        """Create summary statistics for directory templates.

        Args:
            directories: List of directory template details

        Returns:
            Summary statistics dictionary

        """
        if not directories:
            return {
                'count': 0,
                'with_placeholders': 0,
                'without_placeholders': 0,
                'total_template_files': 0,
                'avg_files_per_directory': 0.0,
            }

        with_placeholders = sum(
            1
            for d in directories
            if len(d.get('required_placeholders', [])) > 0 or len(d.get('optional_placeholders', [])) > 0
        )
        without_placeholders = len(directories) - with_placeholders
        total_files = sum(d.get('template_count', 0) for d in directories)

        return {
            'count': len(directories),
            'with_placeholders': with_placeholders,
            'without_placeholders': without_placeholders,
            'total_template_files': total_files,
            'avg_files_per_directory': total_files / len(directories),
        }

    @staticmethod
    def _template_matches_query(template: dict[str, Any], query_lower: str, *, search_in_descriptions: bool) -> bool:
        """Check if a template matches the search query.

        Args:
            template: Template details dictionary
            query_lower: Lowercase search query
            search_in_descriptions: Whether to search in descriptions

        Returns:
            True if template matches query

        """
        # Search in name
        if query_lower in template.get('name', '').lower():
            return True

        # Search in placeholder names
        placeholder_names = template.get('required_placeholders', []) + template.get('optional_placeholders', [])
        for placeholder_name in placeholder_names:
            if query_lower in placeholder_name.lower():
                return True

        # Search in descriptions if enabled
        if search_in_descriptions:
            # Search in frontmatter values if available
            frontmatter = template.get('frontmatter', {})
            for value in frontmatter.values():
                if isinstance(value, str) and query_lower in value.lower():
                    return True

        return False

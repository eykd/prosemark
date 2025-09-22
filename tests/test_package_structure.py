"""Test package structure and importability."""


class TestPackageStructure:
    """Test hexagonal architecture package structure."""

    def test_packages_are_importable(self) -> None:
        """Verify all packages can be imported."""
        # Import all main packages - should not raise ImportError

    def test_domain_package_has_proper_docstring(self) -> None:
        """Verify domain package has descriptive docstring."""
        import prosemark.domain

        assert prosemark.domain.__doc__ is not None
        assert 'domain' in prosemark.domain.__doc__.lower()
        assert 'business logic' in prosemark.domain.__doc__.lower()

    def test_app_package_has_proper_docstring(self) -> None:
        """Verify app package has descriptive docstring."""
        import prosemark.app

        assert prosemark.app.__doc__ is not None
        assert 'application' in prosemark.app.__doc__.lower()

    def test_ports_package_has_proper_docstring(self) -> None:
        """Verify ports package has descriptive docstring."""
        import prosemark.ports

        assert prosemark.ports.__doc__ is not None
        assert 'port' in prosemark.ports.__doc__.lower()
        assert 'interface' in prosemark.ports.__doc__.lower()

    def test_adapters_package_has_proper_docstring(self) -> None:
        """Verify adapters package has descriptive docstring."""
        import prosemark.adapters

        assert prosemark.adapters.__doc__ is not None
        assert 'adapter' in prosemark.adapters.__doc__.lower()
        assert 'implementation' in prosemark.adapters.__doc__.lower()

    def test_cli_package_has_proper_docstring(self) -> None:
        """Verify CLI package has descriptive docstring."""
        import prosemark.cli

        assert prosemark.cli.__doc__ is not None
        assert 'cli' in prosemark.cli.__doc__.lower()
        assert 'command' in prosemark.cli.__doc__.lower()

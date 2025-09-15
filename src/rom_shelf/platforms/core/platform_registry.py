"""Platform registry for managing all supported platforms."""

import importlib
import pkgutil
from pathlib import Path

from .base_platform import BasePlatform
from .platform_decorators import get_discovered_platforms


class PlatformRegistry:
    """Registry for managing all supported platforms."""

    def __init__(self) -> None:
        """Initialize the platform registry."""
        self._platforms: dict[str, BasePlatform] = {}
        self._initialize_platforms()

    def _initialize_platforms(self) -> None:
        """Initialize all supported platforms using auto-discovery."""
        # Auto-discover platforms by importing all platform modules
        self._auto_discover_platforms()

        # Create instances of all discovered platforms
        discovered_platform_classes = get_discovered_platforms()

        for platform_id, platform_class in discovered_platform_classes.items():
            try:
                platform_instance = platform_class()
                self._platforms[platform_id] = platform_instance

                # Register platform extensions
                self._register_platform_extensions(platform_instance)

                # Register platform settings defaults
                self._register_platform_settings(platform_instance)

            except Exception as e:
                print(f"Warning: Failed to initialize platform '{platform_id}': {e}")

        if not self._platforms:
            raise RuntimeError(
                "No platforms were discovered. Ensure platform modules use @register_platform decorator."
            )

    def _auto_discover_platforms(self) -> None:
        """Auto-discover platform modules by importing all .py files in the platforms package."""
        platforms_dir = Path(__file__).parent.parent  # Go up from core/ to platforms/

        for module_info in pkgutil.iter_modules([str(platforms_dir)]):
            module_name = module_info.name

            # Skip utility modules and the registry itself
            if module_name in [
                "platform_registry",
                "platform_utils",
                "platform_decorators",
                "validation",
                "platform_families",
                "base_platform",
                "__init__",
            ]:
                continue

            try:
                # Import the module to trigger @register_platform decorators
                # Import from parent package since we're in core/ subdirectory
                parent_package = ".".join(
                    __package__.split(".")[:-1]
                )  # Remove 'core' from package path
                importlib.import_module(f".{module_name}", package=parent_package)
            except ImportError as e:
                print(f"Warning: Failed to import platform module '{module_name}': {e}")

    def register_platform_class(self, platform_class: type[BasePlatform]) -> None:
        """Manually register a platform class (alternative to decorator)."""
        try:
            platform_instance = platform_class()
            platform_id = platform_instance.platform_id

            if platform_id in self._platforms:
                print(f"Warning: Platform '{platform_id}' is already registered, replacing...")

            self._platforms[platform_id] = platform_instance
        except Exception as e:
            print(f"Error registering platform class {platform_class.__name__}: {e}")

    def get_platform(self, platform_id: str) -> BasePlatform | None:
        """Get a platform by its ID."""
        return self._platforms.get(platform_id)

    def get_all_platforms(self) -> list[BasePlatform]:
        """Get all registered platforms."""
        return list(self._platforms.values())

    def get_platform_by_extension(self, extension: str) -> list[BasePlatform]:
        """Get platforms that support a given extension."""
        extension = extension.lower()
        matching_platforms = []

        for platform in self._platforms.values():
            if extension in platform.supported_handlers:
                matching_platforms.append(platform)

        return matching_platforms

    def get_platform_ids(self) -> list[str]:
        """Get all platform IDs."""
        return list(self._platforms.keys())

    def get_platform_names(self) -> list[str]:
        """Get all platform names."""
        return [platform.name for platform in self._platforms.values()]

    def _register_platform_extensions(self, platform_instance: BasePlatform) -> None:
        """Register platform extensions with the extension registry."""
        try:
            from ...core.extension_handler import extension_registry

            extension_registry.register_platform_extensions(platform_instance)
        except Exception as e:
            print(
                f"Warning: Failed to register extensions for {platform_instance.platform_id}: {e}"
            )

    def _register_platform_settings(self, platform_instance: BasePlatform) -> None:
        """Register platform settings with the global settings."""
        try:
            from ...core.settings import get_settings

            settings = get_settings()
            platform_settings_def = platform_instance.get_platform_settings()
            settings.register_platform_defaults(
                platform_instance.platform_id, platform_settings_def
            )
        except Exception as e:
            print(f"Warning: Failed to register settings for {platform_instance.platform_id}: {e}")


# Global platform registry instance
platform_registry = PlatformRegistry()

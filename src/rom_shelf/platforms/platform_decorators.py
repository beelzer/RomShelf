"""Platform registration decorators and discovery system."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_platform import BasePlatform

# Global registry for discovered platforms
_discovered_platforms: dict[str, type["BasePlatform"]] = {}


def register_platform(cls: type["BasePlatform"]) -> type["BasePlatform"]:
    """
    Decorator to automatically register a platform class.

    Usage:
        @register_platform
        class MyPlatform(BasePlatform):
            ...
    """
    # Create an instance to get the platform ID
    instance = cls()
    platform_id = instance.platform_id

    if platform_id in _discovered_platforms:
        raise ValueError(f"Platform '{platform_id}' is already registered")

    _discovered_platforms[platform_id] = cls
    return cls


def get_discovered_platforms() -> dict[str, type["BasePlatform"]]:
    """Get all platforms discovered through the @register_platform decorator."""
    return _discovered_platforms.copy()


def clear_discovered_platforms() -> None:
    """Clear the discovered platforms registry (mainly for testing)."""
    _discovered_platforms.clear()

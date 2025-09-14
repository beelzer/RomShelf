"""Platform registry for managing all supported platforms."""


from .base_platform import BasePlatform
from .game_boy import GameBoyPlatform
from .game_boy_advance import GameBoyAdvancePlatform
from .game_boy_color import GameBoyColorPlatform
from .nintendo_64 import Nintendo64Platform
from .nintendo_gamecube import NintendoGameCubePlatform
from .playstation_1 import PlayStation1Platform
from .super_nintendo import SuperNintendoPlatform


class PlatformRegistry:
    """Registry for managing all supported platforms."""

    def __init__(self) -> None:
        """Initialize the platform registry."""
        self._platforms: dict[str, BasePlatform] = {}
        self._initialize_platforms()

    def _initialize_platforms(self) -> None:
        """Initialize all supported platforms."""
        platforms = [
            Nintendo64Platform(),
            NintendoGameCubePlatform(),
            GameBoyPlatform(),
            GameBoyColorPlatform(),
            GameBoyAdvancePlatform(),
            SuperNintendoPlatform(),
            PlayStation1Platform(),
        ]

        for platform in platforms:
            self._platforms[platform.platform_id] = platform

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


# Global platform registry instance
platform_registry = PlatformRegistry()

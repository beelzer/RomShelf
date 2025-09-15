"""Nintendo GameCube platform implementation."""

from pathlib import Path
from typing import Any

from ..core.extension_handler import ExtensionHandler, FileHandlingType
from .core.base_platform import (
    PlatformSetting,
    SettingType,
)
from .core.platform_decorators import register_platform
from .core.platform_families import DiscBasedPlatform
from .core.platform_utils import PlatformUtils


@register_platform
class NintendoGameCubePlatform(DiscBasedPlatform):
    """Nintendo GameCube platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Nintendo GameCube"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "gamecube"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".iso", ".gcm", ".rvz", ".wbfs", ".ciso"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".iso", ".gcm", ".rvz", ".wbfs", ".ciso"]

    def register_extensions(self, registry) -> None:
        """Register Nintendo GameCube extension handlers."""
        registry.register_handler(ExtensionHandler(".iso", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".gcm", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".rvz", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".wbfs", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".ciso", FileHandlingType.DIRECT))

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for GameCube ISOs."""
        return (100 * 1024 * 1024, 8 * 1024 * 1024 * 1024)  # 100MB to 8GB

    def get_disc_formats(self) -> list[str]:
        """Get supported disc formats."""
        return [".iso", ".gcm", ".rvz", ".wbfs", ".ciso"]

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Nintendo GameCube-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add GameCube-specific settings
        gamecube_specific_settings = [
            PlatformSetting(
                key="preferred_format",
                label="Preferred ROM Format",
                description="Preferred GameCube ROM format when multiple formats are available",
                setting_type=SettingType.CHOICE,
                default_value=".rvz",
                choices=[".rvz", ".iso", ".gcm", ".wbfs", ".ciso"],
            ),
            PlatformSetting(
                key="validate_disc_headers",
                label="Validate Disc Headers",
                description="Validate GameCube disc headers for authenticity",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
        ]

        return settings + gamecube_specific_settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file (uses parent implementation)."""
        return super().parse_rom_info(file_path)

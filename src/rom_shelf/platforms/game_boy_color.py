"""Game Boy Color platform implementation."""

from pathlib import Path
from typing import Any

from ..core.extension_handler import ExtensionHandler, FileHandlingType
from .core.base_platform import (
    PlatformSetting,
    SettingType,
)
from .core.platform_decorators import register_platform
from .core.platform_families import HandheldPlatform
from .core.platform_utils import PlatformUtils


@register_platform
class GameBoyColorPlatform(HandheldPlatform):
    """Game Boy Color platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Game Boy Color"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "gbc"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".gbc"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".gbc"]

    def register_extensions(self, registry) -> None:
        """Register Game Boy Color extension handlers."""
        registry.register_handler(ExtensionHandler(".gbc", FileHandlingType.DIRECT))

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for GBC ROMs."""
        return (32 * 1024, 8 * 1024 * 1024)  # 32KB to 8MB

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Game Boy Color-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add GBC-specific settings
        gbc_specific_settings = [
            PlatformSetting(
                key="backward_compatibility",
                label="Game Boy Backward Compatibility",
                description="Display compatibility with original Game Boy games",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
        ]

        return settings + gbc_specific_settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        return PlatformUtils.create_base_metadata(file_path)

"""Game Boy Advance platform implementation."""

from pathlib import Path
from typing import Any

from .base_platform import (
    PlatformSetting,
    SettingType,
)
from .platform_decorators import register_platform
from .platform_families import HandheldPlatform
from .platform_utils import PlatformUtils


@register_platform
class GameBoyAdvancePlatform(HandheldPlatform):
    """Game Boy Advance platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Game Boy Advance"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "gba"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".gba"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".gba"]

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for GBA ROMs."""
        return (128 * 1024, 32 * 1024 * 1024)  # 128KB to 32MB

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Game Boy Advance-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add GBA-specific settings
        gba_specific_settings = [
            PlatformSetting(
                key="detect_save_type",
                label="Auto-detect Save Type",
                description="Automatically detect save type (SRAM, Flash, EEPROM) from ROM",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
            PlatformSetting(
                key="multiboot_support",
                label="Support Multiboot ROMs",
                description="Enable support for GBA Multiboot (smaller) ROMs",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
            ),
        ]

        return settings + gba_specific_settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        # Try to determine save type from file size (basic heuristic)
        save_type = "Unknown"
        try:
            file_size = file_path.stat().st_size
            if file_size <= 16 * 1024 * 1024:  # <= 16MB
                save_type = "SRAM"
            else:
                save_type = "Flash"
        except (OSError, FileNotFoundError):
            pass

        return PlatformUtils.create_base_metadata(file_path, save_type=save_type)

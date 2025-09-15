"""PlayStation 1 platform implementation."""

from pathlib import Path
from typing import Any

from .base_platform import (
    PlatformSetting,
    SettingType,
)
from .platform_decorators import register_platform
from .platform_families import DiscBasedPlatform
from .platform_utils import PlatformUtils


@register_platform
class PlayStation1Platform(DiscBasedPlatform):
    """PlayStation 1 platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "PlayStation 1"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "psx"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".iso", ".cue", ".bin", ".chd"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".iso", ".cue", ".bin", ".chd"]

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for PlayStation 1 games."""
        return (100 * 1024 * 1024, 1000 * 1024 * 1024)  # 100MB to 1GB

    def get_disc_formats(self) -> list[str]:
        """Get supported disc formats."""
        return [".iso", ".cue", ".bin", ".chd"]

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get PlayStation 1-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add PlayStation 1-specific settings
        psx_specific_settings = [
            PlatformSetting(
                key="prefer_cue_over_iso",
                label="Prefer CUE over ISO",
                description="When both CUE and ISO files are present, prioritize CUE files for better audio support",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
            PlatformSetting(
                key="disc_naming_format",
                label="Multi-disc Naming Format",
                description="How to detect and handle multi-disc games",
                setting_type=SettingType.CHOICE,
                default_value="Disc N",
                choices=["Disc N", "Disk N", "(Disc N)", "(Disk N)", "CD N", "(CD N)"],
            ),
        ]

        return settings + psx_specific_settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file (uses parent implementation)."""
        return super().parse_rom_info(file_path)

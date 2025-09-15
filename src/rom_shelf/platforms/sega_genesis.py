"""Sega Genesis/Mega Drive platform implementation - demonstrating new platform system."""

from pathlib import Path
from typing import Any

from .base_platform import PlatformSetting, SettingType
from .platform_decorators import register_platform
from .platform_families import ConsolePlatform
from .platform_utils import PlatformUtils


@register_platform
class SegaGenesisPlatform(ConsolePlatform):
    """Sega Genesis/Mega Drive platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Sega Genesis"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "genesis"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".bin", ".gen", ".md", ".smd"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".bin", ".gen", ".md", ".smd"]

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for Genesis ROMs."""
        return (32 * 1024, 4 * 1024 * 1024)  # 32KB to 4MB

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Genesis-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add Genesis-specific settings
        genesis_specific_settings = [
            PlatformSetting(
                key="region_detection",
                label="Auto-detect Region",
                description="Automatically detect region from ROM header",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
            PlatformSetting(
                key="sram_detection",
                label="Detect SRAM Support",
                description="Check if ROM supports save data (SRAM)",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
        ]

        return settings + genesis_specific_settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        # Try to read Genesis header for enhanced metadata
        metadata = PlatformUtils.create_base_metadata(file_path)

        # Try to extract title from Genesis header (offset 0x150)
        try:
            with open(file_path, "rb") as f:
                f.seek(0x150)
                title_bytes = f.read(48)  # Genesis title is 48 bytes
                title = title_bytes.decode("ascii", errors="ignore").strip()
                if title:
                    metadata["header_title"] = title
        except OSError:
            pass

        return metadata

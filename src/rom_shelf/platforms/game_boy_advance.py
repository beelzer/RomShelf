"""Game Boy Advance platform implementation."""

from pathlib import Path
from typing import Any

from .base_platform import (
    BasePlatform,
    PlatformFileTypeSupport,
    PlatformSetting,
    SettingType,
    TableColumn,
)
from .platform_utils import PlatformUtils


class GameBoyAdvancePlatform(BasePlatform):
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

    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        columns = PlatformUtils.get_standard_handheld_columns()
        # Insert save_type column before hash
        columns.insert(-1, TableColumn("save_type", "Save Type", 100))
        return columns

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        return PlatformUtils.get_standard_file_type_support()

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Game Boy Advance-specific settings."""
        return [
            PlatformUtils.create_rom_directories_setting("Game Boy Advance"),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting("Game Boy Advance", [".gba"]),
            PlatformUtils.create_supported_archives_setting(),
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
            PlatformUtils.create_header_validation_setting(),
            PlatformUtils.create_max_file_size_setting(default_mb=32, max_mb=64),
        ]

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

    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        # Check file exists and has correct extension
        if not PlatformUtils.validate_file_exists_and_extension(file_path, [".gba"]):
            return False

        # Basic size check - GBA ROMs are typically 1MB to 32MB
        return PlatformUtils.validate_file_size(file_path, 1024 * 1024, 32 * 1024 * 1024)

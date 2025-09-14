"""Nintendo 64 platform implementation."""

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


class Nintendo64Platform(BasePlatform):
    """Nintendo 64 platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Nintendo 64"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "n64"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".n64", ".z64", ".v64"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".n64", ".z64", ".v64"]

    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        return PlatformUtils.get_standard_console_columns()

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        return PlatformUtils.get_standard_file_type_support()

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Nintendo 64-specific settings."""
        return [
            PlatformUtils.create_rom_directories_setting("Nintendo 64"),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting("Nintendo 64", [".n64", ".z64", ".v64"]),
            PlatformUtils.create_supported_archives_setting(),
            PlatformSetting(
                key="preferred_format",
                label="Preferred ROM Format",
                description="Preferred N64 ROM format when multiple formats are available",
                setting_type=SettingType.CHOICE,
                default_value=".z64",
                choices=[".z64", ".n64", ".v64"]
            ),
            PlatformSetting(
                key="byteswap_detection",
                label="Auto-detect Byteswap",
                description="Automatically detect and handle byteswapped ROM formats",
                setting_type=SettingType.BOOLEAN,
                default_value=True
            ),
            PlatformUtils.create_max_file_size_setting(default_mb=64, max_mb=128)
        ]

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        return PlatformUtils.create_base_metadata(
            file_path,
            file_type=file_path.suffix.upper()
        )

    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        # Check file exists and has correct extension
        if not PlatformUtils.validate_file_exists_and_extension(
            file_path, [".n64", ".z64", ".v64"]
        ):
            return False

        # Basic size check - N64 ROMs are typically 4MB to 64MB
        return PlatformUtils.validate_file_size(
            file_path,
            min_size=1024 * 1024,      # 1MB minimum
            max_size=64 * 1024 * 1024  # 64MB maximum
        )

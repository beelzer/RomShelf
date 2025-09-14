"""Game Boy Color platform implementation."""

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


class GameBoyColorPlatform(BasePlatform):
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

    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        return PlatformUtils.get_standard_handheld_columns()

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        return PlatformUtils.get_standard_file_type_support()

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Game Boy Color-specific settings."""
        return [
            PlatformUtils.create_rom_directories_setting("Game Boy Color"),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting("Game Boy Color", [".gbc"]),
            PlatformUtils.create_supported_archives_setting(),
            PlatformSetting(
                key="backward_compatibility",
                label="Game Boy Backward Compatibility",
                description="Display compatibility with original Game Boy games",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
            PlatformUtils.create_header_validation_setting(),
            PlatformUtils.create_max_file_size_setting(default_mb=8, max_mb=16),
        ]

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        return PlatformUtils.create_base_metadata(file_path)

    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        # Check file exists and has correct extension
        if not PlatformUtils.validate_file_exists_and_extension(file_path, [".gbc"]):
            return False

        # Basic size check - Game Boy Color ROMs are typically 32KB to 8MB
        return PlatformUtils.validate_file_size(
            file_path,
            min_size=32 * 1024,  # 32KB minimum
            max_size=8 * 1024 * 1024,  # 8MB maximum
        )

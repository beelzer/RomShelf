"""Super Nintendo Entertainment System platform implementation."""

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


class SuperNintendoPlatform(BasePlatform):
    """Super Nintendo Entertainment System platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Super Nintendo"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "snes"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".sfc", ".smc"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".sfc", ".smc"]

    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        return [
            TableColumn("name", "Name", 300),
            TableColumn("region", "Region", 80),
            TableColumn("language", "Language", 80),
            TableColumn("version", "Version", 80),
            TableColumn("size", "Size", 100),
            TableColumn("dump_status", "Status", 80),
            TableColumn("file_type", "Type", 80),
            TableColumn("hash", "Hash", 200),
        ]

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        return PlatformUtils.get_standard_file_type_support()

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Super Nintendo-specific settings."""
        return [
            PlatformUtils.create_rom_directories_setting("Super Nintendo"),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting("Super Nintendo", [".sfc", ".smc"]),
            PlatformUtils.create_supported_archives_setting(),
            PlatformSetting(
                key="show_dump_status",
                label="Show Dump Status",
                description="Display ROM dump quality status (verified, beta, etc.)",
                setting_type=SettingType.BOOLEAN,
                default_value=True
            ),
            PlatformSetting(
                key="preferred_format",
                label="Preferred ROM Format",
                description="Preferred SNES ROM format when multiple formats are available",
                setting_type=SettingType.CHOICE,
                default_value=".sfc",
                choices=[".sfc", ".smc"]
            ),
            PlatformSetting(
                key="filter_bad_dumps",
                label="Filter Bad Dumps",
                description="Hide ROMs marked as bad dumps in scan results",
                setting_type=SettingType.BOOLEAN,
                default_value=False
            ),
            PlatformUtils.create_header_validation_setting(),
            PlatformUtils.create_max_file_size_setting(default_mb=6, max_mb=12)
        ]

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        filename = file_path.name

        # Extract version and dump status
        version = PlatformUtils.parse_version_from_filename(filename)
        dump_status = PlatformUtils.parse_dump_status_from_filename(filename)

        # Determine file type based on extension
        extension = file_path.suffix.lower()
        if extension == ".sfc":
            file_type = "SFC"
        elif extension == ".smc":
            file_type = "SMC"
        else:
            file_type = extension.upper()

        metadata = PlatformUtils.create_base_metadata(
            file_path,
            version=version,
            dump_status=dump_status,
            file_type=file_type
        )

        return metadata

    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        # Check file exists and has correct extension
        if not PlatformUtils.validate_file_exists_and_extension(
            file_path, [".sfc", ".smc"]
        ):
            return False

        # Basic size check - SNES ROMs are typically 256KB to 6MB
        return PlatformUtils.validate_file_size(
            file_path,
            min_size=256 * 1024,      # 256KB minimum
            max_size=6 * 1024 * 1024  # 6MB maximum
        )

"""Nintendo GameCube platform implementation."""

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


class NintendoGameCubePlatform(BasePlatform):
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

    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        return PlatformUtils.get_standard_console_columns()

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        return PlatformUtils.get_standard_file_type_support()

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Nintendo GameCube-specific settings."""
        return [
            PlatformUtils.create_rom_directories_setting("Nintendo GameCube"),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting("Nintendo GameCube", [".iso", ".gcm", ".rvz", ".wbfs", ".ciso"]),
            PlatformUtils.create_supported_archives_setting(),
            PlatformSetting(
                key="preferred_format",
                label="Preferred ROM Format",
                description="Preferred GameCube ROM format when multiple formats are available",
                setting_type=SettingType.CHOICE,
                default_value=".rvz",
                choices=[".rvz", ".iso", ".gcm", ".wbfs", ".ciso"]
            ),
            PlatformSetting(
                key="validate_disc_headers",
                label="Validate Disc Headers",
                description="Validate GameCube disc headers for authenticity",
                setting_type=SettingType.BOOLEAN,
                default_value=True
            ),
            PlatformUtils.create_max_file_size_setting(default_mb=1500, min_mb=100, max_mb=8000)
        ]

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        return PlatformUtils.create_base_metadata(
            file_path,
            file_type=file_path.suffix.upper()
        )

    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        print(f"DEBUG: GameCube validation for {file_path.name}")

        # Check file exists and has correct extension
        exists_and_ext = PlatformUtils.validate_file_exists_and_extension(
            file_path, [".iso", ".gcm", ".rvz", ".wbfs", ".ciso"]
        )
        print(f"DEBUG: File exists and extension check: {exists_and_ext}")
        if not exists_and_ext:
            print(f"DEBUG: Failed exists/extension check - exists: {file_path.exists()}, extension: {file_path.suffix}")
            return False

        # Basic size check - GameCube ROMs vary greatly in size
        # RVZ compressed files can be very small (10MB+), uncompressed ISOs are large (1.5GB)
        size_valid = PlatformUtils.validate_file_size(
            file_path,
            min_size=10 * 1024 * 1024,      # 10MB minimum (for highly compressed RVZ files)
            max_size=8 * 1024 * 1024 * 1024  # 8GB maximum (for large collections/multi-disc)
        )
        print(f"DEBUG: Size validation: {size_valid} (size: {file_path.stat().st_size / 1024 / 1024:.1f} MB)")

        result = size_valid
        print(f"DEBUG: Final GameCube validation result for {file_path.name}: {result}")
        return result

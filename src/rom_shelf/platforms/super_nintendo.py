"""Super Nintendo Entertainment System platform implementation."""

from pathlib import Path
from typing import Any

from ..core.extension_handler import ExtensionHandler, FileHandlingType
from .core.base_platform import (
    PlatformSetting,
    SettingType,
)
from .core.platform_decorators import register_platform
from .core.platform_families import ConsolePlatform
from .core.platform_utils import PlatformUtils


@register_platform
class SuperNintendoPlatform(ConsolePlatform):
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

    def register_extensions(self, registry) -> None:
        """Register Super Nintendo extension handlers."""
        registry.register_handler(ExtensionHandler(".sfc", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".smc", FileHandlingType.DIRECT))

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for SNES ROMs."""
        return (128 * 1024, 6 * 1024 * 1024)  # 128KB to 6MB

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Super Nintendo-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add SNES-specific settings
        snes_specific_settings = [
            PlatformSetting(
                key="show_dump_status",
                label="Show Dump Status",
                description="Display ROM dump quality status (verified, beta, etc.)",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
            PlatformSetting(
                key="preferred_format",
                label="Preferred ROM Format",
                description="Preferred SNES ROM format when multiple formats are available",
                setting_type=SettingType.CHOICE,
                default_value=".sfc",
                choices=[".sfc", ".smc"],
            ),
            PlatformSetting(
                key="filter_bad_dumps",
                label="Filter Bad Dumps",
                description="Hide ROMs marked as bad dumps in scan results",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
            ),
        ]

        return settings + snes_specific_settings

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
            file_path, version=version, dump_status=dump_status, file_type=file_type
        )

        return metadata

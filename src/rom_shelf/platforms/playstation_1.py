"""PlayStation 1 platform implementation."""

from pathlib import Path
from typing import Any

from ..core.extension_handler import ExtensionHandler, FileHandlingType
from .core.base_platform import (
    PlatformSetting,
    SettingType,
)
from .core.platform_decorators import register_platform
from .core.platform_families import DiscBasedPlatform
from .core.platform_utils import PlatformUtils
from .validators.cue_bin_validator import CueBinValidator


@register_platform
class PlayStation1Platform(DiscBasedPlatform):
    """PlayStation 1 platform handler."""

    def __init__(self) -> None:
        """Initialize PlayStation 1 platform."""
        super().__init__()
        self._cue_bin_validator = CueBinValidator()

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

    def register_extensions(self, registry) -> None:
        """Register PlayStation 1 extension handlers."""
        registry.register_handler(ExtensionHandler(".iso", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".bin", FileHandlingType.DIRECT))
        registry.register_handler(
            ExtensionHandler(".cue", FileHandlingType.MULTI_FILE, associated_extensions=[".bin"])
        )
        registry.register_handler(ExtensionHandler(".chd", FileHandlingType.DIRECT))

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

    def find_multi_file_primary(self, file_path: Path) -> Path | None:
        """Find the primary file for a multi-file ROM set."""
        return self._cue_bin_validator.find_multi_file_primary(file_path)

    def get_related_files(self, primary_file: Path) -> list[Path]:
        """Get all files that are part of this multi-file ROM."""
        return self._cue_bin_validator.get_related_files(primary_file)

    def is_multi_file_primary(self, file_path: Path) -> bool:
        """Check if file is a primary file in a multi-file set."""
        return self._cue_bin_validator.is_multi_file_primary(file_path)

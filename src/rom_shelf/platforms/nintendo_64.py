"""Nintendo 64 platform implementation."""

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
from .core.validation import N64HeaderValidator


@register_platform
class Nintendo64Platform(ConsolePlatform):
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

    def register_extensions(self, registry) -> None:
        """Register Nintendo 64 extension handlers."""
        registry.register_handler(ExtensionHandler(".n64", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".z64", FileHandlingType.DIRECT))
        registry.register_handler(ExtensionHandler(".v64", FileHandlingType.DIRECT))

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for N64 ROMs."""
        return (1024 * 1024, 64 * 1024 * 1024)  # 1MB to 64MB

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Nintendo 64-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add N64-specific settings
        n64_specific_settings = [
            PlatformSetting(
                key="preferred_format",
                label="Preferred ROM Format",
                description="Preferred N64 ROM format when multiple formats are available",
                setting_type=SettingType.CHOICE,
                default_value=".z64",
                choices=[".z64", ".n64", ".v64"],
            ),
            PlatformSetting(
                key="byteswap_detection",
                label="Auto-detect Byteswap",
                description="Automatically detect and handle byteswapped ROM formats",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
        ]

        return settings + n64_specific_settings

    def _create_validation_chain(self):
        """Create N64-specific validation chain."""
        chain = super()._create_validation_chain()
        # Add N64 header validation
        chain.add_validator(N64HeaderValidator())
        return chain

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        return PlatformUtils.create_base_metadata(file_path, file_type=file_path.suffix.upper())

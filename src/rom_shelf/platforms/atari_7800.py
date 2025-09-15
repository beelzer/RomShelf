"""Atari 7800 platform implementation."""

from pathlib import Path
from typing import Any

from .base_platform import PlatformSetting, SettingType
from .platform_decorators import register_platform
from .platform_families import ConsolePlatform
from .platform_utils import PlatformUtils


@register_platform
class Atari7800Platform(ConsolePlatform):
    """Atari 7800 platform handler."""

    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        return "Atari 7800"

    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        return "atari7800"

    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        return PlatformUtils.create_handlers_list([".a78"])

    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        return [".a78"]

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range for Atari 7800 ROMs."""
        return (16 * 1024, 512 * 1024)  # 16KB to 512KB

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get Atari 7800-specific settings."""
        # Get base settings from parent
        settings = super().get_platform_settings()

        # Add Atari 7800-specific settings
        atari_specific_settings = [
            PlatformSetting(
                key="header_detection",
                label="Detect A78 Header",
                description="Detect and parse Atari 7800 ROM header information",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
            PlatformSetting(
                key="controller_support",
                label="Detect Controller Types",
                description="Automatically detect supported controller types from ROM header",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
        ]

        return settings + atari_specific_settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        # Start with base metadata
        metadata = PlatformUtils.create_base_metadata(file_path)

        # Try to parse Atari 7800 header if present
        try:
            with open(file_path, "rb") as f:
                # Read potential header
                header = f.read(128)

                # Check for A78 header signature
                if len(header) >= 128 and header[:16] == b"ATARI7800       ":
                    # Parse header fields
                    title = header[17:49].decode("ascii", errors="ignore").strip()
                    if title:
                        metadata["header_title"] = title

                    # Parse ROM size from header
                    rom_size = int.from_bytes(header[49:53], byteorder="little")
                    if rom_size > 0:
                        metadata["header_size"] = rom_size

                    # Parse controller info
                    controller_byte = header[54]
                    controllers = []
                    if controller_byte & 0x01:
                        controllers.append("Joystick")
                    if controller_byte & 0x02:
                        controllers.append("Light Gun")
                    if controller_byte & 0x04:
                        controllers.append("Paddle")
                    if controller_byte & 0x08:
                        controllers.append("Trackball")
                    if controller_byte & 0x10:
                        controllers.append("Keyboard")
                    if controllers:
                        metadata["controllers"] = ", ".join(controllers)

                    metadata["has_header"] = True
                else:
                    metadata["has_header"] = False

        except (OSError, ValueError):
            metadata["has_header"] = False

        return metadata

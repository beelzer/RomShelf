"""PlayStation 1 platform implementation."""

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


class PlayStation1Platform(BasePlatform):
    """PlayStation 1 platform handler."""

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

    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        return [
            TableColumn("name", "Name", 300),
            TableColumn("region", "Region", 80),
            TableColumn("language", "Language", 80),
            TableColumn("version", "Version", 80),
            TableColumn("format", "Format", 80),
            TableColumn("size", "Size", 100),
            TableColumn("discs", "Discs", 60),
            TableColumn("hash", "Hash", 200),
        ]

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        return PlatformUtils.get_standard_file_type_support(supports_multi_part=True)

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get PlayStation 1-specific settings."""
        return [
            PlatformUtils.create_rom_directories_setting("PlayStation 1"),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting("PlayStation", [".iso", ".cue", ".bin", ".chd"]),
            PlatformUtils.create_supported_archives_setting(),
            PlatformSetting(
                key="prefer_cue_over_iso",
                label="Prefer CUE over ISO",
                description="When both CUE and ISO files are present, prioritize CUE files for better audio support",
                setting_type=SettingType.BOOLEAN,
                default_value=True
            ),
            PlatformSetting(
                key="disc_naming_format",
                label="Multi-disc Naming Format",
                description="How to detect and handle multi-disc games",
                setting_type=SettingType.CHOICE,
                default_value="Disc N",
                choices=["Disc N", "Disk N", "(Disc N)", "(Disk N)", "CD N", "(CD N)"]
            ),
            PlatformUtils.create_max_file_size_setting(default_mb=800, min_mb=100, max_mb=2000)
        ]

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        extension = file_path.suffix.lower()

        # Determine format based on extension
        if extension == ".iso":
            format_type = "ISO"
        elif extension == ".chd":
            format_type = "CHD"
        else:
            format_type = "CUE/BIN"

        # Try to extract disc information
        discs = 1
        filename_lower = file_path.stem.lower()
        if "disc" in filename_lower:
            if "disc 2" in filename_lower or "disk 2" in filename_lower:
                discs = 2
            elif "disc 3" in filename_lower or "disk 3" in filename_lower:
                discs = 3
            elif "disc 4" in filename_lower or "disk 4" in filename_lower:
                discs = 4

        return PlatformUtils.create_base_metadata(file_path, format=format_type, discs=discs)

    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        valid_extensions = [".iso", ".cue", ".bin", ".chd"]

        # Check file exists and has correct extension
        if not PlatformUtils.validate_file_exists_and_extension(file_path, valid_extensions):
            return False

        extension = file_path.suffix.lower()

        # For .cue files, check if associated .bin files exist
        if extension == ".cue":
            return self._validate_cue_file(file_path)

        # CHD files can be larger, so use different size limits
        if extension == ".chd":
            return PlatformUtils.validate_file_size(file_path, 10 * 1024 * 1024, 1000 * 1024 * 1024)

        # Basic size check - PSX games are typically 100MB to 800MB
        return PlatformUtils.validate_file_size(file_path, 100 * 1024 * 1024, 800 * 1024 * 1024)

    def _validate_cue_file(self, cue_path: Path) -> bool:
        """Validate a .cue file and its associated .bin files."""
        try:
            with open(cue_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Look for FILE entries in the .cue file
            lines = content.split("\n")
            bin_files = []

            for line in lines:
                line = line.strip()
                if line.startswith("FILE") and ".bin" in line.lower():
                    # Extract filename from FILE line
                    parts = line.split('"')
                    if len(parts) >= 2:
                        bin_filename = parts[1]
                        bin_path = cue_path.parent / bin_filename
                        bin_files.append(bin_path)

            # Check if all referenced .bin files exist
            return all(bin_file.exists() for bin_file in bin_files)

        except (OSError, UnicodeDecodeError):
            return False

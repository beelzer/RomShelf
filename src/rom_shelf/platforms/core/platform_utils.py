"""Shared utilities for platform implementations."""

from pathlib import Path
from typing import Any

from .base_platform import PlatformFileTypeSupport, PlatformSetting, SettingType, TableColumn


class PlatformUtils:
    """Common utilities shared across all platform implementations."""

    @staticmethod
    def parse_region_from_filename(filename: str) -> str:
        """Extract region information from ROM filename with comprehensive pattern matching."""
        import re

        filename_lower = filename.lower()

        # Extract parenthetical content for region analysis
        parenthetical_matches = re.findall(r"\([^)]+\)", filename_lower)

        # Look for region indicators in all parenthetical content
        regions_found = []

        for match in parenthetical_matches:
            content = match.strip("()")

            # Skip revision numbers, version numbers, beta, prototype, etc.
            if any(
                skip_word in content
                for skip_word in [
                    "rev",
                    "sgb",
                    "enhanced",
                    "beta",
                    "proto",
                    "sample",
                    "v1.",
                    "v2.",
                    "v3.",
                    "version",
                ]
            ):
                continue

            # Multi-region patterns (check first for specificity)
            if "usa" in content and "europe" in content:
                if "japan" in content:
                    regions_found.append("USA/EUR/JPN")
                else:
                    regions_found.append("USA/EUR")
            elif "japan" in content and "usa" in content:
                regions_found.append("JPN/USA")
            elif "usa" in content and "australia" in content:
                regions_found.append("USA/AUS")
            elif "europe" in content and "australia" in content:
                regions_found.append("EUR/AUS")

            # Single region patterns
            elif "usa" in content or content == "u":
                regions_found.append("USA")
            elif "europe" in content or content == "e":
                regions_found.append("EUR")
            elif "japan" in content or content == "j":
                regions_found.append("JPN")
            elif "world" in content or content == "w":
                regions_found.append("World")
            elif "australia" in content:
                regions_found.append("AUS")
            elif "germany" in content or content == "g":
                regions_found.append("GER")
            elif "france" in content or content == "f":
                regions_found.append("FRA")
            elif "italy" in content:
                regions_found.append("ITA")
            elif "spain" in content:
                regions_found.append("SPA")
            elif "korea" in content:
                regions_found.append("KOR")
            elif "brazil" in content:
                regions_found.append("BRA")
            elif "asia" in content:
                regions_found.append("Asia")
            elif "prototype" in content:
                regions_found.append("Prototype")

        # Return the most specific region found, or derive from language codes
        if regions_found:
            # Prefer multi-region over single region for better accuracy
            multi_regions = [r for r in regions_found if "/" in r]
            if multi_regions:
                return multi_regions[0]  # Return first multi-region match
            else:
                return regions_found[0]  # Return first single region match

        # Fallback: check for language-only indicators
        for match in parenthetical_matches:
            content = match.strip("()")
            if content.startswith("en") and "ja" not in content:
                return "USA"  # English often implies USA release
            elif "ja" in content:
                return "JPN"

        return "Unknown"

    @staticmethod
    def parse_version_from_filename(filename: str) -> str:
        """Extract version information from ROM filename."""
        import re

        filename_lower = filename.lower()

        # Look for version patterns
        version_patterns = [
            r"\(v(\d+\.\d+)\)",  # (V1.2)
            r"\(v(\d+)\)",  # (V1)
            r"\(version\s+(\d+\.\d+)\)",  # (Version 1.1)
        ]

        for pattern in version_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                return f"v{match.group(1)}"

        return ""

    @staticmethod
    def parse_dump_status_from_filename(filename: str) -> str:
        """Extract dump status from ROM filename."""

        # Look for dump status indicators
        if "[!]" in filename:
            return "Verified"
        elif "[a]" in filename:
            return "Alternative"
        elif "[b]" in filename:
            return "Bad Dump"
        elif "[h]" in filename:
            return "Hack"
        elif "[o]" in filename:
            return "Overdump"
        elif "[t]" in filename:
            return "Trained"
        elif "[f]" in filename:
            return "Fixed"
        elif "beta" in filename.lower():
            return "Beta"
        elif "proto" in filename.lower():
            return "Prototype"

        return ""

    @staticmethod
    def get_standard_archive_formats() -> list[str]:
        """Get the standard archive formats supported by all platforms."""
        return [".zip", ".7z", ".rar"]

    @staticmethod
    def validate_file_size(file_path: Path, min_size: int, max_size: int) -> bool:
        """Validate file size is within expected range."""
        try:
            file_size = file_path.stat().st_size
            return min_size <= file_size <= max_size
        except (OSError, FileNotFoundError):
            return False

    @staticmethod
    def create_base_metadata(file_path: Path, **extra_fields: Any) -> dict[str, Any]:
        """Create base metadata dictionary with common fields."""
        metadata = {
            "name": file_path.stem,
            "region": PlatformUtils.parse_region_from_filename(file_path.stem),
            **extra_fields,
        }
        return metadata

    @staticmethod
    def validate_file_exists_and_extension(file_path: Path, valid_extensions: list[str]) -> bool:
        """Validate file exists and has correct extension."""
        if not file_path.exists():
            return False

        extension = file_path.suffix.lower()
        return extension in valid_extensions

    # =================================================================
    # Factory methods for reducing platform code duplication
    # =================================================================

    @staticmethod
    def get_standard_handheld_columns() -> list[TableColumn]:
        """Get standard table columns for handheld gaming platforms (GB, GBC, GBA)."""
        return [
            TableColumn("name", "Name", 300),  # Will stretch, width is minimum
            TableColumn("region", "Region", 100),
            TableColumn("language", "Language", 100),
            TableColumn("version", "Version", 90),
            TableColumn("size", "Size", 100),
            TableColumn("hash", "Hash", 160),
        ]

    @staticmethod
    def get_standard_console_columns() -> list[TableColumn]:
        """Get standard table columns for console gaming platforms (N64, etc)."""
        return [
            TableColumn("name", "Name", 300),  # Will stretch, width is minimum
            TableColumn("region", "Region", 100),
            TableColumn("language", "Language", 100),
            TableColumn("version", "Version", 90),
            TableColumn("size", "Size", 100),
            TableColumn("file_type", "Type", 80),
            TableColumn("hash", "Hash", 160),
        ]

    @staticmethod
    def get_standard_file_type_support(
        supports_multi_part: bool = False,
    ) -> PlatformFileTypeSupport:
        """Get standard file type support configuration."""
        return PlatformFileTypeSupport(
            supports_archives=True, supports_multi_part=supports_multi_part, supports_normal=True
        )

    @staticmethod
    def create_handlers_list(platform_extensions: list[str]) -> list[str]:
        """Create handlers list combining platform extensions with standard archives."""
        return platform_extensions + PlatformUtils.get_standard_archive_formats()

    @staticmethod
    def create_rom_directories_setting(platform_name: str) -> PlatformSetting:
        """Create standard ROM directories setting."""
        return PlatformSetting(
            key="rom_directories",
            label="ROM Directories",
            description=f"Directories to scan for {platform_name} ROMs",
            setting_type=SettingType.DIRECTORY_LIST,
            default_value=[],
            required=False,
        )

    @staticmethod
    def create_scan_subdirectories_setting() -> PlatformSetting:
        """Create standard scan subdirectories setting."""
        return PlatformSetting(
            key="scan_subdirectories",
            label="Scan Subdirectories",
            description="Include subdirectories when scanning for ROMs",
            setting_type=SettingType.BOOLEAN,
            default_value=True,
        )

    @staticmethod
    def create_supported_formats_setting(platform_name: str, formats: list[str]) -> PlatformSetting:
        """Create standard supported formats setting."""
        return PlatformSetting(
            key="supported_formats",
            label="Supported ROM Formats",
            description=f"Enable or disable support for specific {platform_name} ROM formats",
            setting_type=SettingType.FORMAT_LIST,
            default_value=formats,
            choices=formats,
        )

    @staticmethod
    def create_supported_archives_setting() -> PlatformSetting:
        """Create standard supported archives setting."""
        return PlatformSetting(
            key="supported_archives",
            label="Supported Archive Formats",
            description="Enable or disable support for specific archive formats",
            setting_type=SettingType.FORMAT_LIST,
            default_value=PlatformUtils.get_standard_archive_formats(),
            choices=PlatformUtils.get_standard_archive_formats(),
        )

    @staticmethod
    def create_header_validation_setting() -> PlatformSetting:
        """Create standard header validation setting."""
        return PlatformSetting(
            key="header_validation",
            label="Validate ROM Headers",
            description="Perform header validation to ensure ROM integrity",
            setting_type=SettingType.BOOLEAN,
            default_value=True,
        )

    @staticmethod
    def create_max_file_size_setting(
        default_mb: int, min_mb: int = 1, max_mb: int = 128
    ) -> PlatformSetting:
        """Create standard maximum file size setting."""
        return PlatformSetting(
            key="max_file_size_mb",
            label="Maximum File Size (MB)",
            description="Maximum allowed file size for ROMs",
            setting_type=SettingType.INTEGER,
            default_value=default_mb,
            min_value=min_mb,
            max_value=max_mb,
        )

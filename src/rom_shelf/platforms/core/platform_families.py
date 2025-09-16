"""Platform family templates for common platform types."""

from abc import abstractmethod
from enum import Enum
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
from .validation import ExtensionValidator, FileExistsValidator, FileSizeValidator, ValidationChain


class PlatformFamily(Enum):
    """Categories of gaming platforms."""

    HANDHELD = "handheld"
    CONSOLE = "console"
    COMPUTER = "computer"
    ARCADE = "arcade"
    DISC_BASED = "disc"


class CartridgeBasedPlatform(BasePlatform):
    """Base class for cartridge-based gaming platforms."""

    def __init__(self) -> None:
        """Initialize cartridge platform."""
        super().__init__()
        self._validation_chain = self._create_validation_chain()

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Cartridges typically don't support multi-part files."""
        return PlatformUtils.get_standard_file_type_support(supports_multi_part=False)

    def get_table_columns(self) -> list[TableColumn]:
        """Get standard cartridge platform columns."""
        family = self.get_platform_family()
        if family == PlatformFamily.HANDHELD:
            return PlatformUtils.get_standard_handheld_columns()
        else:
            return PlatformUtils.get_standard_console_columns()

    def validate_rom(self, file_path: Path) -> bool:
        """Validate ROM using the validation chain."""
        return self._validation_chain.validate(file_path)

    def get_validation_failure_reason(self) -> str:
        """Get the reason for validation failure."""
        return self._validation_chain.get_failure_reason()

    def _create_validation_chain(self) -> ValidationChain:
        """Create the default validation chain for cartridge platforms."""
        chain = ValidationChain()
        chain.add_validator(FileExistsValidator())
        chain.add_validator(ExtensionValidator(self.get_archive_content_extensions()))

        # Add size validator with platform-specific limits
        min_size, max_size = self.get_expected_file_size_range()
        chain.add_validator(FileSizeValidator(min_size, max_size))

        return chain

    @abstractmethod
    def get_platform_family(self) -> PlatformFamily:
        """Get the platform family type."""
        pass

    @abstractmethod
    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range (min_bytes, max_bytes)."""
        pass

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get standard cartridge platform settings."""
        platform_name = self.get_platform_name()
        extensions = self.get_archive_content_extensions()

        settings = [
            PlatformUtils.create_rom_directories_setting(platform_name),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting(platform_name, extensions),
            PlatformUtils.create_supported_archives_setting(),
            PlatformUtils.create_header_validation_setting(),
        ]

        # Add max file size setting based on platform limits
        _, max_size = self.get_expected_file_size_range()
        max_mb = max(max_size // (1024 * 1024), 1)
        settings.append(
            PlatformUtils.create_max_file_size_setting(default_mb=max_mb, max_mb=max_mb * 2)
        )

        return settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse basic ROM information for cartridge platforms."""
        return PlatformUtils.create_base_metadata(
            file_path, file_type=file_path.suffix.upper(), family=self.get_platform_family().value
        )


class DiscBasedPlatform(BasePlatform):
    """Base class for disc-based gaming platforms."""

    def __init__(self) -> None:
        """Initialize disc platform."""
        super().__init__()
        self._validation_chain = self._create_validation_chain()

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Discs support multi-part files (multiple discs)."""
        return PlatformUtils.get_standard_file_type_support(supports_multi_part=True)

    def get_table_columns(self) -> list[TableColumn]:
        """Get standard disc platform columns."""
        return [
            TableColumn("name", "Name", 300),
            TableColumn("region", "Region", 100),
            TableColumn("language", "Language", 100),
            TableColumn("version", "Version", 90),
            TableColumn("format", "Format", 80),
            TableColumn("size", "Size", 100),
            TableColumn("discs", "Discs", 70),
            TableColumn("hash", "Hashes", 160),
        ]

    def validate_rom(self, file_path: Path) -> bool:
        """Validate ROM using the validation chain."""
        return self._validation_chain.validate(file_path)

    def get_validation_failure_reason(self) -> str:
        """Get the reason for validation failure."""
        return self._validation_chain.get_failure_reason()

    def _create_validation_chain(self) -> ValidationChain:
        """Create the default validation chain for disc platforms."""
        from .validation import CueFileValidator

        chain = ValidationChain()
        chain.add_validator(FileExistsValidator())
        chain.add_validator(ExtensionValidator(self.get_archive_content_extensions()))
        chain.add_validator(CueFileValidator())

        # Add size validator with platform-specific limits
        min_size, max_size = self.get_expected_file_size_range()
        chain.add_validator(FileSizeValidator(min_size, max_size))

        return chain

    def get_platform_family(self) -> PlatformFamily:
        """Disc-based platforms are part of the disc family."""
        return PlatformFamily.DISC_BASED

    @abstractmethod
    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range (min_bytes, max_bytes)."""
        pass

    @abstractmethod
    def get_disc_formats(self) -> list[str]:
        """Get supported disc formats (e.g., ['.iso', '.cue', '.bin'])."""
        pass

    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get standard disc platform settings."""
        platform_name = self.get_platform_name()
        extensions = self.get_archive_content_extensions()

        settings = [
            PlatformUtils.create_rom_directories_setting(platform_name),
            PlatformUtils.create_scan_subdirectories_setting(),
            PlatformUtils.create_supported_formats_setting(platform_name, extensions),
            PlatformUtils.create_supported_archives_setting(),
            # Disc-specific settings
            PlatformSetting(
                key="multi_disc_detection",
                label="Multi-disc Game Detection",
                description="Automatically detect and group multi-disc games",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
            ),
        ]

        # Add max file size setting based on platform limits
        _, max_size = self.get_expected_file_size_range()
        max_mb = max(max_size // (1024 * 1024), 100)
        settings.append(
            PlatformUtils.create_max_file_size_setting(default_mb=max_mb // 2, max_mb=max_mb)
        )

        return settings

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information for disc platforms."""
        extension = file_path.suffix.lower()

        # Determine format based on extension
        format_type = self._get_format_from_extension(extension)

        # Try to extract disc information
        discs = self._detect_disc_count(file_path)

        return PlatformUtils.create_base_metadata(
            file_path, format=format_type, discs=discs, family=PlatformFamily.DISC_BASED.value
        )

    def _get_format_from_extension(self, extension: str) -> str:
        """Get display format from file extension."""
        format_map = {
            ".iso": "ISO",
            ".chd": "CHD",
            ".cue": "CUE/BIN",
            ".bin": "CUE/BIN",
            ".mds": "MDS/MDF",
            ".mdf": "MDS/MDF",
        }
        return format_map.get(extension, extension.upper())

    def _detect_disc_count(self, file_path: Path) -> int:
        """Detect number of discs from filename."""
        filename_lower = file_path.stem.lower()

        # Look for disc indicators
        disc_patterns = ["disc", "disk", "cd"]
        for pattern in disc_patterns:
            if f"{pattern} 2" in filename_lower:
                return 2
            elif f"{pattern} 3" in filename_lower:
                return 3
            elif f"{pattern} 4" in filename_lower:
                return 4

        return 1


class HandheldPlatform(CartridgeBasedPlatform):
    """Base class for handheld gaming platforms."""

    def get_platform_family(self) -> PlatformFamily:
        """Handheld platforms are part of the handheld family."""
        return PlatformFamily.HANDHELD

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Default size range for handheld platforms."""
        return (32 * 1024, 32 * 1024 * 1024)  # 32KB to 32MB


class ConsolePlatform(CartridgeBasedPlatform):
    """Base class for console gaming platforms."""

    def get_platform_family(self) -> PlatformFamily:
        """Console platforms are part of the console family."""
        return PlatformFamily.CONSOLE

    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Default size range for console platforms."""
        return (1024 * 1024, 64 * 1024 * 1024)  # 1MB to 64MB


class ComputerPlatform(BasePlatform):
    """Base class for computer/PC gaming platforms."""

    def get_platform_family(self) -> PlatformFamily:
        """Computer platforms are part of the computer family."""
        return PlatformFamily.COMPUTER

    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Computers support all file types."""
        return PlatformUtils.get_standard_file_type_support(supports_multi_part=True)

    def get_table_columns(self) -> list[TableColumn]:
        """Get standard computer platform columns."""
        return [
            TableColumn("name", "Name", 300),
            TableColumn("region", "Region", 100),
            TableColumn("format", "Format", 100),
            TableColumn("version", "Version", 90),
            TableColumn("size", "Size", 100),
            TableColumn("hash", "Hashes", 160),
        ]

    @abstractmethod
    def get_expected_file_size_range(self) -> tuple[int, int]:
        """Get expected file size range (min_bytes, max_bytes)."""
        pass

    def validate_rom(self, file_path: Path) -> bool:
        """Basic validation for computer platforms."""
        return PlatformUtils.validate_file_exists_and_extension(
            file_path, self.get_archive_content_extensions()
        ) and PlatformUtils.validate_file_size(file_path, *self.get_expected_file_size_range())

    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse basic ROM information for computer platforms."""
        return PlatformUtils.create_base_metadata(
            file_path, format=file_path.suffix.upper(), family=PlatformFamily.COMPUTER.value
        )

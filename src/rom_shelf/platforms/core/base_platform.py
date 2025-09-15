"""Base platform class for ROM platforms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ...models.rom_entry import ROMEntry


class SettingType(Enum):
    """Types of settings that platforms can define."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    CHOICE = "choice"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    DIRECTORY_LIST = "directory_list"  # List of directories with add/remove buttons
    FORMAT_LIST = "format_list"  # List of file formats with individual checkboxes


@dataclass
class PlatformSetting:
    """Defines a single platform setting."""

    key: str  # Internal key for the setting
    label: str  # Display label in UI
    description: str  # Help text/tooltip
    setting_type: SettingType  # Type of setting
    default_value: Any  # Default value
    choices: list[str] | None = None  # For CHOICE type or FORMAT_LIST options
    min_value: int | float | None = None  # For INTEGER/FLOAT
    max_value: int | float | None = None  # For INTEGER/FLOAT
    required: bool = True  # Whether setting is required


@dataclass
class PlatformFileTypeSupport:
    """Defines what file types a platform supports."""

    supports_archives: bool = True
    supports_multi_part: bool = True
    supports_normal: bool = True


@dataclass
class TableColumn:
    """Represents a table column configuration."""

    key: str
    label: str
    width: int = 200


class BasePlatform(ABC):
    """Base class for all ROM platforms."""

    def __init__(self) -> None:
        """Initialize the platform."""
        self._name = self.get_platform_name()
        self._platform_id = self.get_platform_id()
        self._supported_handlers = self.get_supported_handlers()
        self._archive_content_extensions = self.get_archive_content_extensions()
        self._table_columns = self.get_table_columns()
        self._file_type_support = self.get_file_type_support()

    @property
    def name(self) -> str:
        """Platform display name."""
        return self._name

    @property
    def platform_id(self) -> str:
        """Unique platform identifier."""
        return self._platform_id

    @property
    def supported_handlers(self) -> list[str]:
        """List of supported extension handlers."""
        return self._supported_handlers

    @property
    def archive_content_extensions(self) -> list[str]:
        """Extensions to look for inside archives."""
        return self._archive_content_extensions

    @property
    def table_columns(self) -> list[TableColumn]:
        """Table column configuration."""
        return self._table_columns

    @property
    def file_type_support(self) -> PlatformFileTypeSupport:
        """File type support configuration."""
        return self._file_type_support

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get the display name of the platform."""
        pass

    @abstractmethod
    def get_platform_id(self) -> str:
        """Get the unique identifier for the platform."""
        pass

    @abstractmethod
    def get_supported_handlers(self) -> list[str]:
        """Get list of supported extension handler names."""
        pass

    @abstractmethod
    def register_extensions(self, registry) -> None:
        """Register platform-specific extension handlers."""
        pass

    @abstractmethod
    def get_archive_content_extensions(self) -> list[str]:
        """Get extensions to look for inside archives."""
        pass

    @abstractmethod
    def get_table_columns(self) -> list[TableColumn]:
        """Get table column configuration."""
        pass

    @abstractmethod
    def get_file_type_support(self) -> PlatformFileTypeSupport:
        """Get file type support configuration."""
        pass

    @abstractmethod
    def get_platform_settings(self) -> list[PlatformSetting]:
        """Get platform-specific settings definitions."""
        pass

    @abstractmethod
    def parse_rom_info(self, file_path: Path) -> dict[str, Any]:
        """Parse ROM information from file."""
        pass

    def find_multi_file_primary(self, file_path: Path) -> Path | None:
        """Find the primary file for a multi-file ROM set."""
        # Default implementation: no multi-file support
        return None

    def get_related_files(self, primary_file: Path) -> list[Path]:
        """Get all files that are part of this multi-file ROM."""
        # Default implementation: only the primary file
        return [primary_file]

    def is_multi_file_primary(self, file_path: Path) -> bool:
        """Check if file is a primary file in a multi-file set."""
        # Default implementation: no multi-file support
        return False

    @abstractmethod
    def validate_rom(self, file_path: Path) -> bool:
        """Validate if file is a valid ROM for this platform."""
        pass

    def get_validation_failure_reason(self) -> str:
        """Get the reason for validation failure (optional)."""
        return "ROM validation failed"

    def create_rom_entry(
        self,
        file_path: Path,
        internal_path: str | None = None,
        is_archive: bool = False,
        related_files: list[Path] | None = None,
    ) -> ROMEntry:
        """Create a ROM entry for this platform."""
        if related_files is None:
            related_files = []

        # Parse ROM information
        metadata = self.parse_rom_info(file_path)

        # Generate display name from metadata or filename
        original_name = metadata.get("name", file_path.stem)

        # Clean the display name and extract additional metadata
        from ...utils.name_cleaner import get_display_name_and_metadata

        display_name, extracted_metadata = get_display_name_and_metadata(original_name)

        # Merge extracted metadata with platform-specific metadata
        metadata.update(extracted_metadata)

        # Get file size
        file_size = 0
        try:
            file_size = file_path.stat().st_size
        except (OSError, FileNotFoundError):
            pass

        # Skip MD5 calculation during initial scan for performance
        # MD5 will be calculated in background after scan completes
        return ROMEntry(
            platform_id=self.platform_id,
            display_name=display_name,
            file_path=file_path,
            internal_path=internal_path,
            file_size=file_size,
            is_archive=is_archive,
            related_files=related_files,
            metadata=metadata,
        )

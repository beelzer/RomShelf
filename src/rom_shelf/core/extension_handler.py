"""Extension handler system for different file types."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileHandlingType(Enum):
    """Types of file handling strategies."""

    DIRECT = "direct"  # Single file, use as-is
    ARCHIVE = "archive"  # Needs extraction (7z, zip, rar)
    MULTI_FILE = "multi_file"  # Multiple related files (cue+bin)


@dataclass
class ExtensionHandler:
    """Handler for a specific file extension."""

    extension: str
    handling_type: FileHandlingType
    associated_extensions: list[str] | None = None  # For multi-file formats
    extract_filter: list[str] | None = None  # Which files to extract from archives

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.associated_extensions is None:
            self.associated_extensions = []
        if self.extract_filter is None:
            self.extract_filter = []


class ExtensionHandlerRegistry:
    """Registry for managing extension handlers."""

    def __init__(self) -> None:
        """Initialize the registry with default handlers."""
        self._handlers: dict[str, ExtensionHandler] = {}
        self._initialize_archive_handlers()

    def _initialize_archive_handlers(self) -> None:
        """Set up archive format handlers (platform-agnostic)."""
        # Archive formats - these are platform-agnostic
        self.register_handler(ExtensionHandler(".zip", FileHandlingType.ARCHIVE))
        self.register_handler(ExtensionHandler(".7z", FileHandlingType.ARCHIVE))
        self.register_handler(ExtensionHandler(".rar", FileHandlingType.ARCHIVE))

    def register_handler(self, handler: ExtensionHandler) -> None:
        """Register an extension handler."""
        self._handlers[handler.extension.lower()] = handler

    def register_platform_extensions(self, platform) -> None:
        """Register extensions for a platform instance."""
        if hasattr(platform, "register_extensions"):
            platform.register_extensions(self)

    def get_handler(self, extension: str) -> ExtensionHandler | None:
        """Get handler for an extension."""
        return self._handlers.get(extension.lower())

    def get_handler_for_file(self, file_path: Path) -> ExtensionHandler | None:
        """Get handler for a file path."""
        return self.get_handler(file_path.suffix)

    def is_supported_extension(self, extension: str) -> bool:
        """Check if an extension is supported."""
        return extension.lower() in self._handlers

    def is_archive_extension(self, extension: str) -> bool:
        """Check if an extension is an archive format."""
        handler = self.get_handler(extension)
        return handler is not None and handler.handling_type == FileHandlingType.ARCHIVE

    def is_direct_extension(self, extension: str) -> bool:
        """Check if an extension is a direct format."""
        handler = self.get_handler(extension)
        return handler is not None and handler.handling_type == FileHandlingType.DIRECT

    def is_multi_file_extension(self, extension: str) -> bool:
        """Check if an extension is a multi-file format."""
        handler = self.get_handler(extension)
        return handler is not None and handler.handling_type == FileHandlingType.MULTI_FILE

    def get_archive_extensions(self) -> list[str]:
        """Get all archive extensions."""
        return [
            ext
            for ext, handler in self._handlers.items()
            if handler.handling_type == FileHandlingType.ARCHIVE
        ]

    def get_direct_extensions(self) -> list[str]:
        """Get all direct extensions."""
        return [
            ext
            for ext, handler in self._handlers.items()
            if handler.handling_type == FileHandlingType.DIRECT
        ]

    def get_multi_file_extensions(self) -> list[str]:
        """Get all multi-file extensions."""
        return [
            ext
            for ext, handler in self._handlers.items()
            if handler.handling_type == FileHandlingType.MULTI_FILE
        ]


# Global registry instance
extension_registry = ExtensionHandlerRegistry()

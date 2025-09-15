"""ROM validation system with chain architecture."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ROMValidator(ABC):
    """Abstract base class for ROM validators."""

    @abstractmethod
    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """
        Validate a ROM file.

        Args:
            file_path: Path to the ROM file
            metadata: Optional metadata dictionary for context

        Returns:
            True if validation passes, False otherwise
        """
        pass

    @abstractmethod
    def get_error_message(self) -> str:
        """Get the error message if validation fails."""
        pass


class ValidationChain:
    """Manages a chain of ROM validators."""

    def __init__(self, validators: list[ROMValidator] | None = None) -> None:
        """Initialize with optional list of validators."""
        self.validators = validators or []
        self._last_failed_validator: ROMValidator | None = None

    def add_validator(self, validator: ROMValidator) -> None:
        """Add a validator to the chain."""
        self.validators.append(validator)

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """
        Run all validators in the chain.

        Returns True if all validators pass, False if any fail.
        """
        self._last_failed_validator = None

        for validator in self.validators:
            if not validator.validate(file_path, metadata):
                self._last_failed_validator = validator
                return False

        return True

    def get_failure_reason(self) -> str:
        """Get the error message from the last failed validator."""
        if self._last_failed_validator:
            return self._last_failed_validator.get_error_message()
        return "Unknown validation error"


# Common validators
class ExtensionValidator(ROMValidator):
    """Validates file extension."""

    def __init__(self, valid_extensions: list[str]) -> None:
        """Initialize with list of valid extensions."""
        self.valid_extensions = [ext.lower() for ext in valid_extensions]

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate file extension."""
        return file_path.suffix.lower() in self.valid_extensions

    def get_error_message(self) -> str:
        """Get error message."""
        return f"Invalid file extension. Expected one of: {', '.join(self.valid_extensions)}"


class FileExistsValidator(ROMValidator):
    """Validates that file exists."""

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate file exists."""
        return file_path.exists()

    def get_error_message(self) -> str:
        """Get error message."""
        return "File does not exist"


class FileSizeValidator(ROMValidator):
    """Validates file size is within expected range."""

    def __init__(self, min_size: int, max_size: int) -> None:
        """
        Initialize with size limits.

        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
        """
        self.min_size = min_size
        self.max_size = max_size

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate file size."""
        try:
            file_size = file_path.stat().st_size
            return self.min_size <= file_size <= self.max_size
        except (OSError, FileNotFoundError):
            return False

    def get_error_message(self) -> str:
        """Get error message."""
        return f"File size must be between {self.min_size:,} and {self.max_size:,} bytes"


class HeaderMagicValidator(ROMValidator):
    """Validates ROM header magic bytes."""

    def __init__(self, magic_bytes: bytes, offset: int = 0) -> None:
        """
        Initialize with magic bytes to check.

        Args:
            magic_bytes: Expected magic bytes
            offset: Byte offset where magic bytes should appear
        """
        self.magic_bytes = magic_bytes
        self.offset = offset

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate header magic bytes."""
        try:
            with open(file_path, "rb") as f:
                f.seek(self.offset)
                actual_bytes = f.read(len(self.magic_bytes))
                return actual_bytes == self.magic_bytes
        except OSError:
            return False

    def get_error_message(self) -> str:
        """Get error message."""
        magic_hex = self.magic_bytes.hex().upper()
        return f"Invalid header magic bytes. Expected: {magic_hex} at offset {self.offset}"


class HeaderChecksumValidator(ROMValidator):
    """Validates ROM header checksum."""

    def __init__(self, checksum_offset: int, checksum_size: int = 2) -> None:
        """
        Initialize checksum validator.

        Args:
            checksum_offset: Byte offset of checksum in header
            checksum_size: Size of checksum in bytes (2 or 4)
        """
        self.checksum_offset = checksum_offset
        self.checksum_size = checksum_size

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate header checksum (implementation varies by platform)."""
        # This is a base implementation - platforms should override with specific logic
        try:
            with open(file_path, "rb") as f:
                f.seek(self.checksum_offset)
                checksum_bytes = f.read(self.checksum_size)
                return len(checksum_bytes) == self.checksum_size
        except OSError:
            return False

    def get_error_message(self) -> str:
        """Get error message."""
        return "Invalid header checksum"


class CueFileValidator(ROMValidator):
    """Validates CUE files and their associated BIN files."""

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate CUE file and associated BIN files."""
        if file_path.suffix.lower() != ".cue":
            return True  # Not a CUE file, validation passes

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
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
                        bin_path = file_path.parent / bin_filename
                        bin_files.append(bin_path)

            # Check if all referenced .bin files exist
            return all(bin_file.exists() for bin_file in bin_files)

        except (OSError, UnicodeDecodeError):
            return False

    def get_error_message(self) -> str:
        """Get error message."""
        return "CUE file references missing BIN files"


# Platform-specific validators can be created by inheriting from ROMValidator
class GameBoyHeaderValidator(ROMValidator):
    """Validates Game Boy ROM header."""

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate Game Boy header."""
        try:
            with open(file_path, "rb") as f:
                # Check Nintendo logo at 0x104-0x133 (partial check)
                f.seek(0x104)
                logo_start = f.read(4)
                # Game Boy logo starts with specific bytes
                return logo_start == b"\xce\xed\x66\x66"
        except OSError:
            return False

    def get_error_message(self) -> str:
        """Get error message."""
        return "Invalid Game Boy header - missing Nintendo logo"


class N64HeaderValidator(ROMValidator):
    """Validates Nintendo 64 ROM header."""

    def validate(self, file_path: Path, metadata: dict[str, Any] | None = None) -> bool:
        """Validate N64 header."""
        try:
            with open(file_path, "rb") as f:
                # Check for valid N64 header magic
                f.seek(0)
                header = f.read(4)

                # Different formats have different byte orders
                valid_headers = [
                    b"\x80\x37\x12\x40",  # .z64 (big-endian)
                    b"\x37\x80\x40\x12",  # .v64 (byteswapped)
                    b"\x40\x12\x37\x80",  # .n64 (little-endian)
                ]

                return header in valid_headers
        except OSError:
            return False

    def get_error_message(self) -> str:
        """Get error message."""
        return "Invalid Nintendo 64 ROM header"

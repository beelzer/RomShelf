"""ROM entry data model."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ROMEntry:
    """Represents a ROM file entry."""

    platform_id: str
    display_name: str
    file_path: Path
    internal_path: str | None = None  # Path within archive if applicable
    file_size: int = 0
    is_archive: bool = False
    related_files: list[Path] = field(default_factory=list)  # For multi-file ROMs
    metadata: dict[str, Any] = field(default_factory=dict)  # Platform-specific fields

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)

        # Convert string paths in related_files to Path objects
        self.related_files = [Path(f) if isinstance(f, str) else f for f in self.related_files]

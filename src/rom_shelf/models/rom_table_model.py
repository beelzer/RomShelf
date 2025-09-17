"""Table model for displaying ROM entries."""

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from ..core.rom_database import get_rom_database
from ..platforms.core.base_platform import TableColumn
from .rom_entry import ROMEntry


class ROMTableModel(QAbstractTableModel):
    """Table model for ROM entries."""

    def __init__(self, parent: Any | None = None) -> None:
        """Initialize the table model."""
        super().__init__(parent)
        self._rom_entries: list[ROMEntry] = []
        self._columns: list[TableColumn] = []
        self._filtered_entries: list[ROMEntry] = []
        self._platform_filter: list[str] = []  # Platform IDs to show
        self._search_filter: str = ""  # Search text filter

    def set_columns(self, columns: list[TableColumn]) -> None:
        """Set the table columns."""
        self.beginResetModel()
        self._columns = columns
        self.endResetModel()

    def set_rom_entries(self, entries: list[ROMEntry]) -> None:
        """Set the ROM entries."""
        self.beginResetModel()
        self._rom_entries = entries
        self._apply_filter()
        self.endResetModel()

    def add_rom_entries(self, entries: list[ROMEntry]) -> None:
        """Add ROM entries to the model."""
        if not entries:
            return

        # Always add all entries to the underlying data
        self._rom_entries.extend(entries)

        # Filter entries based on current platform filter for display
        filtered_entries = [
            entry
            for entry in entries
            if not self._platform_filter or entry.platform_id in self._platform_filter
        ]

        if not filtered_entries:
            return

        start_row = len(self._filtered_entries)
        end_row = start_row + len(filtered_entries) - 1

        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self._filtered_entries.extend(filtered_entries)
        self.endInsertRows()

    def clear(self) -> None:
        """Clear all ROM entries."""
        self.beginResetModel()
        self._rom_entries.clear()
        self._filtered_entries.clear()
        self.endResetModel()

    def set_platform_filter(self, platform_ids: list[str]) -> None:
        """Set which platforms to show."""
        self.beginResetModel()
        self._platform_filter = platform_ids
        self._apply_filter()
        self.endResetModel()

    def set_search_filter(self, search_text: str) -> None:
        """Set the search text filter."""
        self.beginResetModel()
        self._search_filter = search_text.lower().strip()
        self._apply_filter()
        self.endResetModel()

    def _apply_filter(self) -> None:
        """Apply the current platform and search filters."""
        # Start with all entries
        filtered_entries = self._rom_entries.copy()

        # Apply platform filter
        if self._platform_filter:
            filtered_entries = [
                entry for entry in filtered_entries if entry.platform_id in self._platform_filter
            ]

        # Apply search filter
        if self._search_filter:
            filtered_entries = [
                entry
                for entry in filtered_entries
                if self._matches_search(entry, self._search_filter)
            ]

        self._filtered_entries = filtered_entries

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        """Return the number of rows."""
        return len(self._filtered_entries)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        """Return the number of columns."""
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid() or index.row() >= len(self._filtered_entries):
            return None

        entry = self._filtered_entries[index.row()]
        column = self._columns[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(entry, column.key)
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip_data(entry, column.key)
        elif role == Qt.ItemDataRole.UserRole:
            # Return raw sort data for Qt's sorting
            return self._get_sort_data(entry, column.key)
        elif role == Qt.ItemDataRole.UserRole + 1:
            # Return the ROM entry itself for custom delegates
            return entry
        elif role == Qt.ItemDataRole.UserRole + 10:
            # Return RA game ID for achievement delegate
            return self._get_ra_game_id(entry)
        elif role == Qt.ItemDataRole.UserRole + 11:
            # Return user progress for achievement delegate
            return self._get_ra_user_progress(entry)

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Return header data."""
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self._columns)
        ):
            return self._columns[section].label
        return None

    def _get_display_data(self, entry: ROMEntry, key: str) -> str:
        """Get display data for a ROM entry field."""
        if key == "actions":
            return ""  # Actions column is handled by custom delegate
        elif key == "achievements":
            return ""  # Achievements column is handled by custom delegate
        elif key == "name":
            return entry.display_name
        elif key == "size":
            return self._format_file_size(entry.file_size)
        elif key == "platform":
            return entry.platform_id.upper()
        elif key == "hash":
            return self._get_rom_hash(entry)
        elif key == "region":
            # Region display is handled by the delegate
            return ""
        elif key == "language":
            # Return the language data as fallback if delegate doesn't work
            # The delegate should override this display
            return entry.metadata.get("language", "")
        elif key in entry.metadata:
            # Return any other metadata field
            return str(entry.metadata.get(key, ""))
        else:
            return ""

    def _get_tooltip_data(self, entry: ROMEntry, key: str) -> str:
        """Get tooltip data for a ROM entry field."""
        if key == "actions":
            return "Action column"
        elif key == "achievements":
            ra_id = self._get_ra_game_id(entry)
            if ra_id:
                return "Click to open RetroAchievements page"
            return "No RetroAchievements data"
        elif key == "name":
            tooltip_parts = [f"File: {entry.file_path}"]
            if entry.internal_path:
                tooltip_parts.append(f"Internal: {entry.internal_path}")
            if entry.related_files:
                related_str = ", ".join(f.name for f in entry.related_files)
                tooltip_parts.append(f"Related: {related_str}")
            return "\n".join(tooltip_parts)
        elif key == "hash":
            # Hash column tooltips are handled by the custom delegate
            return ""
        elif key == "region":
            # Region column tooltips are handled by the custom delegate
            return ""
        elif key == "language":
            # Language column tooltips are handled by the custom delegate
            return ""
        return self._get_display_data(entry, key)

    def _get_sort_data(self, entry: ROMEntry, key: str) -> Any:
        """Get sort data for a ROM entry field."""
        if key == "actions":
            # Sort by name for actions column
            return entry.display_name.lower()
        elif key == "achievements":
            # Sort by completion percentage (highest completion first, then by name)
            user_progress = self._get_ra_user_progress(entry)
            ra_id = self._get_ra_game_id(entry)

            if not ra_id:
                # No RA data - sort to bottom
                return (999, entry.display_name.lower())
            elif user_progress:
                earned = user_progress.get("achievements_earned", 0)
                total = user_progress.get("achievements_total", 0)
                percentage = (earned / total * 100) if total > 0 else 0
                # Sort by percentage (descending), then by name (ascending)
                return (-percentage, entry.display_name.lower())
            else:
                # Has RA data but no progress data - treat as 0%
                return (0, entry.display_name.lower())
        elif key == "name":
            return entry.display_name.lower()
        elif key == "size":
            return entry.file_size  # Return numeric value for proper sorting
        elif key == "platform":
            return entry.platform_id.lower()
        elif key == "hash":
            return self._get_rom_hash(entry).lower()
        elif key in entry.metadata:
            value = entry.metadata[key]
            if isinstance(value, str):
                return value.lower()
            else:
                return value  # Return numeric values as-is
        else:
            return ""

    def _matches_search(self, entry: ROMEntry, search_text: str) -> bool:
        """Check if a ROM entry matches the search text."""
        # Search in display name
        if search_text in entry.display_name.lower():
            return True

        # Search in platform name
        from ..platforms.core.platform_registry import platform_registry

        platform = platform_registry.get_platform(entry.platform_id)
        if platform and search_text in platform.name.lower():
            return True

        # Search in metadata fields
        for key, value in entry.metadata.items():
            if search_text in str(value).lower():
                return True

        # Search in file name (without path)
        if search_text in entry.file_path.name.lower():
            return True

        return False

    def _get_rom_hash(self, entry: ROMEntry) -> str:
        """Get MD5 hash for a ROM entry from the database."""
        try:
            rom_db = get_rom_database()
            fingerprint = rom_db.get_fingerprint(entry.file_path, entry.internal_path)
            if fingerprint and fingerprint.md5_hash:
                return fingerprint.md5_hash
            return ""
        except Exception:
            return ""

    def _get_ra_game_id(self, entry: ROMEntry) -> int | None:
        """Get RetroAchievements game ID for a ROM entry."""
        try:
            rom_db = get_rom_database()
            fingerprint = rom_db.get_fingerprint(entry.file_path, entry.internal_path)
            if fingerprint and fingerprint.ra_game_id:
                return fingerprint.ra_game_id
            return None
        except Exception:
            return None

    def _get_ra_user_progress(self, entry: ROMEntry) -> dict | None:
        """Get user's achievement progress for a ROM entry.

        Returns dict with completion_percentage if available.
        """
        game_id = self._get_ra_game_id(entry)
        if not game_id:
            return None

        try:
            # Check if we have a configured username
            from pathlib import Path

            from ..core.settings import Settings

            settings_file = Path("data") / "settings.json"
            if not settings_file.exists():
                return None

            settings = Settings.load(settings_file)
            if not settings.ra_username:
                return None

            # Only get cached progress - don't trigger API calls from the model
            from ..services.ra_database import RetroAchievementsDatabase

            ra_db = RetroAchievementsDatabase(Path("data/retroachievements.db"))
            progress = ra_db.get_user_game_progress(settings.ra_username, game_id)

            return progress
        except Exception:
            return None

    def _format_file_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            kb = size / 1024
            if kb < 10:
                return f"{kb:.1f} KB"
            else:
                return f"{kb:.0f} KB"
        elif size < 1024 * 1024 * 1024:
            mb = size / (1024 * 1024)
            if mb < 10:
                return f"{mb:.1f} MB"
            else:
                return f"{mb:.0f} MB"
        else:
            gb = size / (1024 * 1024 * 1024)
            return f"{gb:.2f} GB"

    def get_rom_entry(self, index: QModelIndex) -> ROMEntry | None:
        """Get ROM entry at the given index."""
        if not index.isValid() or index.row() >= len(self._filtered_entries):
            return None
        return self._filtered_entries[index.row()]

    def get_all_rom_entries(self) -> list[ROMEntry]:
        """Get all ROM entries (unfiltered)."""
        return self._rom_entries.copy()

    def get_search_filtered_entries(self) -> list[ROMEntry]:
        """Get ROM entries filtered by search text only (ignoring platform filter)."""
        if not self._search_filter:
            return self._rom_entries.copy()

        return [
            entry for entry in self._rom_entries if self._matches_search(entry, self._search_filter)
        ]

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort the table by the given column."""
        if column < 0 or column >= len(self._columns):
            return

        self.layoutAboutToBeChanged.emit()

        column_key = self._columns[column].key
        reverse = order == Qt.SortOrder.DescendingOrder

        def sort_key(entry: ROMEntry) -> Any:
            """Generate sort key for an entry."""
            return self._get_sort_data(entry, column_key)

        self._filtered_entries.sort(key=sort_key, reverse=reverse)
        self.layoutChanged.emit()

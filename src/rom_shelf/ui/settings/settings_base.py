"""Base classes and utilities for settings UI components."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from ...core.settings import Settings
from ..themes.themed_widget import ThemeHelper


def normalize_path_display(path_str: str) -> str:
    """Normalize path for consistent display on Windows."""
    try:
        # Convert to Path and back to string to ensure consistent separators
        return str(Path(path_str).resolve())
    except (OSError, ValueError):
        # Fallback to original string if path normalization fails
        return path_str


class SettingsPage(QWidget):
    """Base class for settings pages."""

    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the settings page."""
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.setProperty("formVariant", "compact")
        self._setup_ui()
        ThemeHelper.apply_compact_form_style(self)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        pass

    def load_settings(self, settings: Settings) -> None:
        """Load settings into the page."""
        pass

    def save_settings(self, settings: Settings) -> None:
        """Save settings from the page."""
        pass

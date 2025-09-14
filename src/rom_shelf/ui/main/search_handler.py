"""Search functionality for ROM filtering."""

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QToolBar, QWidget

from ...models.rom_table_model import ROMTableModel


class SearchHandler(QObject):
    """Handles ROM search and filtering functionality."""

    # Signal emitted when search filter changes
    filter_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the search handler."""
        super().__init__(parent)
        self._search_edit: QLineEdit | None = None
        self._rom_model: ROMTableModel | None = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_search_filter)

    def create_search_toolbar(self, parent: QWidget) -> QToolBar:
        """Create and return the search toolbar."""
        search_toolbar = QToolBar("Search", parent)
        search_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # Add search label and field
        search_label = QLabel("Search:")
        search_toolbar.addWidget(search_label)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(
            "Filter ROMs by name, platform, region, language, or version..."
        )
        self._search_edit.setMinimumWidth(300)
        self._search_edit.setMaximumWidth(500)
        self._search_edit.textChanged.connect(self._on_search_text_changed)
        search_toolbar.addWidget(self._search_edit)

        return search_toolbar

    def set_rom_model(self, model: ROMTableModel) -> None:
        """Set the ROM model to filter."""
        self._rom_model = model

    def get_search_text(self) -> str:
        """Get the current search text."""
        if self._search_edit:
            return self._search_edit.text().strip()
        return ""

    def clear_search(self) -> None:
        """Clear the search field."""
        if self._search_edit:
            self._search_edit.clear()

    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes with a delay."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms delay

    def _apply_search_filter(self) -> None:
        """Apply search filter to the ROM model."""
        if not self._rom_model or not self._search_edit:
            return

        search_text = self._search_edit.text().strip()
        self._rom_model.set_search_filter(search_text)
        self.filter_changed.emit()

    def apply_font_settings(self, font) -> None:
        """Apply font settings to search components."""
        if self._search_edit:
            self._search_edit.setFont(font)

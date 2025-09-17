"""Compact button widget for use in table cells and other space-constrained areas."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class CompactButton(QPushButton):
    """A compact button designed to fit nicely in table cells."""

    # Shared style for all compact buttons
    COMPACT_STYLE = """
        QPushButton {
            padding: 0px 6px;
            margin: 0px;
            min-height: 20px;
            max-height: 20px;
            font-size: 11px;
            border: 1px solid rgba(128, 128, 128, 0.5);
            border-radius: 2px;
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.08),
                stop: 1 rgba(255, 255, 255, 0.02)
            );
        }
        QPushButton:hover {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.12),
                stop: 1 rgba(255, 255, 255, 0.06)
            );
            border-color: rgba(255, 255, 255, 0.3);
        }
        QPushButton:pressed {
            background: rgba(0, 0, 0, 0.2);
            padding-top: 1px;
        }
        QPushButton:disabled {
            color: rgba(128, 128, 128, 0.5);
            border-color: rgba(128, 128, 128, 0.2);
            background: transparent;
        }
    """

    def __init__(self, text: str = "", parent=None):
        """Initialize the compact button.

        Args:
            text: Button text
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.setStyleSheet(self.COMPACT_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class TableCellButton(CompactButton):
    """Specialized compact button for table cells with even tighter constraints."""

    TABLE_CELL_STYLE = """
        QPushButton {
            padding: 1px 6px;
            margin: 0px;
            min-width: 50px;
            height: 20px;
            min-height: 20px;
            max-height: 20px;
            font-size: 11px;
            border: 1px solid rgba(128, 128, 128, 0.4);
            border-radius: 2px;
            background: rgba(255, 255, 255, 0.03);
        }
        QPushButton:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.4);
        }
        QPushButton:pressed {
            background: rgba(0, 0, 0, 0.15);
        }
    """

    def __init__(self, text: str = "", parent=None):
        """Initialize the table cell button."""
        super().__init__(text, parent)
        self.setStyleSheet(self.TABLE_CELL_STYLE)

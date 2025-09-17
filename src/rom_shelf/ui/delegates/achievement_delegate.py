"""Delegate for displaying RetroAchievements icon in ROM table."""

import webbrowser
from pathlib import Path
from typing import Any

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QIcon, QMouseEvent, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class AchievementDelegate(QStyledItemDelegate):
    """Delegate for rendering RetroAchievements icon."""

    def __init__(self, parent=None):
        """Initialize the achievement delegate."""
        super().__init__(parent)
        self._icon = None
        self._load_icon()

    def _load_icon(self) -> None:
        """Load the RetroAchievements icon."""
        # Try to load SVG icon
        svg_path = Path(__file__).parent.parent.parent / "images" / "retroachievements.svg"
        if svg_path.exists():
            self._icon = QIcon(str(svg_path))
        else:
            # Fallback to PNG if available
            png_path = (
                Path(__file__).parent.parent.parent / "images" / "retro-achievements-logo.png"
            )
            if png_path.exists():
                self._icon = QIcon(str(png_path))

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint the achievement icon if game has RA data."""
        # Get RA game ID from model
        ra_game_id = index.data(Qt.UserRole + 10)  # Custom role for RA game ID

        if ra_game_id:
            # Calculate icon rect centered in the cell
            icon_size = 16
            icon_rect = QRect(
                option.rect.center().x() - icon_size // 2,
                option.rect.center().y() - icon_size // 2,
                icon_size,
                icon_size,
            )

            # Draw icon if available
            if self._icon:
                self._icon.paint(painter, icon_rect)
            else:
                # Fallback: draw a simple "RA" text
                painter.save()
                painter.setPen(Qt.GlobalColor.darkYellow)
                painter.drawText(option.rect, Qt.AlignCenter, "RA")
                painter.restore()
        else:
            # No RA data, leave cell empty
            super().paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Return size hint for the cell."""
        return QSize(24, option.rect.height())

    def editorEvent(
        self, event: Any, model: Any, option: QStyleOptionViewItem, index: QModelIndex
    ) -> bool:
        """Handle mouse clicks on the achievement icon."""
        if event.type() == event.Type.MouseButtonRelease:
            if isinstance(event, QMouseEvent) and event.button() == Qt.LeftButton:
                # Get RA game ID
                ra_game_id = index.data(Qt.UserRole + 10)

                if ra_game_id:
                    # Open RA game page in browser
                    url = f"https://retroachievements.org/game/{ra_game_id}"
                    webbrowser.open(url)
                    return True

        return super().editorEvent(event, model, option, index)

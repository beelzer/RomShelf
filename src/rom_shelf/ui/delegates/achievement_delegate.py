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
        """Paint the achievement icon and progress if game has RA data."""
        # Get RA game ID from model
        ra_game_id = index.data(Qt.UserRole + 10)  # Custom role for RA game ID
        # Get user progress from model
        user_progress = index.data(Qt.UserRole + 11)  # Custom role for user progress

        if ra_game_id:
            painter.save()

            # Draw the icon on the left side if available
            icon_width = 0
            if self._icon:
                icon_size = 16
                icon_rect = QRect(
                    option.rect.left() + 2,
                    option.rect.center().y() - icon_size // 2,
                    icon_size,
                    icon_size,
                )
                self._icon.paint(painter, icon_rect)
                icon_width = icon_size + 4

            # Draw progress text to the right of icon
            if user_progress:
                earned = user_progress.get("achievements_earned", 0)
                total = user_progress.get("achievements_total", 0)

                # Format: (X/Y)
                text = f"({earned}/{total})"

                # Set color based on completion
                if total > 0 and earned == total:
                    painter.setPen(Qt.GlobalColor.darkGreen)
                elif earned > 0:
                    painter.setPen(Qt.GlobalColor.darkYellow)
                else:
                    painter.setPen(Qt.GlobalColor.gray)
            else:
                # No user progress but has RA data - show (0/?)
                text = "(0/?)"
                painter.setPen(Qt.GlobalColor.gray)

            # Draw progress text
            text_rect = QRect(
                option.rect.left() + icon_width,
                option.rect.top(),
                option.rect.width() - icon_width,
                option.rect.height(),
            )
            # Use the default option font to match other table cells
            painter.setFont(option.font)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)

            painter.restore()
        else:
            # No RA data, leave cell empty
            super().paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Return size hint for the cell."""
        return QSize(100, option.rect.height())

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

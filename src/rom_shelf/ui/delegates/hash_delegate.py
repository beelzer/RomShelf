"""Custom delegate for displaying hash information with icons and tooltips."""

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import QCursor, QFont, QGuiApplication, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
)

from ...core.rom_database import get_rom_database


class HashDelegate(QStyledItemDelegate):
    """Delegate for displaying hash information with visual indicators."""

    def __init__(self, parent=None):
        """Initialize the hash delegate."""
        super().__init__(parent)
        self._rom_database = get_rom_database()
        self._hash_rects = {}  # Store rectangles for each hash icon
        self._last_index = None  # Track last hovered index

        # Hash type indicators (using Unicode symbols)
        self.hash_symbols = {
            "md5": "M",  # MD5
            "crc32": "C",  # CRC32
            "header": "H",  # Header hash
        }

        # Colors for different hash types
        self.hash_colors = {
            "md5": "#4CAF50",  # Green
            "crc32": "#2196F3",  # Blue
            "header": "#FF9800",  # Orange
        }

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        """Paint the hash indicators.

        Args:
            painter: The painter to use
            option: Style options
            index: The model index
        """
        # Get the ROM entry (UserRole + 1)
        rom_entry = index.data(Qt.UserRole + 1)
        if not rom_entry:
            super().paint(painter, option, index)
            return

        # Get hash data from database
        fingerprint = self._rom_database.get_fingerprint(
            rom_entry.file_path, rom_entry.internal_path
        )

        if not fingerprint:
            super().paint(painter, option, index)
            return

        # Prepare painter
        painter.save()

        # Draw background if selected
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # Calculate positions
        rect = option.rect
        x = rect.x() + 5
        y = rect.y()
        height = rect.height()

        # Create a bold font for indicators
        font = QFont(option.font)
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        painter.setFont(font)

        # Draw hash indicators and store their positions
        indicator_width = 20
        indicators_drawn = []
        index_key = (index.row(), index.column())
        self._hash_rects[index_key] = {}

        # Check and draw MD5 indicator
        if fingerprint.md5_hash:
            rect = QRect(x, y, indicator_width, height)
            self._hash_rects[index_key]["md5"] = rect
            painter.setPen(self.hash_colors["md5"])
            painter.drawText(rect, Qt.AlignCenter, self.hash_symbols["md5"])
            indicators_drawn.append("md5")
            x += indicator_width

        # Check and draw CRC32 indicator
        if fingerprint.crc32:
            rect = QRect(x, y, indicator_width, height)
            self._hash_rects[index_key]["crc32"] = rect
            painter.setPen(self.hash_colors["crc32"])
            painter.drawText(rect, Qt.AlignCenter, self.hash_symbols["crc32"])
            indicators_drawn.append("crc32")
            x += indicator_width

        # Check and draw header hash indicator
        if fingerprint.header_hash:
            rect = QRect(x, y, indicator_width, height)
            self._hash_rects[index_key]["header"] = rect
            painter.setPen(self.hash_colors["header"])
            painter.drawText(rect, Qt.AlignCenter, self.hash_symbols["header"])
            indicators_drawn.append("header")
            x += indicator_width

        # If no hashes available, show a dash
        if not indicators_drawn:
            painter.setPen(option.palette.text().color())
            painter.setFont(option.font)
            painter.drawText(rect, Qt.AlignCenter, "—")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        """Handle mouse events to show tooltips for individual hash icons.

        Args:
            event: The event
            model: The model
            option: Style options
            index: The model index

        Returns:
            True if event was handled
        """
        # Handle mouse click events to copy hash to clipboard
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # Get the ROM entry
            rom_entry = index.data(Qt.UserRole + 1)
            if not rom_entry:
                return False

            # Get hash data from database
            fingerprint = self._rom_database.get_fingerprint(
                rom_entry.file_path, rom_entry.internal_path
            )

            if not fingerprint:
                return False

            # Check which hash icon was clicked
            index_key = (index.row(), index.column())
            if index_key in self._hash_rects:
                pos = event.pos()

                # Check each hash rectangle
                for hash_type, rect in self._hash_rects[index_key].items():
                    if rect.contains(pos):
                        # Copy the hash to clipboard
                        clipboard = QGuiApplication.clipboard()
                        copied_text = ""
                        tooltip_text = ""

                        if hash_type == "md5" and fingerprint.md5_hash:
                            copied_text = fingerprint.md5_hash
                            tooltip_text = "MD5 hash copied!"
                        elif hash_type == "crc32" and fingerprint.crc32:
                            copied_text = f"{fingerprint.crc32:08X}"
                            tooltip_text = "CRC32 hash copied!"
                        elif hash_type == "header" and fingerprint.header_hash:
                            copied_text = fingerprint.header_hash
                            tooltip_text = "Header hash copied!"

                        if copied_text:
                            clipboard.setText(copied_text)
                            return True  # Consume the event to prevent row selection

                return False

        # Handle mouse move events for tooltips
        elif event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            # Get the ROM entry
            rom_entry = index.data(Qt.UserRole + 1)
            if not rom_entry:
                QToolTip.hideText()
                QApplication.restoreOverrideCursor()
                return False

            # Get hash data from database
            fingerprint = self._rom_database.get_fingerprint(
                rom_entry.file_path, rom_entry.internal_path
            )

            if not fingerprint:
                QToolTip.hideText()
                QApplication.restoreOverrideCursor()
                return False

            # Check which hash icon the mouse is over
            index_key = (index.row(), index.column())
            if index_key in self._hash_rects:
                pos = event.pos()
                tooltip_shown = False
                cursor_set = False

                # Check each hash rectangle
                for hash_type, rect in self._hash_rects[index_key].items():
                    if rect.contains(pos):
                        # Show tooltip for this specific hash
                        tooltip = ""
                        if hash_type == "md5" and fingerprint.md5_hash:
                            tooltip = (
                                f"<b>MD5:</b><br>{fingerprint.md5_hash}<br><i>Click to copy</i>"
                            )
                            cursor_set = True
                        elif hash_type == "crc32" and fingerprint.crc32:
                            tooltip = (
                                f"<b>CRC32:</b><br>{fingerprint.crc32:08X}<br><i>Click to copy</i>"
                            )
                            cursor_set = True
                        elif hash_type == "header" and fingerprint.header_hash:
                            header_display = fingerprint.header_hash[:32]
                            if len(fingerprint.header_hash) > 32:
                                header_display += "..."
                            tooltip = (
                                f"<b>Header Hash:</b><br>{header_display}<br><i>Click to copy</i>"
                            )
                            cursor_set = True

                        if tooltip:
                            QToolTip.showText(event.globalPos(), tooltip)
                            tooltip_shown = True
                            # Change cursor to hand pointer
                            QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
                            break

                # Hide tooltip and restore cursor if not over any icon
                if not tooltip_shown:
                    QToolTip.hideText()
                    QApplication.restoreOverrideCursor()

                return False  # Don't consume the event

        # Handle tooltip event type as well for compatibility
        elif event.type() == QEvent.ToolTip:
            # Get the ROM entry
            rom_entry = index.data(Qt.UserRole + 1)
            if not rom_entry:
                return False

            # Get hash data from database
            fingerprint = self._rom_database.get_fingerprint(
                rom_entry.file_path, rom_entry.internal_path
            )

            if not fingerprint:
                return False

            # Check which hash icon the mouse is over
            index_key = (index.row(), index.column())
            if index_key in self._hash_rects:
                pos = event.pos()

                # Check each hash rectangle
                for hash_type, rect in self._hash_rects[index_key].items():
                    if rect.contains(pos):
                        # Show tooltip for this specific hash
                        tooltip = ""
                        if hash_type == "md5" and fingerprint.md5_hash:
                            tooltip = (
                                f"<b>MD5:</b><br>{fingerprint.md5_hash}<br><i>Click to copy</i>"
                            )
                        elif hash_type == "crc32" and fingerprint.crc32:
                            tooltip = (
                                f"<b>CRC32:</b><br>{fingerprint.crc32:08X}<br><i>Click to copy</i>"
                            )
                        elif hash_type == "header" and fingerprint.header_hash:
                            header_display = fingerprint.header_hash[:32]
                            if len(fingerprint.header_hash) > 32:
                                header_display += "..."
                            tooltip = (
                                f"<b>Header Hash:</b><br>{header_display}<br><i>Click to copy</i>"
                            )

                        if tooltip:
                            QToolTip.showText(event.globalPos(), tooltip)
                            return True

                # Hide tooltip if not over any icon
                QToolTip.hideText()

        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        """Return the size hint for the cell.

        Args:
            option: Style options
            index: The model index

        Returns:
            The size hint
        """
        # Make sure we have enough width for 3 indicators
        return option.rect.size()

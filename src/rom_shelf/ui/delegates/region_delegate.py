"""Custom delegate for displaying region information with flag icons and tooltips."""

from PySide6.QtCore import QEvent, QRect, QSize, Qt
from PySide6.QtGui import QCursor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
)

from ...utils.flag_icons import FlagIcons


class RegionDelegate(QStyledItemDelegate):
    """Delegate for displaying region information with flag icons."""

    def __init__(self, parent=None):
        """Initialize the region delegate."""
        super().__init__(parent)
        self._icon_rects = {}  # Store rectangles for each flag icon
        self._region_data = {}  # Store region data for each cell

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        """Paint the region flag icons.

        Args:
            painter: The painter to use
            option: Style options
            index: The model index
        """
        # Get the ROM entry
        rom_entry = index.data(Qt.UserRole + 1)
        if not rom_entry or "region" not in rom_entry.metadata:
            super().paint(painter, option, index)
            return

        region_str = str(rom_entry.metadata.get("region", ""))
        if not region_str:
            super().paint(painter, option, index)
            return

        # Prepare painter
        painter.save()

        # Draw background if selected
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Parse regions (handle multi-region strings)
        regions = []
        if "/" in region_str:
            # Multi-region game
            regions = [r.strip() for r in region_str.split("/")]
        elif "," in region_str:
            # Alternative separator
            regions = [r.strip() for r in region_str.split(",")]
        else:
            regions = [region_str.strip()]

        # Calculate positions with proper padding to match text cells
        rect = option.rect
        x = rect.x() + 8  # Match standard text padding
        y = rect.y() + (rect.height() - 14) // 2  # Center vertically

        # Draw flag icons and store their positions
        icon_width = 22  # 20px icon + 2px spacing
        icon_height = 14
        index_key = (index.row(), index.column())
        self._icon_rects[index_key] = {}
        self._region_data[index_key] = {}

        for i, region in enumerate(regions[:5]):  # Limit to 5 flags for space
            # Get flag icon
            flag_icon = FlagIcons.get_flag_icon(region, size=QSize(20, 14))

            if flag_icon:
                # Draw the flag icon
                icon_rect = QRect(x, y, 20, icon_height)
                flag_icon.paint(painter, icon_rect, Qt.AlignCenter)

                # Store the rect and region info for hover detection
                self._icon_rects[index_key][i] = icon_rect
                self._region_data[index_key][i] = region

                x += icon_width

        # If no flags were drawn, show text fallback
        if not self._icon_rects.get(index_key):
            painter.setPen(option.palette.text().color())
            painter.setFont(option.font)
            display_text = FlagIcons.get_display_text_for_region(region_str)
            painter.drawText(option.rect, Qt.AlignVCenter | Qt.AlignLeft, f"  {display_text}")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        """Handle mouse events to show tooltips for individual flag icons.

        Args:
            event: The event
            model: The model
            option: Style options
            index: The model index

        Returns:
            True if event was handled
        """
        # Handle mouse move events for tooltips
        if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            # Check which flag icon the mouse is over
            index_key = (index.row(), index.column())

            if index_key not in self._icon_rects:
                QToolTip.hideText()
                QApplication.restoreOverrideCursor()
                return False

            pos = event.pos()
            tooltip_shown = False

            # Check each flag rectangle
            for flag_idx, rect in self._icon_rects[index_key].items():
                if rect.contains(pos):
                    # Show tooltip for this specific region
                    if flag_idx in self._region_data.get(index_key, {}):
                        region = self._region_data[index_key][flag_idx]
                        region_text = FlagIcons.get_display_text_for_region(region)

                        # Build tooltip with region info
                        tooltip = f"<b>{region_text}</b>"

                        # Add additional info for special regions
                        if region.upper() in ["PAL", "NTSC"]:
                            if region.upper() == "PAL":
                                tooltip += (
                                    "<br><i>Phase Alternating Line</i><br>50Hz video standard"
                                )
                            else:
                                tooltip += "<br><i>National Television System Committee</i><br>60Hz video standard"
                        elif region.upper() in ["USA", "US", "U"]:
                            tooltip += "<br>United States of America"
                        elif region.upper() in ["EUR", "EUROPE", "E"]:
                            tooltip += "<br>European Region"
                        elif region.upper() in ["JPN", "JAPAN", "J"]:
                            tooltip += "<br>日本 (Japan)"

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
            # Check which flag icon the mouse is over
            index_key = (index.row(), index.column())

            if index_key not in self._icon_rects:
                return False

            pos = event.pos()

            # Check each flag rectangle
            for flag_idx, rect in self._icon_rects[index_key].items():
                if rect.contains(pos):
                    # Show tooltip for this specific region
                    if flag_idx in self._region_data.get(index_key, {}):
                        region = self._region_data[index_key][flag_idx]
                        region_text = FlagIcons.get_display_text_for_region(region)
                        tooltip = f"<b>{region_text}</b>"
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
        # Make sure we have enough width for multiple flags
        return option.rect.size()

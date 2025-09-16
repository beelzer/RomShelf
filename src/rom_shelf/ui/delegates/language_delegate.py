"""Custom delegate for displaying language information with flag icons and tooltips."""

import logging

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

logger = logging.getLogger(__name__)


class LanguageDelegate(QStyledItemDelegate):
    """Delegate for displaying language information with flag icons."""

    # Map language codes to their full names and associated country flags
    LANGUAGE_INFO = {
        "En": ("English", "gb"),  # Great Britain flag for English
        "Fr": ("Français", "fr"),
        "De": ("Deutsch", "de"),
        "Es": ("Español", "es"),
        "It": ("Italiano", "it"),
        "Pt": ("Português", "pt"),
        "Ja": ("日本語", "jp"),
        "Ko": ("한국어", "kr"),
        "Zh": ("中文", "cn"),
        "Ru": ("Русский", "ru"),
        "Nl": ("Nederlands", "nl"),
        "Sv": ("Svenska", "se"),
        "No": ("Norsk", "no"),
        "Da": ("Dansk", "dk"),
        "Fi": ("Suomi", "fi"),
        "Pl": ("Polski", "pl"),
        "Ar": ("العربية", "sa"),  # Saudi Arabia for Arabic
        "He": ("עברית", "il"),  # Israel for Hebrew
        "Tr": ("Türkçe", "tr"),
        "Gr": ("Ελληνικά", "gr"),
        "Hu": ("Magyar", "hu"),
        "Cs": ("Čeština", "cz"),
        "Ro": ("Română", "ro"),
    }

    def __init__(self, parent=None):
        """Initialize the language delegate."""
        super().__init__(parent)
        self._icon_rects = {}  # Store rectangles for each language icon
        self._language_data = {}  # Store language data for each cell

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        """Paint the language flag icons with text abbreviations.

        Args:
            painter: The painter to use
            option: Style options
            index: The model index
        """
        # Get the ROM entry
        rom_entry = index.data(Qt.UserRole + 1)
        if not rom_entry or "language" not in rom_entry.metadata:
            super().paint(painter, option, index)
            return

        language_str = str(rom_entry.metadata.get("language", ""))
        if not language_str:
            super().paint(painter, option, index)
            return

        # Prepare painter
        painter.save()

        # Draw background if selected
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Parse languages (handle multi-language strings)
        # First normalize the string by replacing common separators
        normalized = language_str.replace("+", ",").replace("/", ",")

        # Split by comma and clean up
        languages = [lang.strip() for lang in normalized.split(",") if lang.strip()]

        # If no languages found, use the original string
        if not languages:
            languages = [language_str.strip()]

        # Log the parsed languages for debugging
        if len(languages) > 1:
            logger.debug(f"Multi-language ROM: '{language_str}' parsed as {languages}")

        # Calculate positions
        rect = option.rect
        x = rect.x() + 4
        y = rect.y()
        height = rect.height()

        # Draw language indicators and store their positions
        index_key = (index.row(), index.column())
        self._icon_rects[index_key] = {}
        self._language_data[index_key] = {}

        for i, lang in enumerate(languages[:6]):  # Limit to 6 languages for space
            # Normalize language code (capitalize first letter)
            lang_code = lang[:2].capitalize() if len(lang) >= 2 else lang.capitalize()

            # Get language info
            if lang_code in self.LANGUAGE_INFO:
                full_name, country_code = self.LANGUAGE_INFO[lang_code]

                # Get flag icon for the language's associated country
                flag_icon = FlagIcons.get_flag_icon(country_code, size=QSize(16, 12))

                if flag_icon:
                    # Draw the flag icon
                    icon_y = y + (height - 12) // 2
                    icon_rect = QRect(x, icon_y, 16, 12)
                    flag_icon.paint(painter, icon_rect, Qt.AlignCenter)

                    # Store the clickable area for hover detection
                    self._icon_rects[index_key][i] = icon_rect
                    self._language_data[index_key][i] = (lang_code, full_name)

                    x += 18  # Move to next icon position
                else:
                    logger.debug(
                        f"No flag icon found for language {lang_code} (country: {country_code})"
                    )
            else:
                # Unknown language - skip showing it since we don't have a flag
                logger.debug(f"Unknown language code: {lang_code} from '{lang}'")
                pass

        # If no languages were drawn, show text fallback
        if not self._icon_rects.get(index_key):
            painter.setPen(option.palette.text().color())
            painter.setFont(option.font)
            painter.drawText(option.rect, Qt.AlignVCenter | Qt.AlignLeft, f"  {language_str}")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        """Handle mouse events to show tooltips for individual language icons.

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
            # Check which language icon the mouse is over
            index_key = (index.row(), index.column())

            if index_key not in self._icon_rects:
                QToolTip.hideText()
                QApplication.restoreOverrideCursor()
                return False

            pos = event.pos()
            tooltip_shown = False

            # Check each language rectangle
            for lang_idx, rect in self._icon_rects[index_key].items():
                if rect.contains(pos):
                    # Show tooltip for this specific language
                    if lang_idx in self._language_data.get(index_key, {}):
                        lang_code, full_name = self._language_data[index_key][lang_idx]

                        # Build tooltip with language info
                        tooltip = f"<b>{full_name}</b>"
                        if lang_code != full_name:
                            tooltip += f"<br>Language code: {lang_code}"

                        # Add additional info for some languages
                        extra_info = {
                            "En": "Primary language for UK, USA, Australia, Canada",
                            "Fr": "Primary language for France, Canada (Quebec), Belgium",
                            "De": "Primary language for Germany, Austria, Switzerland",
                            "Es": "Primary language for Spain, Latin America",
                            "It": "Primary language for Italy",
                            "Pt": "Primary language for Portugal, Brazil",
                            "Ja": "Primary language for Japan",
                            "Ko": "Primary language for South Korea",
                            "Zh": "Primary language for China, Taiwan, Hong Kong",
                        }

                        if lang_code in extra_info:
                            tooltip += f"<br><i>{extra_info[lang_code]}</i>"

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
            # Check which language icon the mouse is over
            index_key = (index.row(), index.column())

            if index_key not in self._icon_rects:
                return False

            pos = event.pos()

            # Check each language rectangle
            for lang_idx, rect in self._icon_rects[index_key].items():
                if rect.contains(pos):
                    # Show tooltip for this specific language
                    if lang_idx in self._language_data.get(index_key, {}):
                        lang_code, full_name = self._language_data[index_key][lang_idx]
                        tooltip = f"<b>{full_name}</b>"
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
        # Make sure we have enough width for multiple language indicators
        return option.rect.size()

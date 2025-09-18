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
    # Using lowercase keys for case-insensitive matching
    LANGUAGE_INFO = {
        "en": ("English", "gb"),  # Great Britain flag for English
        "fr": ("French", "fr"),
        "de": ("German", "de"),
        "es": ("Spanish", "es"),
        "it": ("Italian", "it"),
        "pt": ("Portuguese", "pt"),
        "ja": ("Japanese", "jp"),
        "ko": ("Korean", "kr"),
        "zh": ("Chinese", "cn"),
        "ru": ("Russian", "ru"),
        "nl": ("Dutch", "nl"),
        "sv": ("Swedish", "se"),
        "no": ("Norwegian", "no"),
        "da": ("Danish", "dk"),
        "fi": ("Finnish", "fi"),
        "pl": ("Polish", "pl"),
        "ar": ("Arabic", "sa"),  # Saudi Arabia for Arabic
        "he": ("Hebrew", "il"),  # Israel for Hebrew
        "tr": ("Turkish", "tr"),
        "gr": ("Greek", "gr"),
        "hu": ("Hungarian", "hu"),
        "cs": ("Czech", "cz"),
        "ro": ("Romanian", "ro"),
        "ca": ("Catalan", "es"),  # Catalan - use Spanish flag
        "eu": ("Basque", "es"),  # Basque - use Spanish flag
        "ga": ("Irish", "ie"),  # Irish
        "cy": ("Welsh", "gb"),  # Welsh - use GB flag
        "is": ("Icelandic", "is"),  # Icelandic
        "hr": ("Croatian", "hr"),  # Croatian
        "sr": ("Serbian", "rs"),  # Serbian
        "sk": ("Slovak", "sk"),  # Slovak
        "sl": ("Slovenian", "si"),  # Slovenian
        "lt": ("Lithuanian", "lt"),  # Lithuanian
        "lv": ("Latvian", "lv"),  # Latvian
        "et": ("Estonian", "ee"),  # Estonian
        "bg": ("Bulgarian", "bg"),  # Bulgarian
        "uk": ("Ukrainian", "ua"),  # Ukrainian
        "be": ("Belarusian", "by"),  # Belarusian
        "mk": ("Macedonian", "mk"),  # Macedonian
        "sq": ("Albanian", "al"),  # Albanian
        "vi": ("Vietnamese", "vn"),  # Vietnamese
        "th": ("Thai", "th"),  # Thai
        "id": ("Indonesian", "id"),  # Indonesian
        "ms": ("Malay", "my"),  # Malay
        "hi": ("Hindi", "in"),  # Hindi
        "ta": ("Tamil", "in"),  # Tamil
        "te": ("Telugu", "in"),  # Telugu
        "bn": ("Bengali", "bd"),  # Bengali
        "ur": ("Urdu", "pk"),  # Urdu
        "fa": ("Persian", "ir"),  # Persian/Farsi
        "multi": ("Multi-language", "world"),  # For multi-language ROMs
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
        if not rom_entry:
            logger.debug(f"No ROM entry for row {index.row()}")
            super().paint(painter, option, index)
            return

        if "language" not in rom_entry.metadata:
            # Log first few times to avoid spam
            if index.row() < 5:
                logger.debug(
                    f"No language in metadata for {rom_entry.display_name}. Metadata keys: {list(rom_entry.metadata.keys())}"
                )
            super().paint(painter, option, index)
            return

        language_str = str(rom_entry.metadata.get("language", ""))
        if not language_str:
            super().paint(painter, option, index)
            return

        # Debug log the language string (disabled for normal operation)
        # logger.info(
        #     f"[LANG] Row {index.row()}: Language string for {rom_entry.display_name}: '{language_str}'"
        # )

        # Prepare painter
        painter.save()

        # Draw background if selected
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Parse languages (handle multi-language strings)
        # Check for special "Multi" indicator
        if language_str.strip().lower() == "multi":
            # For generic multi-language ROMs, show a special indicator
            languages = ["Multi"]
        else:
            # First normalize the string by replacing common separators
            normalized = language_str.replace("+", ",").replace("/", ",")

            # Split by comma and clean up
            languages = [lang.strip() for lang in normalized.split(",") if lang.strip()]

            # If no languages found, use the original string
            if not languages:
                languages = [language_str.strip()]

        # Log the parsed languages for debugging (disabled for normal operation)
        # logger.info(f"[LANG] Parsed '{language_str}' into languages: {languages}")

        # Calculate positions with proper padding to match text cells
        rect = option.rect
        x = rect.x() + 8  # Match standard text padding
        y = rect.y()
        height = rect.height()

        # Draw language indicators and store their positions
        index_key = (index.row(), index.column())
        self._icon_rects[index_key] = {}
        self._language_data[index_key] = {}

        icons_drawn = 0
        # Calculate how many flags we can fit based on available width
        available_width = option.rect.width() - 16  # Account for padding
        flag_width = 22  # Each flag takes 22px (20px + 2px spacing)
        plus_indicator_width = 30  # Space needed for "+X" text

        # Calculate max flags that can fit
        max_flags_possible = available_width // flag_width
        # If we have more languages than can fit, reserve space for "+X"
        if len(languages) > max_flags_possible:
            max_flags = (available_width - plus_indicator_width) // flag_width
        else:
            max_flags = max_flags_possible

        # Ensure at least 1 flag is shown if there are languages
        max_flags = max(1, min(max_flags, len(languages)))

        for i, lang in enumerate(languages[:max_flags]):  # Show as many as fit
            # Normalize language code to lowercase for matching
            lang_code = lang[:2].lower() if len(lang) >= 2 else lang.lower()
            # logger.info(f"[LANG] Processing language '{lang}' -> normalized to '{lang_code}'")

            # Get language info
            if lang_code in self.LANGUAGE_INFO:
                full_name, country_code = self.LANGUAGE_INFO[lang_code]

                # Get flag icon for the language's associated country
                flag_icon = FlagIcons.get_flag_icon(country_code, size=QSize(20, 14))

                if flag_icon:
                    # Draw the flag icon
                    icon_y = y + (height - 14) // 2  # Center vertically
                    icon_rect = QRect(x, icon_y, 20, 14)
                    flag_icon.paint(painter, icon_rect, Qt.AlignCenter)

                    # Store the clickable area for hover detection
                    self._icon_rects[index_key][i] = icon_rect
                    self._language_data[index_key][i] = (lang_code, full_name)

                    x += 22  # Move to next icon position (20px icon + 2px spacing)
                    icons_drawn += 1
                else:
                    # No flag icon found for this language
                    pass
            else:
                # Unknown language - skip showing it since we don't have a flag
                pass

        # Show "+X" indicator if there are more languages
        if len(languages) > max_flags:
            additional_count = len(languages) - max_flags
            painter.setPen(option.palette.text().color())
            painter.setFont(option.font)
            # Draw the "+X" text
            plus_text = f"+{additional_count}"
            text_rect = QRect(x, y, 30, height)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, plus_text)

            # Store the "+X" area for hover detection
            self._icon_rects[index_key]["plus_indicator"] = text_rect
            # Store the remaining languages for tooltip
            remaining_languages = languages[max_flags:]
            self._language_data[index_key]["plus_indicator"] = remaining_languages

        # If no languages were drawn, show text fallback
        if icons_drawn == 0:
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

            # Check each language rectangle and plus indicator
            for lang_idx, rect in self._icon_rects[index_key].items():
                if rect.contains(pos):
                    # Check if this is the plus indicator
                    if lang_idx == "plus_indicator":
                        # Show tooltip for remaining languages
                        if "plus_indicator" in self._language_data.get(index_key, {}):
                            remaining_languages = self._language_data[index_key]["plus_indicator"]

                            # Build tooltip showing the remaining languages
                            tooltip_parts = ["<b>Additional Languages:</b>"]
                            for lang in remaining_languages:
                                lang_code = lang[:2].lower() if len(lang) >= 2 else lang.lower()
                                if lang_code in self.LANGUAGE_INFO:
                                    full_name, _ = self.LANGUAGE_INFO[lang_code]
                                    tooltip_parts.append(f"• {full_name}")
                                else:
                                    tooltip_parts.append(f"• {lang}")

                            tooltip = "<br>".join(tooltip_parts)
                            QToolTip.showText(event.globalPos(), tooltip)
                            tooltip_shown = True
                            QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
                            break
                    else:
                        # Show tooltip for individual language flag
                        if lang_idx in self._language_data.get(index_key, {}):
                            lang_code, full_name = self._language_data[index_key][lang_idx]

                            # Build tooltip with language info
                            tooltip = f"<b>{full_name}</b>"
                            if lang_code != full_name:
                                tooltip += f"<br>Language code: {lang_code}"

                            # Add additional info for some languages
                            extra_info = {
                                "en": "Primary language for UK, USA, Australia, Canada",
                                "fr": "Primary language for France, Canada (Quebec), Belgium",
                                "de": "Primary language for Germany, Austria, Switzerland",
                                "es": "Primary language for Spain, Latin America",
                                "it": "Primary language for Italy",
                                "pt": "Primary language for Portugal, Brazil",
                                "ja": "Primary language for Japan",
                                "ko": "Primary language for South Korea",
                                "zh": "Primary language for China, Taiwan, Hong Kong",
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
        # Get the ROM entry to calculate actual width needed
        rom_entry = index.data(Qt.UserRole + 1)
        if not rom_entry or "language" not in rom_entry.metadata:
            return QSize(60, option.rect.height())  # Minimum width

        language_str = str(rom_entry.metadata.get("language", ""))
        if not language_str:
            return QSize(60, option.rect.height())

        # Parse languages to count how many flag icons we'll show
        if language_str.strip().lower() == "multi":
            languages = ["Multi"]
        else:
            normalized = language_str.replace("+", ",").replace("/", ",")
            languages = [lang.strip() for lang in normalized.split(",") if lang.strip()]
            if not languages:
                languages = [language_str.strip()]

        # Count valid languages that will have flag icons
        valid_languages = 0
        for lang in languages:
            lang_code = lang[:2].lower() if len(lang) >= 2 else lang.lower()
            if lang_code in self.LANGUAGE_INFO:
                valid_languages += 1

        # Calculate optimal width for all languages with flexibility
        # Each icon is 20px wide + 2px spacing = 22px per icon
        # Plus 16px total padding (8px on each side)
        if valid_languages > 0:
            # Calculate width needed for all valid flags
            all_flags_width = 16 + (valid_languages * 22)
            # But also calculate a reasonable minimum/maximum
            min_width = 16 + 22  # At least 1 flag
            reasonable_max = 16 + (6 * 22)  # Up to 6 flags

            # If we have many languages, include space for "+X"
            if valid_languages > 6:
                calculated_width = reasonable_max + 30  # 6 flags + "+X"
            else:
                calculated_width = min(all_flags_width, reasonable_max)
        else:
            # Fallback for text display
            calculated_width = max(80, len(language_str) * 8)

        return QSize(calculated_width, option.rect.height())

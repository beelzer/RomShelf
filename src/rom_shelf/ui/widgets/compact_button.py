"""Compact button widgets styled using theme tokens."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from ..themes import get_theme_manager


class CompactButton(QPushButton):
    """A compact button designed to fit nicely in dense layouts."""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_theme()

    def apply_theme(self) -> None:
        """Public hook so callers can reapply theme overrides."""
        self._apply_theme()

    def _apply_theme(self) -> None:
        theme_manager = get_theme_manager()
        palette = theme_manager.get_palette()

        base_bg = theme_manager.color_with_alpha("overlay", 0.12)
        hover_bg = theme_manager.color_with_alpha("overlay", 0.2)
        pressed_bg = theme_manager.color_with_alpha("primary", 0.35)
        border_color = palette.border_light
        text_color = palette.text
        disabled_color = palette.text_disabled

        style = f"""
            QPushButton {{
                padding: 0px 6px;
                margin: 0px;
                min-height: 20px;
                max-height: 20px;
                font-size: 11px;
                border: 1px solid {border_color};
                border-radius: 2px;
                background: {base_bg};
                color: {text_color};
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border-color: {palette.primary};
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
                color: {palette.text_on_primary};
            }}
            QPushButton:disabled {{
                background: transparent;
                color: {disabled_color};
                border-color: {border_color};
            }}
        """
        self.setStyleSheet(style)


class TableCellButton(CompactButton):
    """Specialised compact button for table cells with tighter constraints."""

    def _apply_theme(self) -> None:
        theme_manager = get_theme_manager()
        palette = theme_manager.get_palette()

        base_bg = theme_manager.color_with_alpha("overlay", 0.08)
        hover_bg = theme_manager.color_with_alpha("overlay", 0.18)
        pressed_bg = theme_manager.color_with_alpha("primary", 0.3)
        border_color = palette.border_light
        text_color = palette.text
        disabled_color = palette.text_disabled

        style = f"""
            QPushButton {{
                padding: 1px 6px;
                margin: 0px;
                min-width: 50px;
                height: 20px;
                min-height: 20px;
                max-height: 20px;
                font-size: 11px;
                border: 1px solid {border_color};
                border-radius: 2px;
                background: {base_bg};
                color: {text_color};
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border-color: {palette.primary};
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
                color: {palette.text_on_primary};
            }}
            QPushButton:disabled {{
                background: transparent;
                color: {disabled_color};
                border-color: {border_color};
            }}
        """
        self.setStyleSheet(style)

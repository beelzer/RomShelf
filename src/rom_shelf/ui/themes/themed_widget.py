"""Utility class for widgets that need themed styling."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtWidgets import QWidget

from ..themes import get_theme_manager


class ThemedWidget(Protocol):
    """Protocol for widgets that can be themed."""

    def setStyleSheet(self, styleSheet: str) -> None:
        """Set the widget's stylesheet."""
        ...


class ThemeHelper:
    """Helper class for applying themed styles to widgets."""

    @staticmethod
    def apply_status_style(widget: ThemedWidget, status: str, text_prefix: str = "color: ") -> None:
        """Apply status-based styling to a widget."""
        theme_manager = get_theme_manager()
        color = theme_manager.get_status_color(status)
        widget.setStyleSheet(f"{text_prefix}{color};")

    @staticmethod
    def apply_header_style(widget: ThemedWidget, size: int = 14) -> None:
        """Apply header styling to a widget."""
        widget.setStyleSheet(f"font-weight: bold; font-size: {size}px; margin-bottom: 10px;")

    @staticmethod
    def apply_description_style(widget: ThemedWidget) -> None:
        """Apply description text styling to a widget."""
        theme_manager = get_theme_manager()
        palette = theme_manager.get_palette()
        widget.setStyleSheet(f"color: {palette.text_secondary}; margin-bottom: 15px;")

    @staticmethod
    def get_status_colors() -> dict[str, str]:
        """Get all status colors from the current theme."""
        theme_manager = get_theme_manager()
        return theme_manager.get_status_colors()

    @staticmethod
    def configure_button_sizing(button, min_width: int = None, min_height: int = None) -> None:
        """Configure button sizing with proper auto-sizing behavior."""
        from PySide6.QtWidgets import QPushButton, QSizePolicy

        if isinstance(button, QPushButton):
            # Set size policy to allow expansion but maintain minimum size
            button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

            # Set minimum sizes based on button type and text length
            text_length = len(button.text()) if button.text() else 0

            if min_width is None:
                # Auto-calculate minimum width based on text length (more compact)
                min_width = max(60, text_length * 6 + 24)  # 6px per char + 24px padding

            if min_height is None:
                # Compact button height
                min_height = 24

            button.setMinimumSize(min_width, min_height)

            # Remove any maximum size constraints that might cut off text
            button.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX

    @staticmethod
    def auto_size_button(button) -> None:
        """Automatically size a button based on its text content."""
        ThemeHelper.configure_button_sizing(button)

    @staticmethod
    def apply_compact_form_style(widget: QWidget) -> None:
        """Mark a widget tree to use the compact form variant and refresh styles."""
        if widget is None:
            return
        widget.setProperty("formVariant", "compact")
        if not widget.objectName():
            widget.setObjectName("settingsPage")
        ThemeHelper._repolish_widget_tree(widget)

    @staticmethod
    def _repolish_widget_tree(widget: QWidget) -> None:
        """Force Qt to re-evaluate styles for a widget subtree."""
        if widget is None:
            return
        style = widget.style()
        if style is None:
            return
        style.unpolish(widget)
        style.polish(widget)
        ThemeHelper._safe_update(widget)
        for child in widget.findChildren(QWidget):
            style.unpolish(child)
            style.polish(child)
            ThemeHelper._safe_update(child)

    @staticmethod
    def _safe_update(widget: QWidget) -> None:
        """Update a widget defensively to support views with special signatures."""
        if widget is None:
            return
        try:
            widget.update()
        except TypeError:
            widget.repaint()

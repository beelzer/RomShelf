"""Utility class for widgets that need themed styling."""

from typing import Protocol

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
        color = theme_manager.get_current_theme()
        if color:
            text_color = color.colors.text_secondary
            widget.setStyleSheet(f"color: {text_color}; margin-bottom: 15px;")

    @staticmethod
    def get_status_colors():
        """Get all status colors from the current theme."""
        theme_manager = get_theme_manager()
        if theme_manager.get_current_theme():
            return theme_manager.get_current_theme().get_status_colors()
        return {"success": "#4caf50", "warning": "#ff9800", "error": "#f44336", "info": "#2196f3"}

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

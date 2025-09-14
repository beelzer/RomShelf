"""Theme manager for handling theme switching and application."""

from PySide6.QtWidgets import QApplication

from .base_theme import BaseTheme
from .modern_dark_theme import ModernDarkTheme
from .modern_light_theme import ModernLightTheme


class ThemeManager:
    """Manages application themes and provides styling services."""

    def __init__(self):
        self._themes: dict[str, BaseTheme] = {}
        self._current_theme: BaseTheme | None = None
        self._register_default_themes()

    def _register_default_themes(self) -> None:
        """Register the modern themes."""
        self.register_theme(ModernDarkTheme())
        self.register_theme(ModernLightTheme())

    def register_theme(self, theme: BaseTheme) -> None:
        """Register a new theme."""
        self._themes[theme.name.lower()] = theme

    def get_available_themes(self) -> dict[str, str]:
        """Get available theme names mapped to display names."""
        return {key: theme.name for key, theme in self._themes.items()}

    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme by name."""
        theme_key = theme_name.lower()
        if theme_key in self._themes:
            self._current_theme = self._themes[theme_key]
            return True
        return False

    def get_current_theme(self) -> BaseTheme | None:
        """Get the currently active theme."""
        return self._current_theme

    def apply_theme_to_application(self, app: QApplication) -> None:
        """Apply the current theme to the entire application."""
        if self._current_theme:
            stylesheet = self._current_theme.get_complete_stylesheet()
            app.setStyleSheet(stylesheet)

    def apply_theme_to_widget(self, widget, theme_name: str | None = None) -> None:
        """Apply theme to a specific widget."""
        theme = self._current_theme
        if theme_name:
            theme_key = theme_name.lower()
            if theme_key in self._themes:
                theme = self._themes[theme_key]

        if theme:
            stylesheet = theme.get_complete_stylesheet()
            widget.setStyleSheet(stylesheet)

    def get_status_color(self, status: str) -> str:
        """Get color for a status (success, warning, error, info)."""
        if self._current_theme:
            colors = self._current_theme.get_status_colors()
            return colors.get(status.lower(), colors.get("info", "#000000"))
        return "#000000"

    def get_themed_style(self, component: str) -> str:
        """Get stylesheet for a specific component."""
        if not self._current_theme:
            return ""

        if component == "window":
            return self._current_theme.get_window_stylesheet()
        elif component == "navigation":
            return self._current_theme.get_navigation_stylesheet()
        elif component == "table":
            return self._current_theme.get_table_stylesheet()
        elif component == "form":
            return self._current_theme.get_form_stylesheet()
        elif component == "scrollbar":
            return self._current_theme.get_scrollbar_stylesheet()
        else:
            return ""


# Global theme manager instance
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager

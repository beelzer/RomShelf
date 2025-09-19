"""Theme manager for handling theme switching and application."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from .base_theme import BaseTheme, ColorPalette
from .modern_dark_theme import ModernDarkTheme
from .modern_light_theme import ModernLightTheme
from .twilight_theme import TwilightTheme


class ThemeManager:
    """Manages application themes and provides styling services."""

    def __init__(self) -> None:
        self._themes: dict[str, BaseTheme] = {}
        self._current_theme: BaseTheme | None = None
        self._register_default_themes()

    # ---------------------------------------------------------------------
    # Theme registration and access

    def _register_default_themes(self) -> None:
        """Register bundled themes and default to the dark palette."""
        dark_theme = ModernDarkTheme()
        light_theme = ModernLightTheme()
        twilight_theme = TwilightTheme()

        self.register_theme(dark_theme)
        self.register_theme(light_theme)
        self.register_theme(twilight_theme)
        self._current_theme = dark_theme

    def register_theme(self, theme: BaseTheme) -> None:
        """Register a new theme so it can be selected by name."""
        self._themes[theme.name.lower()] = theme

    def get_available_themes(self) -> dict[str, str]:
        """Return available theme keys mapped to their display names."""
        return {key: theme.name for key, theme in self._themes.items()}

    def ensure_theme(self) -> BaseTheme:
        """Return the active theme, falling back to the first registered theme."""
        if self._current_theme:
            return self._current_theme

        if self._themes:
            first_key = next(iter(self._themes))
            self._current_theme = self._themes[first_key]
            return self._current_theme

        default_theme = ModernDarkTheme()
        self.register_theme(default_theme)
        self._current_theme = default_theme
        return default_theme

    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme by name."""
        theme_key = theme_name.lower()
        if theme_key in self._themes:
            self._current_theme = self._themes[theme_key]
            return True
        return False

    def get_current_theme(self) -> BaseTheme:
        """Expose the active theme (guaranteed to be available)."""
        return self.ensure_theme()

    def get_palette(self) -> ColorPalette:
        """Return the current theme's color palette."""
        return self.get_current_theme().colors

    # ---------------------------------------------------------------------
    # Palette helpers

    def get_color(self, token: str, fallback: str | None = None) -> str:
        """Return a named color from the palette or a fallback value."""
        palette = self.get_palette()
        value = getattr(palette, token, None)
        if value is None:
            return fallback if fallback is not None else token
        return value

    def resolve_color(self, value: str) -> str:
        """Resolve either a palette token or raw color literal."""
        if value.startswith("#") or value.startswith("rgb"):
            return value
        return self.get_color(value, value)

    def to_rgba(self, color: str, alpha_override: float | None = None) -> str:
        """Convert a color into an rgba() string, applying an alpha override if given."""
        color = color.strip()
        if not color.startswith("#"):
            return color

        hex_value = color[1:]
        if len(hex_value) == 6:
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            alpha = 1.0 if alpha_override is None else float(alpha_override)
        elif len(hex_value) == 8:
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            base_alpha = int(hex_value[6:8], 16) / 255
            alpha = base_alpha if alpha_override is None else float(alpha_override)
        else:
            return color

        alpha = max(0.0, min(1.0, alpha))
        return f"rgba({r}, {g}, {b}, {alpha:.3f})"

    def color_with_alpha(self, token_or_color: str, alpha: float) -> str:
        """Resolve a palette token/raw color and apply the requested opacity."""
        color = self.resolve_color(token_or_color)
        return self.to_rgba(color, alpha)

    def get_status_colors(self) -> dict[str, str]:
        """Return the themed status colors (success, warning, error, info)."""
        return self.get_current_theme().get_status_colors()

    def get_status_color(self, status: str) -> str:
        """Look up a themed color for a status keyword."""
        colors = self.get_status_colors()
        return colors.get(status.lower(), colors.get("info", self.get_color("text")))

    # ---------------------------------------------------------------------
    # Stylesheet helpers

    def apply_theme_to_application(self, app: QApplication) -> None:
        """Apply the current theme to the entire application."""
        stylesheet = self.get_current_theme().get_complete_stylesheet()
        app.setStyleSheet(stylesheet)

    def apply_theme_to_widget(self, widget, theme_name: str | None = None) -> None:
        """Apply a theme to a specific widget, optionally overriding the active theme."""
        theme = self.get_current_theme()
        if theme_name:
            theme_key = theme_name.lower()
            if theme_key in self._themes:
                theme = self._themes[theme_key]

        widget.setStyleSheet(theme.get_complete_stylesheet())

    def get_themed_style(self, component: str) -> str:
        """Get a component-specific stylesheet fragment from the active theme."""
        theme = self.get_current_theme()

        if component == "window":
            return theme.get_window_stylesheet()
        if component == "navigation":
            return theme.get_navigation_stylesheet()
        if component == "table":
            return theme.get_table_stylesheet()
        if component == "form":
            return theme.get_form_stylesheet()
        if component == "scrollbar":
            return theme.get_scrollbar_stylesheet()
        return ""


# Global theme manager instance
_theme_manager: ThemeManager | None = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager

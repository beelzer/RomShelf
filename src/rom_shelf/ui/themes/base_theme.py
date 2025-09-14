"""Base theme class defining the theming interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorPalette:
    """Color palette for a theme with WCAG AA compliance."""
    # Core colors
    primary: str
    primary_hover: str
    primary_pressed: str
    secondary: str
    accent: str

    # Background colors
    background: str
    surface: str
    surface_variant: str
    card: str
    overlay: str

    # Text colors (WCAG AA compliant)
    text: str
    text_secondary: str
    text_disabled: str
    text_on_primary: str

    # State colors
    success: str
    warning: str
    error: str
    info: str

    # Interactive colors
    hover: str
    pressed: str
    selected: str
    selected_hover: str
    focus: str
    focus_ring: str

    # Border colors
    border: str
    border_light: str
    border_strong: str
    border_focus: str

    # Input colors
    input_bg: str
    input_bg_hover: str
    input_bg_focus: str
    input_border: str
    input_border_focus: str

    # Scrollbar colors
    scrollbar_bg: str
    scrollbar_handle: str
    scrollbar_handle_hover: str


class BaseTheme(ABC):
    """Abstract base class for themes."""

    def __init__(self, name: str):
        self.name = name
        self.colors = self._create_color_palette()

    @abstractmethod
    def _create_color_palette(self) -> ColorPalette:
        """Create the color palette for this theme."""
        pass

    @abstractmethod
    def get_window_stylesheet(self) -> str:
        """Get stylesheet for main windows and dialogs."""
        pass

    @abstractmethod
    def get_navigation_stylesheet(self) -> str:
        """Get stylesheet for navigation elements (menus, toolbars, trees)."""
        pass

    @abstractmethod
    def get_table_stylesheet(self) -> str:
        """Get stylesheet for table views and headers."""
        pass

    @abstractmethod
    def get_form_stylesheet(self) -> str:
        """Get stylesheet for form elements (inputs, buttons)."""
        pass

    @abstractmethod
    def get_scrollbar_stylesheet(self) -> str:
        """Get stylesheet for scrollbars and splitters."""
        pass

    def get_complete_stylesheet(self) -> str:
        """Get the complete stylesheet for the theme."""
        return "\n\n".join([
            self.get_window_stylesheet(),
            self.get_navigation_stylesheet(),
            self.get_table_stylesheet(),
            self.get_form_stylesheet(),
            self.get_scrollbar_stylesheet()
        ])

    def get_status_colors(self) -> Dict[str, str]:
        """Get colors for different status states."""
        return {
            "success": self.colors.success,
            "warning": self.colors.warning,
            "error": self.colors.error,
            "info": self.colors.info
        }
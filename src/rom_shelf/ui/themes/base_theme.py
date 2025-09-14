"""Base theme class defining the theming interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


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

    def get_window_stylesheet(self) -> str:
        """Get stylesheet for main windows and dialogs."""
        return f"""
QMainWindow {{
    background-color: {self.colors.background};
    color: {self.colors.text};
}}

QWidget {{
    background-color: {self.colors.background};
    color: {self.colors.text};
}}

QDialog {{
    background-color: {self.colors.surface};
    color: {self.colors.text};
    border: 1px solid {self.colors.border};
}}

QLabel {{
    color: {self.colors.text};
}}

QGroupBox {{
    color: {self.colors.text};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 500;
}}

QGroupBox::title {{
    color: {self.colors.text};
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px 0 8px;
}}"""

    def get_navigation_stylesheet(self) -> str:
        """Get stylesheet for navigation elements (menus, toolbars, trees)."""
        return f"""
QMenuBar {{
    background-color: {self.colors.card};
    color: {self.colors.text};
    border-bottom: 1px solid {self.colors.border};
    padding: 2px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 2px;
}}

QMenuBar::item:selected {{
    background-color: {self.colors.hover};
}}

QMenuBar::item:pressed {{
    background-color: {self.colors.pressed};
}}

QMenu {{
    background-color: {self.colors.surface};
    color: {self.colors.text};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 16px;
    border-radius: 4px;
    margin: 1px;
}}

QMenu::item:selected {{
    background-color: {self.colors.hover};
}}

QTreeWidget {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    outline: none;
    selection-background-color: {self.colors.selected};
}}

QTreeWidget::item {{
    padding: 8px 6px;
    border: none;
    min-height: 28px;
    border-radius: 4px;
    margin: 1px;
}}

QTreeWidget::item:selected {{
    background-color: {self.colors.selected};
    color: {self.colors.text_on_primary};
}}

QTreeWidget::item:hover:!selected {{
    background-color: {self.colors.hover};
}}

QTreeWidget::item:focus {{
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -2px;
}}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTYgNEwxMCA4TDYgMTJWNFoiIGZpbGw9IntzdHIoe3NlbGYuY29sb3JzLnRleHRfc2Vjb25kYXJ5fSkucmVwbGFjZSgnIycsICclMjMnKX0iLz4KPHN2Zz4K);
}}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkwxMiA2TDggMTBMNCA2WiIgZmlsbD0ie3N0cih7c2VsZi5jb2xvcnMudGV4dF9zZWNvbmRhcnl9KS5yZXBsYWNlKCcjJywgJyUyMycpfSIvPgo8L3N2Zz4K);
}}

QTreeWidget QCheckBox {{
    spacing: 8px;
}}

QTreeWidget QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 3px;
}}

QTreeWidget QCheckBox::indicator:unchecked {{
    background-color: {self.colors.input_bg};
    border: 2px solid {self.colors.input_border};
}}

QTreeWidget QCheckBox::indicator:unchecked:hover {{
    background-color: {self.colors.input_bg_hover};
    border-color: {self.colors.border_strong};
}}

QTreeWidget QCheckBox::indicator:checked {{
    background-color: {self.colors.primary};
    border: 2px solid {self.colors.primary};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDZMMyA1TDQuNSA2LjVMOSAyTDEwIDNaIiBmaWxsPSJ3aGl0ZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIwLjUiLz4KPHN2Zz4K);
}}

QTreeWidget QCheckBox::indicator:checked:hover {{
    background-color: {self.colors.primary_hover};
    border-color: {self.colors.primary_hover};
}}

QTreeWidget QCheckBox::indicator:focus {{
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: 2px;
}}

QToolBar {{
    background-color: {self.colors.surface};
    border: none;
    padding: 8px 12px;
    spacing: 8px;
}}

QToolBar QToolButton {{
    background-color: {self.colors.input_bg};
    border: 1px solid {self.colors.input_border};
    border-radius: 4px;
    padding: 4px 8px;
    color: {self.colors.text};
    font-weight: 500;
    min-width: 50px;
    min-height: 22px;
    text-align: center;
}}

QToolBar QToolButton:hover {{
    background-color: {self.colors.hover};
    border-color: {self.colors.border_strong};
}}

QToolBar QToolButton:pressed {{
    background-color: {self.colors.pressed};
}}

QToolBar QToolButton:focus {{
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -2px;
}}

QToolBar QLabel {{
    color: {self.colors.text};
    background: transparent;
    border: none;
    padding: 0px 6px;
}}

QStatusBar {{
    background-color: {self.colors.background};
    border-top: 1px solid {self.colors.border};
    color: {self.colors.text_secondary};
    padding: 4px 12px;
}}"""

    def get_table_stylesheet(self) -> str:
        """Get stylesheet for table views and headers."""
        return f"""
QTableView {{
    background-color: {self.colors.surface};
    alternate-background-color: {self.colors.surface_variant};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    gridline-color: {self.colors.border_light};
    outline: none;
    selection-background-color: {self.colors.selected};
}}

QTableView::item {{
    padding: 12px 16px;
    border: none;
}}

QTableView::item:selected {{
    background-color: {self.colors.selected};
    color: {self.colors.text_on_primary};
}}

QTableView::item:hover:!selected {{
    background-color: {self.colors.hover};
}}

QTableView::item:focus {{
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -2px;
}}

QHeaderView::section {{
    background-color: {self.colors.card};
    color: {self.colors.text};
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid {self.colors.border};
    border-right: 1px solid {self.colors.border_light};
    font-weight: 600;
}}

QHeaderView::section:first {{
    border-left: none;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {self.colors.hover};
}}"""

    def get_form_stylesheet(self) -> str:
        """Get stylesheet for form elements (inputs, buttons)."""
        return f"""
QLineEdit {{
    background-color: {self.colors.input_bg};
    border: 2px solid {self.colors.input_border};
    padding: 10px 12px;
    border-radius: 6px;
    color: {self.colors.text};
}}

QLineEdit:hover {{
    background-color: {self.colors.input_bg_hover};
    border-color: {self.colors.border_strong};
}}

QLineEdit:focus {{
    border-color: {self.colors.input_border_focus};
    background-color: {self.colors.input_bg_focus};
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -4px;
}}

QToolBar QLineEdit {{
    background-color: {self.colors.input_bg};
    border: 1px solid {self.colors.input_border};
    padding: 6px 10px;
    border-radius: 4px;
    color: {self.colors.text};
    margin: 2px;
}}

QToolBar QLineEdit:focus {{
    border-color: {self.colors.input_border_focus};
    background-color: {self.colors.input_bg_focus};
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -3px;
}}

QPushButton {{
    background-color: {self.colors.input_bg};
    border: 1px solid {self.colors.input_border};
    border-radius: 4px;
    padding: 6px 12px;
    color: {self.colors.text};
    font-weight: 500;
    min-width: 60px;
    min-height: 24px;
    text-align: center;
}}

QPushButton:hover {{
    background-color: {self.colors.hover};
    border-color: {self.colors.border_strong};
}}

QPushButton:pressed {{
    background-color: {self.colors.pressed};
}}

QPushButton:focus {{
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -2px;
}}

QPushButton:default {{
    background-color: {self.colors.primary};
    color: {self.colors.text_on_primary};
    border-color: {self.colors.primary};
}}

QPushButton:default:hover {{
    background-color: {self.colors.primary_hover};
    border-color: {self.colors.primary_hover};
}}

QPushButton:default:pressed {{
    background-color: {self.colors.primary_pressed};
}}

QComboBox {{
    background-color: {self.colors.input_bg};
    border: 1px solid {self.colors.input_border};
    border-radius: 6px;
    padding: 8px 12px;
    color: {self.colors.text};
}}

QComboBox:hover {{
    background-color: {self.colors.input_bg_hover};
    border-color: {self.colors.border_strong};
}}

QComboBox:focus {{
    border-color: {self.colors.input_border_focus};
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -2px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {self.colors.border};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QComboBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNUw2IDhMOSA1SDNaIiBmaWxsPSJ7c3RyKHtzZWxmLmNvbG9ycy50ZXh0X3NlY29uZGFyeX0pLnJlcGxhY2UoJyMnLCAnJTIzJyl9Ii8+Cjwvc3ZnPgo=);
}}

QComboBox QAbstractItemView {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    selection-background-color: {self.colors.selected};
    selection-color: {self.colors.text_on_primary};
    outline: none;
}}

QCheckBox {{
    color: {self.colors.text};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 3px;
}}

QCheckBox::indicator:unchecked {{
    background-color: {self.colors.input_bg};
    border: 2px solid {self.colors.input_border};
}}

QCheckBox::indicator:unchecked:hover {{
    background-color: {self.colors.input_bg_hover};
    border-color: {self.colors.border_strong};
}}

QCheckBox::indicator:checked {{
    background-color: {self.colors.primary};
    border: 2px solid {self.colors.primary};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDZMMyA1TDQuNSA2LjVMOSAyTDEwIDNaIiBmaWxsPSJ3aGl0ZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIwLjUiLz4KPHN2Zz4K);
}}

QCheckBox::indicator:checked:hover {{
    background-color: {self.colors.primary_hover};
    border-color: {self.colors.primary_hover};
}}

QCheckBox::indicator:focus {{
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: 2px;
}}

QCheckBox::indicator:disabled {{
    background-color: {self.colors.surface_variant};
    border-color: {self.colors.border_light};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {self.colors.input_bg};
    border: 1px solid {self.colors.input_border};
    border-radius: 6px;
    padding: 8px 12px;
    color: {self.colors.text};
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    background-color: {self.colors.input_bg_hover};
    border-color: {self.colors.border_strong};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {self.colors.input_border_focus};
    outline: 2px solid {self.colors.focus_ring};
    outline-offset: -2px;
}}"""

    def get_scrollbar_stylesheet(self) -> str:
        """Get stylesheet for scrollbars and splitters."""
        return f"""
QSplitter::handle {{
    background-color: {self.colors.border};
    border-radius: 1px;
}}

QSplitter::handle:horizontal {{
    width: 3px;
    margin: 2px 0;
}}

QSplitter::handle:vertical {{
    height: 3px;
    margin: 0 2px;
}}

QSplitter::handle:hover {{
    background-color: {self.colors.border_strong};
}}

QScrollBar:vertical {{
    background-color: {self.colors.scrollbar_bg};
    width: 14px;
    border: none;
    border-radius: 7px;
    margin: 2px;
}}


QScrollBar::handle:vertical {{
    background-color: {self.colors.scrollbar_handle};
    min-height: 30px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {self.colors.scrollbar_handle_hover};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {self.colors.scrollbar_bg};
    height: 14px;
    border: none;
    border-radius: 7px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background-color: {self.colors.scrollbar_handle};
    min-width: 30px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {self.colors.scrollbar_handle_hover};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}"""

    def get_complete_stylesheet(self) -> str:
        """Get the complete stylesheet for the theme."""
        return "\n\n".join(
            [
                self.get_window_stylesheet(),
                self.get_navigation_stylesheet(),
                self.get_table_stylesheet(),
                self.get_form_stylesheet(),
                self.get_scrollbar_stylesheet(),
            ]
        )

    def get_status_colors(self) -> dict[str, str]:
        """Get colors for different status states."""
        return {
            "success": self.colors.success,
            "warning": self.colors.warning,
            "error": self.colors.error,
            "info": self.colors.info,
        }

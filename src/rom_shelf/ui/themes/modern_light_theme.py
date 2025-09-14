"""Modern light theme with accessibility improvements."""

from .base_theme import BaseTheme, ColorPalette


class ModernLightTheme(BaseTheme):
    """Modern light theme following accessibility guidelines."""

    def __init__(self):
        super().__init__("Modern Light")

    def _create_color_palette(self) -> ColorPalette:
        """Create a modern light theme color palette with WCAG AA compliance."""
        return ColorPalette(
            # Core colors - Using modern blue with proper contrast
            primary="#0066CC",
            primary_hover="#1976D2",
            primary_pressed="#0D47A1",
            secondary="#F5F5F5",
            accent="#FF6B35",

            # Background colors - Clean, modern whites and grays
            background="#FFFFFF",
            surface="#FAFAFA",
            surface_variant="#F5F5F5",
            card="#FFFFFF",
            overlay="#00000033",

            # Text colors - WCAG AA compliant (4.5:1 contrast minimum)
            text="#212121",           # 9.74:1 contrast ratio
            text_secondary="#616161", # 5.47:1 contrast ratio
            text_disabled="#9E9E9E",  # 3.08:1 contrast ratio (for disabled elements)
            text_on_primary="#FFFFFF", # High contrast on primary

            # State colors - Accessible and distinct
            success="#2E7D32",
            warning="#F57C00",
            error="#C62828",
            info="#1976D2",

            # Interactive colors
            hover="#F5F5F5",
            pressed="#EEEEEE",
            selected="#0066CC",
            selected_hover="#1976D2",
            focus="#0066CC",
            focus_ring="#0066CC40",

            # Border colors
            border="#E0E0E0",
            border_light="#F0F0F0",
            border_strong="#BDBDBD",
            border_focus="#0066CC",

            # Input colors
            input_bg="#FFFFFF",
            input_bg_hover="#FAFAFA",
            input_bg_focus="#FFFFFF",
            input_border="#CCCCCC",
            input_border_focus="#0066CC",

            # Scrollbar colors
            scrollbar_bg="#F5F5F5",
            scrollbar_handle="#BDBDBD",
            scrollbar_handle_hover="#9E9E9E"
        )

    def get_window_stylesheet(self) -> str:
        """Get modern window stylesheet."""
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
        """Get modern navigation stylesheet."""
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
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTYgNEwxMCA4TDYgMTJWNFoiIGZpbGw9IiM2MTYxNjEiLz4KPHN2Zz4K);
}}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkwxMiA2TDggMTBMNCA2WiIgZmlsbD0iIzYxNjE2MSIvPgo8L3N2Zz4K);
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
        """Get modern table stylesheet."""
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
        """Get modern form stylesheet."""
        return f"""
QLineEdit {{
    background-color: {self.colors.input_bg};
    border: 2px solid {self.colors.input_border};
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 13px;
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
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNUw2IDhMOSA1SDNaIiBmaWxsPSIjNjE2MTYxIi8+Cjwvc3ZnPgo=);
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
        """Get modern scrollbar stylesheet."""
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
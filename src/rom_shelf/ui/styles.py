"""UI styles and constants."""

DARK_STYLE = """
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMenuBar {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
}

QMenuBar::item {
    background-color: #3c3c3c;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background-color: #555555;
}

QMenu {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
}

QMenu::item {
    padding: 4px 16px;
}

QMenu::item:selected {
    background-color: #555555;
}

QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QTreeWidget {
    background-color: #353535;
    border: 1px solid #555555;
    outline: 0;
}

QTreeWidget::item {
    padding: 6px 4px;
    border: none;
    min-height: 24px;
}

QTreeWidget::item:selected {
    background-color: #555555;
}

QTreeWidget::item:hover {
    background-color: #404040;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
    image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVpY+xDYAwDAS/ECOwhRuwAiuwQpuwAhuwQpqwAVvQsAFbUKRNuKLy5XxfuQDeAF+ADxABM0DGGJP/4Ad4A7yZmZkNwADMZjab2QAMwGw2s9kADAAAAAB4mFkA);
}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
    image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABaSURBVBiVpY+xCQAwCAS/lKEcwi1cwpXcwpVcy5XcwpXcwSUcwi1cwsEpdXAOlwDvgC/AB4iAmWEwM2Zm/oAP4A3wzMxMBjAAMzOTAQzAzMxkAAMws9kAAAAA/gBZgAEOI1YnAAAAAElFTkSuQmCC);
}

QTreeWidget QCheckBox {
    spacing: 4px;
}

QTreeWidget QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QTreeWidget QCheckBox::indicator:unchecked {
    background-color: #404040;
    border: 2px solid #666666;
}

QTreeWidget QCheckBox::indicator:checked {
    background-color: #0078d4;
    border: 2px solid #0078d4;
    image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABQSURBVBiVpY4xDgAgCAPL//9Mh5MYNBhI2oBKLKK2oAzaDkUBOHgOYByAmRERERER8QEmADRmZmZ2AKAANmZmZnsAUICtmZndASAANgAAALiZAB0ICvuRAAAAAElFTkSuQmCC);
}

QTableView {
    background-color: #353535;
    alternate-background-color: #3a3a3a;
    border: 1px solid #555555;
    gridline-color: #555555;
    outline: 0;
}

QTableView::item {
    padding: 6px 8px;
    border: none;
}

QTableView::item:selected {
    background-color: #0078d4;
}

QHeaderView::section {
    background-color: #404040;
    color: #ffffff;
    padding: 6px;
    border: 1px solid #555555;
    border-left: none;
}

QHeaderView::section:first {
    border-left: 1px solid #555555;
}

QHeaderView::section:hover {
    background-color: #4a4a4a;
}

QScrollBar:vertical {
    background-color: #404040;
    width: 16px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #666666;
    min-height: 20px;
    border-radius: 8px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #777777;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background-color: #404040;
    height: 16px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #666666;
    min-width: 20px;
    border-radius: 8px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #777777;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

QLineEdit {
    background-color: #404040;
    border: 2px solid #555555;
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 12px;
}

QLineEdit:focus {
    border-color: #0078d4;
    background-color: #454545;
}

QToolBar {
    background-color: #353535;
    border: none;
    padding: 6px 8px;
    spacing: 8px;
}

QToolBar QToolButton {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
}

QToolBar QToolButton:hover {
    background-color: #4a4a4a;
    border-color: #0078d4;
}

QToolBar QToolButton:pressed {
    background-color: #0078d4;
}

QToolBar QLabel {
    color: #ffffff;
    background: transparent;
    border: none;
    padding: 0px 4px;
}

QToolBar QLineEdit {
    background-color: #404040;
    border: 1px solid #555555;
    padding: 4px 8px;
    border-radius: 4px;
    color: #ffffff;
    margin: 2px;
}

QToolBar QLineEdit:focus {
    border-color: #0078d4;
    background-color: #454545;
}

QStatusBar {
    background-color: #353535;
    border-top: 1px solid #555555;
    color: #cccccc;
    padding: 2px;
}

QLabel {
    color: #ffffff;
}
"""

LIGHT_STYLE = """
QMainWindow {
    background-color: #ffffff;
    color: #000000;
}

QWidget {
    background-color: #ffffff;
    color: #000000;
}

QMenuBar {
    background-color: #f0f0f0;
    color: #000000;
    border: 1px solid #cccccc;
}

QMenuBar::item {
    background-color: #f0f0f0;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenu {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #cccccc;
}

QMenu::item {
    padding: 4px 16px;
}

QMenu::item:selected {
    background-color: #e0e0e0;
}

QSplitter::handle {
    background-color: #cccccc;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    outline: 0;
}

QTreeWidget::item {
    padding: 6px 4px;
    border: none;
    min-height: 24px;
}

QTreeWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QTreeWidget::item:hover {
    background-color: #f0f0f0;
}

QTreeWidget QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QTreeWidget QCheckBox::indicator:unchecked {
    background-color: #ffffff;
    border: 2px solid #cccccc;
}

QTreeWidget QCheckBox::indicator:checked {
    background-color: #0078d4;
    border: 2px solid #0078d4;
}

QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8f8f8;
    border: 1px solid #cccccc;
    gridline-color: #e0e0e0;
    outline: 0;
}

QTableView::item {
    padding: 6px 8px;
    border: none;
}

QTableView::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #f0f0f0;
    color: #000000;
    padding: 6px;
    border: 1px solid #cccccc;
    border-left: none;
}

QHeaderView::section:first {
    border-left: 1px solid #cccccc;
}

QHeaderView::section:hover {
    background-color: #e8e8e8;
}

QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 16px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #cccccc;
    min-height: 20px;
    border-radius: 8px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #bbbbbb;
}

QScrollBar:horizontal {
    background-color: #f0f0f0;
    height: 16px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #cccccc;
    min-width: 20px;
    border-radius: 8px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #bbbbbb;
}

QLineEdit {
    background-color: #ffffff;
    border: 2px solid #cccccc;
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 12px;
}

QLineEdit:focus {
    border-color: #0078d4;
    background-color: #f8f9ff;
}

QToolBar {
    background-color: #f8f8f8;
    border: none;
    padding: 6px 8px;
    spacing: 8px;
}

QToolBar QToolButton {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 12px;
    color: #333333;
}

QToolBar QToolButton:hover {
    background-color: #f0f8ff;
    border-color: #0078d4;
}

QToolBar QToolButton:pressed {
    background-color: #0078d4;
    color: #ffffff;
}

QToolBar QLabel {
    color: #333333;
    background: transparent;
    border: none;
    padding: 0px 4px;
}

QToolBar QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    padding: 4px 8px;
    border-radius: 4px;
    color: #333333;
    margin: 2px;
}

QToolBar QLineEdit:focus {
    border-color: #0078d4;
    background-color: #f8f9ff;
}

QStatusBar {
    background-color: #f8f8f8;
    border-top: 1px solid #cccccc;
    color: #555555;
    padding: 2px;
}

QLabel {
    color: #000000;
}
"""

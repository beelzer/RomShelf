"""Modern, clean settings dialog using extracted components."""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.settings import SettingsManager
from ...platforms.platform_registry import platform_registry
from .interface_page import InterfacePage
from .platforms_page import PlatformsPage
from .platform_specific_page import PlatformSpecificPage
from .retroachievements_page import RetroAchievementsPage


class SettingsDialog(QDialog):
    """Settings dialog with sidebar navigation using extracted components."""

    # Signal emitted when settings are applied
    settings_applied = Signal()

    def __init__(self, settings_manager: SettingsManager, parent: QWidget | None = None) -> None:
        """Initialize the settings dialog."""
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._pages: dict[str, Any] = {}
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Main splitter
        splitter = QSplitter()
        layout.addWidget(splitter)

        # Left sidebar - Category tree
        self._category_tree = QTreeWidget()
        self._category_tree.setFixedWidth(200)
        self._category_tree.setHeaderHidden(True)
        self._category_tree.setRootIsDecorated(False)
        self._category_tree.itemClicked.connect(self._on_category_selected)
        splitter.addWidget(self._category_tree)

        # Right side - Stacked widget for pages
        self._page_stack = QStackedWidget()
        splitter.addWidget(self._page_stack)

        # Setup categories and pages
        self._setup_categories()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._apply_button = QPushButton("Apply")
        self._ok_button = QPushButton("OK")
        self._cancel_button = QPushButton("Cancel")

        # Connect button signals
        self._apply_button.clicked.connect(self._apply_settings)
        self._ok_button.clicked.connect(self._ok_clicked)
        self._cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self._apply_button)
        button_layout.addWidget(self._ok_button)
        button_layout.addWidget(self._cancel_button)

        layout.addLayout(button_layout)

        # Select first item by default
        if self._category_tree.topLevelItemCount() > 0:
            first_item = self._category_tree.topLevelItem(0)
            first_item.setSelected(True)
            self._on_category_selected(first_item, 0)

    def _setup_categories(self) -> None:
        """Set up the category tree and corresponding pages."""
        # Interface category
        interface_item = QTreeWidgetItem(self._category_tree)
        interface_item.setText(0, "Interface")
        interface_item.setData(0, 32, "interface")  # Store page identifier

        interface_page = InterfacePage()
        interface_page.settings_changed.connect(self._on_settings_changed)
        self._pages["interface"] = interface_page
        self._page_stack.addWidget(interface_page)

        # RetroAchievements category
        ra_item = QTreeWidgetItem(self._category_tree)
        ra_item.setText(0, "RetroAchievements")
        ra_item.setData(0, 32, "retroachievements")

        ra_page = RetroAchievementsPage(self._settings_manager)
        ra_page.settings_changed.connect(self._on_settings_changed)
        self._pages["retroachievements"] = ra_page
        self._page_stack.addWidget(ra_page)

        # Platforms category
        platforms_item = QTreeWidgetItem(self._category_tree)
        platforms_item.setText(0, "Platforms")
        platforms_item.setData(0, 32, "platforms")

        platforms_page = PlatformsPage(self._settings_manager)
        platforms_page.settings_changed.connect(self._on_settings_changed)
        self._pages["platforms"] = platforms_page
        self._page_stack.addWidget(platforms_page)

        # Platform-specific categories
        platforms = platform_registry.get_all_platforms()
        for platform in platforms:
            platform_item = QTreeWidgetItem(self._category_tree)
            platform_item.setText(0, platform.name)
            platform_key = f"platform_{platform.platform_id}"
            platform_item.setData(0, 32, platform_key)

            platform_page = PlatformSpecificPage(platform.platform_id, platform.name)
            platform_page.settings_changed.connect(self._on_settings_changed)
            self._pages[platform_key] = platform_page
            self._page_stack.addWidget(platform_page)

    def _on_category_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle category selection."""
        page_id = item.data(0, 32)
        if page_id in self._pages:
            page = self._pages[page_id]
            self._page_stack.setCurrentWidget(page)

    def _on_settings_changed(self) -> None:
        """Handle settings changes from any page."""
        self._apply_button.setEnabled(True)

    def _load_settings(self) -> None:
        """Load current settings into all pages."""
        settings = self._settings_manager.settings
        for page in self._pages.values():
            page.load_settings(settings)

    def _save_settings(self) -> None:
        """Save settings from all pages."""
        settings = self._settings_manager.settings
        for page in self._pages.values():
            page.save_settings(settings)

    def _apply_settings(self) -> None:
        """Apply settings changes."""
        self._save_settings()
        self._settings_manager.save()
        self.settings_applied.emit()
        self._apply_button.setEnabled(False)

    def _ok_clicked(self) -> None:
        """Handle OK button click."""
        self._apply_settings()
        self.accept()

    def exec(self) -> int:
        """Execute the dialog."""
        # Reload settings before showing
        self._load_settings()
        return super().exec()
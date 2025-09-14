"""Toolbar and menu management for the main window."""

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenuBar, QStatusBar, QToolBar


class ToolbarManager(QObject):
    """Manages toolbars, menus, and status bar for the main window."""

    def __init__(self, main_window: QMainWindow) -> None:
        """Initialize the toolbar manager."""
        super().__init__(main_window)
        self._main_window = main_window
        self._status_bar: QStatusBar | None = None

    def create_main_toolbar(self, refresh_callback, settings_callback) -> QToolBar:
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar", self._main_window)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._main_window.addToolBar(toolbar)

        # Refresh action
        refresh_action = QAction("Refresh", self._main_window)
        refresh_action.setStatusTip("Refresh ROM library")
        refresh_action.triggered.connect(refresh_callback)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # Settings action
        settings_action = QAction("Settings", self._main_window)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(settings_callback)
        toolbar.addAction(settings_action)

        return toolbar

    def create_menu_bar(self, refresh_callback, settings_callback) -> QMenuBar:
        """Create the menu bar."""
        menubar = self._main_window.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        refresh_action = QAction("Refresh Library", self._main_window)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(refresh_callback)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self._main_window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._main_window.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings...", self._main_window)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(settings_callback)
        tools_menu.addAction(settings_action)

        return menubar

    def create_status_bar(self) -> QStatusBar:
        """Create the status bar."""
        self._status_bar = QStatusBar(self._main_window)
        self._main_window.setStatusBar(self._status_bar)

        # Default status message
        self._status_bar.showMessage("Ready")
        return self._status_bar

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        if self._status_bar:
            self._status_bar.showMessage(message)

    def apply_font_settings(self, font) -> None:
        """Apply font settings to toolbar components."""
        # Apply to menu bar
        if hasattr(self._main_window, 'menuBar'):
            self._main_window.menuBar().setFont(font)

        # Apply to status bar
        if self._status_bar:
            self._status_bar.setFont(font)
"""Toolbar and menu management for the main window."""

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenuBar, QProgressBar, QStatusBar, QToolBar


class ToolbarManager(QObject):
    """Manages toolbars, menus, and status bar for the main window."""

    def __init__(self, main_window: QMainWindow) -> None:
        """Initialize the toolbar manager."""
        super().__init__(main_window)
        self._main_window = main_window
        self._status_bar: QStatusBar | None = None
        self._progress_bar: QProgressBar | None = None

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

        # Create progress bar (initially hidden)
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedSize(180, 20)  # Modern dimensions
        self._progress_bar.setTextVisible(True)  # Show percentage text
        self._progress_bar.setFormat("%p%")  # Show percentage format
        # Modern appearance
        self._progress_bar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Add progress bar to status bar (right side) without separators
        self._status_bar.addPermanentWidget(self._progress_bar, 0)  # 0 stretch, no separators

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
        if hasattr(self._main_window, "menuBar"):
            self._main_window.menuBar().setFont(font)

        # Apply to status bar
        if self._status_bar:
            self._status_bar.setFont(font)

    def show_progress_bar(self) -> None:
        """Show the progress bar in the status bar."""
        if self._progress_bar:
            self._progress_bar.setVisible(True)
            self._progress_bar.setValue(0)
            self._progress_bar.setRange(0, 100)
            # Force initial update
            self._progress_bar.repaint()

    def hide_progress_bar(self) -> None:
        """Hide the progress bar in the status bar."""
        if self._progress_bar:
            self._progress_bar.setVisible(False)

    def update_progress(self, value: int, message: str = "") -> None:
        """Update progress bar value and optionally the status message."""
        if self._progress_bar:
            # Ensure the progress bar is in determinate mode
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setRange(0, 100)

            # Clamp value and force UI update
            clamped_value = min(max(value, 0), 100)

            # Debug output to track progress bar updates
            current_value = self._progress_bar.value()
            print(f"ProgressBar: Setting value from {current_value} to {clamped_value}%")

            self._progress_bar.setValue(clamped_value)

            # Force immediate repaint to ensure visual update
            self._progress_bar.repaint()

        if message and self._status_bar:
            self._status_bar.showMessage(message)

    def set_progress_indeterminate(self, indeterminate: bool = True) -> None:
        """Set progress bar to indeterminate mode."""
        if self._progress_bar:
            print(f"ProgressBar: Setting indeterminate mode to {indeterminate}")
            if indeterminate:
                self._progress_bar.setRange(0, 0)
            else:
                self._progress_bar.setRange(0, 100)
                # Don't reset value when switching to determinate - preserve current progress
                current_value = self._progress_bar.value()
                print(
                    f"ProgressBar: Set to determinate mode (0-100, preserving value={current_value})"
                )
            # Force visual update
            self._progress_bar.repaint()

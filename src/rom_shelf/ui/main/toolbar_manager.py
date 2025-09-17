"""Toolbar and menu management for the main window."""

import logging

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenuBar, QProgressBar, QStatusBar, QToolBar

from ..widgets.scan_progress_widget import ScanProgressWidget


class ToolbarManager(QObject):
    """Manages toolbars, menus, and status bar for the main window."""

    def __init__(self, main_window: QMainWindow) -> None:
        """Initialize the toolbar manager."""
        super().__init__(main_window)
        self.logger = logging.getLogger(__name__)
        self._main_window = main_window
        self._status_bar: QStatusBar | None = None
        self._progress_bar: QProgressBar | None = None
        self._progress_widget: ScanProgressWidget | None = None
        self._ra_match_count = 0

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

        # Create expandable progress widget
        self._progress_widget = ScanProgressWidget(self._status_bar)
        self._progress_widget.setVisible(False)

        # Add progress widget to status bar (takes full width when visible)
        self._status_bar.addWidget(self._progress_widget, 1)  # Stretch factor 1

        # Create old-style progress bar for compatibility (hidden by default)
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedSize(180, 20)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Keep old progress bar for fallback
        self._status_bar.addPermanentWidget(self._progress_bar, 0)

        # Default status message
        self._status_bar.showMessage("Ready")
        return self._status_bar

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        if self._status_bar:
            # If progress widget is visible, update it instead
            if self._progress_widget and self._progress_widget.isVisible():
                self._progress_widget.update_status(message)
            else:
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
        # Hide status message when showing progress
        if self._status_bar:
            self._status_bar.clearMessage()

        # Show expandable progress widget
        if self._progress_widget:
            self._progress_widget.clear()
            self._progress_widget.setVisible(True)
            self._ra_match_count = 0

        # Keep old progress bar hidden
        if self._progress_bar:
            self._progress_bar.setVisible(False)

    def hide_progress_bar(self) -> None:
        """Hide the progress bar in the status bar."""
        if self._progress_widget:
            self._progress_widget.set_completed()
            # Don't automatically hide - let user close it or keep it for history
            # Widget remains accessible until user collapses and a new scan starts

        if self._progress_bar:
            self._progress_bar.setVisible(False)

    def update_progress(self, value: int, message: str = "") -> None:
        """Update progress bar value and optionally the status message."""
        # Update expandable widget
        if self._progress_widget and self._progress_widget.isVisible():
            self._progress_widget.set_progress(value)
            if message:
                self._progress_widget.update_status(message)

        # Keep old progress bar logic for compatibility
        if self._progress_bar and self._progress_bar.isVisible():
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setRange(0, 100)
            clamped_value = min(max(value, 0), 100)
            current_value = self._progress_bar.value()
            self.logger.debug(
                f"ProgressBar: Setting value from {current_value} to {clamped_value}%"
            )
            self._progress_bar.setValue(clamped_value)
            self._progress_bar.repaint()

        if message and self._status_bar and not self._progress_widget:
            self._status_bar.showMessage(message)

    def set_progress_indeterminate(self, indeterminate: bool = True) -> None:
        """Set progress bar to indeterminate mode."""
        # Update expandable widget
        if self._progress_widget and self._progress_widget.isVisible():
            self._progress_widget.set_indeterminate(indeterminate)

        # Keep old logic for compatibility
        if self._progress_bar and self._progress_bar.isVisible():
            self.logger.debug(f"ProgressBar: Setting indeterminate mode to {indeterminate}")
            if indeterminate:
                self._progress_bar.setRange(0, 0)
            else:
                self._progress_bar.setRange(0, 100)
                current_value = self._progress_bar.value()
                self.logger.debug(
                    f"ProgressBar: Set to determinate mode (0-100, preserving value={current_value})"
                )
            self._progress_bar.repaint()

    def update_scan_details(
        self,
        operation: str = None,
        current_file: str = None,
        files_processed: int = None,
        total_files: int = None,
        roms_found: int = None,
        ra_matches: int = None,
        detail_message: str = None,
        message_type: str = "info",
    ):
        """Update detailed scan progress information.

        Args:
            operation: Current operation description
            current_file: Path of file being processed
            files_processed: Number of files processed
            total_files: Total number of files to process
            roms_found: Number of ROMs found
            ra_matches: Number of RetroAchievements matches
            detail_message: Detailed message to add to log
            message_type: Type of detail message ('info', 'success', 'warning', 'error')
        """
        if not self._progress_widget or not self._progress_widget.isVisible():
            return

        if operation:
            self._progress_widget.update_operation(operation)

        if current_file is not None:
            self._progress_widget.update_current_file(current_file)

        if files_processed is not None and total_files is not None:
            self._progress_widget.update_file_progress(files_processed, total_files)

        if roms_found is not None:
            self._progress_widget.update_rom_count(roms_found)

        if ra_matches is not None:
            self._ra_match_count = ra_matches
            self._progress_widget.update_ra_matches(ra_matches)

        if detail_message:
            self._progress_widget.add_detail_message(detail_message, message_type)

    def increment_ra_matches(self):
        """Increment the RetroAchievements match counter."""
        self._ra_match_count += 1
        if self._progress_widget and self._progress_widget.isVisible():
            self._progress_widget.update_ra_matches(self._ra_match_count)

    def update_download_progress(
        self, bytes_downloaded: int, total_bytes: int = 0, speed_bps: float = 0
    ):
        """Update download progress information.

        Args:
            bytes_downloaded: Number of bytes downloaded
            total_bytes: Total size in bytes (0 if unknown)
            speed_bps: Download speed in bytes per second
        """
        if self._progress_widget and self._progress_widget.isVisible():
            self._progress_widget.update_download_progress(bytes_downloaded, total_bytes, speed_bps)

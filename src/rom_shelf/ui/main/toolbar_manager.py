"""Toolbar and menu management for the main window."""

import logging

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QToolBar,
)


class ToolbarManager(QObject):
    """Manages toolbars, menus, and status bar for the main window."""

    def __init__(self, main_window: QMainWindow) -> None:
        """Initialize the toolbar manager."""
        super().__init__(main_window)
        self.logger = logging.getLogger(__name__)
        self._main_window = main_window
        self._status_bar: QStatusBar | None = None
        self._progress_bar: QProgressBar | None = None
        self._progress_label: QLabel | None = None
        self._expand_button: QPushButton | None = None
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
        self._status_bar.setSizeGripEnabled(False)
        self._main_window.setStatusBar(self._status_bar)

        # Create compact progress bar for status bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedSize(180, 20)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")

        # Progress label
        self._progress_label = QLabel("")
        self._progress_label.setVisible(False)

        # Button to show/hide scan details dock
        self._expand_button = QPushButton("Show Details")
        self._expand_button.setFixedHeight(20)
        self._expand_button.setVisible(False)
        self._expand_button.clicked.connect(self._toggle_scan_dock)

        # Add widgets to status bar
        self._status_bar.addPermanentWidget(self._progress_label)
        self._status_bar.addPermanentWidget(self._progress_bar)
        self._status_bar.addPermanentWidget(self._expand_button)

        # Default status message
        self._status_bar.showMessage("Ready")
        return self._status_bar

    def _toggle_scan_dock(self):
        """Toggle the scan progress dock visibility."""
        if hasattr(self._main_window, "_scan_dock") and self._main_window._scan_dock:
            dock = self._main_window._scan_dock
            if dock.isVisible():
                dock.hide()
                self._expand_button.setText("Show Details")
            else:
                dock.show()
                self._expand_button.setText("Hide Details")

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        if self._status_bar:
            # Always show regular status messages in the status bar
            # The progress widget is only for scan-related messages
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
        # Show progress components
        if self._progress_bar:
            self._progress_bar.setValue(0)
            self._progress_bar.setVisible(True)
        if self._progress_label:
            self._progress_label.setText("Scanning...")
            self._progress_label.setVisible(True)
        if self._expand_button:
            self._expand_button.setVisible(True)

        # Show and clear dock if available
        if hasattr(self._main_window, "_scan_dock") and self._main_window._scan_dock:
            self._main_window._scan_dock.clear()
            self._main_window._scan_dock.show()
            self._expand_button.setText("Hide Details")

        self._ra_match_count = 0

    def hide_progress_bar(self) -> None:
        """Hide the progress bar in the status bar."""
        # Mark scan as completed in dock
        if hasattr(self._main_window, "_scan_dock") and self._main_window._scan_dock:
            self._main_window._scan_dock.set_completed()
            # Don't auto-hide dock - let user close it

        # Hide progress bar but keep button visible
        if self._progress_bar:
            self._progress_bar.setVisible(False)
        if self._progress_label:
            self._progress_label.setVisible(False)

    def update_progress(self, value: int, message: str = "") -> None:
        """Update progress bar value and optionally the status message."""
        # Update progress bar
        if self._progress_bar and self._progress_bar.isVisible():
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setRange(0, 100)
            clamped_value = min(max(value, 0), 100)
            self._progress_bar.setValue(clamped_value)

        # Update label if message provided
        if message and self._progress_label:
            self._progress_label.setText(message)

    def set_progress_indeterminate(self, indeterminate: bool = True) -> None:
        """Set progress bar to indeterminate mode."""
        if self._progress_bar and self._progress_bar.isVisible():
            if indeterminate:
                self._progress_bar.setRange(0, 0)
            else:
                self._progress_bar.setRange(0, 100)

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
        # Update dock if available
        if not hasattr(self._main_window, "_scan_dock") or not self._main_window._scan_dock:
            return

        dock = self._main_window._scan_dock

        if files_processed is not None and total_files is not None:
            dock.update_file_progress(files_processed, total_files)
            # Update progress bar percentage
            if total_files > 0:
                percentage = int((files_processed / total_files) * 100)
                self.update_progress(percentage)

        if roms_found is not None:
            dock.update_rom_count(roms_found)

        if ra_matches is not None:
            self._ra_match_count = ra_matches
            dock.update_ra_matches(ra_matches)

        if detail_message:
            dock.add_detail_message(detail_message, message_type)

    def increment_ra_matches(self):
        """Increment the RetroAchievements match counter."""
        self._ra_match_count += 1
        if hasattr(self._main_window, "_scan_dock") and self._main_window._scan_dock:
            self._main_window._scan_dock.update_ra_matches(self._ra_match_count)

    def update_download_progress(
        self, bytes_downloaded: int, total_bytes: int = 0, speed_bps: float = 0
    ):
        """Update download progress information.

        Args:
            bytes_downloaded: Number of bytes downloaded
            total_bytes: Total size in bytes (0 if unknown)
            speed_bps: Download speed in bytes per second
        """
        # Download progress tracking removed - not currently used

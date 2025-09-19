"""Toolbar and menu management for the main window."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QProgressBar,
    QStatusBar,
    QToolBar,
    QWidget,
)


class ToolbarManager(QObject):
    """Manages toolbars, menus, and status bar for the main window."""

    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window)
        self.logger = logging.getLogger(__name__)
        self._main_window = main_window
        self._status_bar: QStatusBar | None = None
        self._progress_bar: QProgressBar | None = None
        self._progress_label: QLabel | None = None
        self._scan_dock = None
        self._ra_match_count = 0

    # Wiring ---------------------------------------------------------------------------

    def attach_scan_dock(self, scan_dock) -> None:
        """Let the toolbar manager collaborate with the scan progress dock."""
        self._scan_dock = scan_dock

    # Toolbar and menu -----------------------------------------------------------------

    def create_main_toolbar(self, refresh_callback, settings_callback) -> QToolBar:
        toolbar = QToolBar("Main Toolbar", self._main_window)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._main_window.addToolBar(toolbar)

        refresh_action = QAction("Refresh", self._main_window)
        refresh_action.setStatusTip("Refresh ROM library")
        refresh_action.triggered.connect(refresh_callback)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        settings_action = QAction("Settings", self._main_window)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(settings_callback)
        toolbar.addAction(settings_action)

        return toolbar

    def create_menu_bar(self, refresh_callback, settings_callback) -> QMenuBar:
        menubar = self._main_window.menuBar()

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

        tools_menu = menubar.addMenu("Tools")
        settings_action = QAction("Settings...", self._main_window)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(settings_callback)
        tools_menu.addAction(settings_action)

        return menubar

    # Status bar -----------------------------------------------------------------------

    def create_status_bar(self) -> QStatusBar:
        self._status_bar = QStatusBar(self._main_window)
        self._status_bar.setSizeGripEnabled(False)
        self._main_window.setStatusBar(self._status_bar)

        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 12, 0)
        right_layout.setSpacing(8)

        self._progress_label = QLabel("")
        self._progress_label.setVisible(False)
        right_layout.addWidget(self._progress_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedSize(180, 18)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        right_layout.addWidget(self._progress_bar)

        self._status_bar.addPermanentWidget(right_container)
        self._status_bar.showMessage("Ready")
        return self._status_bar

    def update_status(self, message: str) -> None:
        if self._status_bar:
            self._status_bar.showMessage(message)

    def apply_font_settings(self, font) -> None:
        if hasattr(self._main_window, "menuBar"):
            self._main_window.menuBar().setFont(font)
        if self._status_bar:
            self._status_bar.setFont(font)

    # Progress helpers -----------------------------------------------------------------

    def show_progress_bar(self) -> None:
        if self._progress_bar:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
            self._progress_bar.setVisible(True)
        if self._progress_label:
            self._progress_label.setText("Scanning...")
            self._progress_label.setVisible(True)
        self._ra_match_count = 0

    def hide_progress_bar(self) -> None:
        if self._progress_bar:
            self._progress_bar.setVisible(False)
        if self._progress_label:
            self._progress_label.setVisible(False)

    def update_progress(self, value: int, message: str = "") -> None:
        if self._progress_bar and self._progress_bar.isVisible():
            clamped_value = min(max(value, 0), 100)
            self._progress_bar.setValue(clamped_value)
        if message and self._progress_label:
            self._progress_label.setText(message)

    def set_progress_indeterminate(self, indeterminate: bool = True) -> None:
        if not self._progress_bar or not self._progress_bar.isVisible():
            return
        self._progress_bar.setRange(0, 0 if indeterminate else 100)

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
    ) -> None:
        if not self._scan_dock:
            return

        if files_processed is not None and total_files is not None:
            self._scan_dock.update_file_progress(files_processed, total_files)
            if total_files > 0:
                percentage = int((files_processed / total_files) * 100)
                self.update_progress(percentage)

        if roms_found is not None:
            self._scan_dock.update_rom_count(roms_found)

        if ra_matches is not None:
            self._ra_match_count = ra_matches
            self._scan_dock.update_ra_matches(ra_matches)

        if detail_message:
            self._scan_dock.add_detail_message(detail_message, message_type)

    def increment_ra_matches(self) -> None:
        self._ra_match_count += 1
        if self._scan_dock:
            self._scan_dock.update_ra_matches(self._ra_match_count)

    def update_download_progress(
        self, bytes_downloaded: int, total_bytes: int = 0, speed_bps: float = 0
    ) -> None:
        """Update download progress information (currently unused)."""
        # Download progress tracking removed - not currently used
        _ = (bytes_downloaded, total_bytes, speed_bps)

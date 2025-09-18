"""Dockable scan progress widget that appears below the main window."""

import logging
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ScanProgressDock(QDockWidget):
    """Dockable widget showing detailed scan progress."""

    def __init__(self, parent=None):
        """Initialize the scan progress dock."""
        super().__init__("Scan Progress Details", parent)
        self.logger = logging.getLogger(__name__)

        # Configure dock widget
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )

        # State
        self._detail_messages = []
        self._max_detail_messages = 1000

        self._setup_ui()

        # Start hidden
        self.hide()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)

        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Create frame for visual separation
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame_layout = QHBoxLayout(frame)

        # Left panel - Statistics (narrower)
        left_panel = QWidget()
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(4)

        # Changes section
        changes_label = QLabel("Changes:")
        changes_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(changes_label)

        self._new_roms_label = QLabel("New: 0")
        self._new_roms_label.setStyleSheet("color: #4CAF50; padding-left: 10px;")
        left_layout.addWidget(self._new_roms_label)

        self._modified_roms_label = QLabel("Modified: 0")
        self._modified_roms_label.setStyleSheet("color: #FFA500; padding-left: 10px;")
        left_layout.addWidget(self._modified_roms_label)

        self._removed_roms_label = QLabel("Removed: 0")
        self._removed_roms_label.setStyleSheet("color: #F44336; padding-left: 10px;")
        left_layout.addWidget(self._removed_roms_label)

        self._existing_roms_label = QLabel("Existing: 0")
        self._existing_roms_label.setStyleSheet("color: #888888; padding-left: 10px;")
        left_layout.addWidget(self._existing_roms_label)

        # Progress section
        left_layout.addSpacing(20)
        progress_label = QLabel("Progress:")
        progress_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(progress_label)

        self._files_label = QLabel("Files checked: 0/0")
        self._files_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._files_label)

        self._roms_label = QLabel("ROMs validated: 0")
        self._roms_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._roms_label)

        self._ra_label = QLabel("RA matches: 0")
        self._ra_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._ra_label)

        left_layout.addStretch()

        # Right panel - Detailed log
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)

        log_label = QLabel("Scan Log:")
        log_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(log_label)

        # Text area for detailed messages
        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        right_layout.addWidget(self._detail_text)

        # Add panels to frame
        frame_layout.addWidget(left_panel)
        frame_layout.addWidget(right_panel, 1)  # Right panel gets stretch

        # Add frame to main layout
        layout.addWidget(frame)

        # Set a reasonable default height
        self.setMinimumHeight(200)
        self.setMaximumHeight(400)

    def clear(self):
        """Clear all progress information."""
        self._detail_messages.clear()
        self._detail_text.clear()
        self.update_scan_changes(0, 0, 0, 0)
        self.update_file_progress(0, 0)
        self.update_rom_count(0)
        self.update_ra_matches(0)

    def update_scan_changes(self, new=None, modified=None, removed=None, existing=None):
        """Update scan change statistics."""
        if new is not None:
            self._new_roms_label.setText(f"New: {new}")
        if modified is not None:
            self._modified_roms_label.setText(f"Modified: {modified}")
        if removed is not None:
            self._removed_roms_label.setText(f"Removed: {removed}")
        if existing is not None:
            self._existing_roms_label.setText(f"Existing: {existing}")

    def update_file_progress(self, current, total):
        """Update file processing progress."""
        self._files_label.setText(f"Files checked: {current}/{total}")

    def update_rom_count(self, count):
        """Update the number of ROMs found."""
        self._roms_label.setText(f"ROMs validated: {count}")

    def update_ra_matches(self, count):
        """Update RetroAchievements match count."""
        self._ra_label.setText(f"RA matches: {count}")

    def add_detail_message(self, message, message_type="info"):
        """Add a detailed message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color based on type
        color_map = {
            "info": "#ffffff",
            "success": "#4CAF50",
            "warning": "#FFA500",
            "error": "#F44336",
        }
        color = color_map.get(message_type, "#ffffff")

        # Format message with timestamp and color
        formatted_message = f'<span style="color: #888888">[{timestamp}]</span> <span style="color: {color}">{message}</span>'

        # Add to list
        self._detail_messages.append(formatted_message)

        # Trim if needed
        if len(self._detail_messages) > self._max_detail_messages:
            self._detail_messages = self._detail_messages[-self._max_detail_messages :]

        # Update display
        self._detail_text.append(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self._detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_completed(self):
        """Mark the scan as completed."""
        self.add_detail_message("Scan completed", "success")

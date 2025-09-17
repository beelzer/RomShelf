"""Expandable scan progress widget for detailed progress information."""

import logging

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ScanProgressWidget(QWidget):
    """Widget showing expandable scan progress information."""

    # Signal emitted when expand/collapse state changes
    expand_toggled = Signal(bool)

    def __init__(self, parent=None):
        """Initialize the scan progress widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # State
        self._expanded = False
        self._total_files = 0
        self._files_processed = 0
        self._roms_found = 0
        self._current_operation = ""
        self._detail_messages = []
        self._max_detail_messages = 100  # Keep last 100 messages

        # Animation
        self._animation = None

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Compact view (always visible)
        compact_frame = QFrame()
        compact_frame.setFrameStyle(QFrame.Shape.NoFrame)
        compact_layout = QHBoxLayout(compact_frame)
        compact_layout.setContentsMargins(8, 4, 8, 4)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setMaximumHeight(20)
        compact_layout.addWidget(self._progress_bar, 1)

        # Status label (short summary)
        self._status_label = QLabel("Ready")
        self._status_label.setMinimumWidth(200)
        compact_layout.addWidget(self._status_label)

        # Expand/collapse button
        self._expand_button = QPushButton("▶")
        self._expand_button.setMaximumWidth(30)
        self._expand_button.setToolTip("Show detailed progress")
        self._expand_button.clicked.connect(self._toggle_expand)
        self._expand_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 2px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
        """)
        compact_layout.addWidget(self._expand_button)

        layout.addWidget(compact_frame)

        # Detailed view (collapsible)
        self._detail_widget = QWidget()
        self._detail_widget.setMaximumHeight(0)
        self._detail_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        detail_layout = QVBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(8, 8, 8, 8)
        detail_layout.setSpacing(4)

        # Detail info frame
        detail_info_frame = QFrame()
        detail_info_frame.setFrameStyle(QFrame.Shape.Box)
        detail_info_layout = QVBoxLayout(detail_info_frame)
        detail_info_layout.setContentsMargins(8, 8, 8, 8)
        detail_info_layout.setSpacing(4)

        # Current operation
        self._operation_label = QLabel("Operation: Idle")
        self._operation_label.setStyleSheet("font-weight: bold;")
        detail_info_layout.addWidget(self._operation_label)

        # Statistics
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._files_label = QLabel("Files: 0/0")
        stats_layout.addWidget(self._files_label)

        self._roms_label = QLabel("ROMs Found: 0")
        stats_layout.addWidget(self._roms_label)

        self._matches_label = QLabel("RA Matches: 0")
        stats_layout.addWidget(self._matches_label)

        self._download_label = QLabel("")
        self._download_label.setStyleSheet("color: #4CAF50;")
        stats_layout.addWidget(self._download_label)

        stats_layout.addStretch()
        detail_info_layout.addLayout(stats_layout)

        # Current file being processed
        self._current_file_label = QLabel("Current: None")
        self._current_file_label.setWordWrap(True)
        self._current_file_label.setStyleSheet("color: #888;")
        detail_info_layout.addWidget(self._current_file_label)

        detail_layout.addWidget(detail_info_frame)

        # Detail log (scrollable text)
        self._detail_log = QTextEdit()
        self._detail_log.setReadOnly(True)
        self._detail_log.setMaximumHeight(150)
        self._detail_log.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 4px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        detail_layout.addWidget(self._detail_log)

        layout.addWidget(self._detail_widget)

    def _toggle_expand(self):
        """Toggle expanded/collapsed state."""
        self._expanded = not self._expanded

        # Update button
        self._expand_button.setText("▼" if self._expanded else "▶")
        self._expand_button.setToolTip(
            "Hide detailed progress" if self._expanded else "Show detailed progress"
        )

        # Animate height change
        if self._animation:
            self._animation.stop()

        self._animation = QPropertyAnimation(self._detail_widget, b"maximumHeight")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if self._expanded:
            # Calculate required height
            target_height = 250  # Fixed height for expanded view
            self._animation.setStartValue(0)
            self._animation.setEndValue(target_height)
        else:
            self._animation.setStartValue(self._detail_widget.maximumHeight())
            self._animation.setEndValue(0)

        self._animation.start()
        self.expand_toggled.emit(self._expanded)

    def set_progress(self, value: int):
        """Set progress bar value (0-100)."""
        self._progress_bar.setValue(value)

    def set_indeterminate(self, indeterminate: bool):
        """Set progress bar to indeterminate mode."""
        if indeterminate:
            self._progress_bar.setRange(0, 0)
        else:
            self._progress_bar.setRange(0, 100)

    def update_status(self, message: str):
        """Update the status message."""
        # Truncate if too long for compact view
        max_length = 50
        if len(message) > max_length:
            message = message[: max_length - 3] + "..."
        self._status_label.setText(message)

    def update_operation(self, operation: str):
        """Update the current operation description."""
        self._current_operation = operation
        self._operation_label.setText(f"Operation: {operation}")

        # Add to detail log
        self._add_detail_message(f"[{self._get_timestamp()}] {operation}")

    def update_file_progress(self, current: int, total: int):
        """Update file processing progress."""
        self._files_processed = current
        self._total_files = total
        self._files_label.setText(f"Files: {current}/{total}")

        # Update progress bar
        if total > 0:
            percentage = int((current / total) * 100)
            self.set_progress(percentage)

    def update_rom_count(self, count: int):
        """Update the number of ROMs found."""
        self._roms_found = count
        self._roms_label.setText(f"ROMs Found: {count}")

    def update_ra_matches(self, count: int):
        """Update the number of RetroAchievements matches."""
        self._matches_label.setText(f"RA Matches: {count}")

    def update_current_file(self, filepath: str):
        """Update the current file being processed."""
        # Show just the filename for space
        if filepath:
            filename = filepath.split("/")[-1].split("\\")[-1]
            display_text = f"Current: {filename}"
        else:
            display_text = "Current: None"

        self._current_file_label.setText(display_text)

    def add_detail_message(self, message: str, message_type: str = "info"):
        """Add a detailed message to the log.

        Args:
            message: The message to add
            message_type: Type of message ('info', 'success', 'warning', 'error')
        """
        self._add_detail_message(f"[{self._get_timestamp()}] {message}", message_type)

    def _add_detail_message(self, message: str, message_type: str = "info"):
        """Internal method to add message with formatting."""
        # Color coding based on type
        colors = {
            "info": "#ffffff",
            "success": "#4CAF50",
            "warning": "#FFA726",
            "error": "#EF5350",
        }
        color = colors.get(message_type, "#ffffff")

        # Add to messages list
        self._detail_messages.append((message, color))

        # Keep only last N messages
        if len(self._detail_messages) > self._max_detail_messages:
            self._detail_messages = self._detail_messages[-self._max_detail_messages :]

        # Update display
        self._update_detail_log()

    def _update_detail_log(self):
        """Update the detail log display."""
        html_lines = []
        for message, color in self._detail_messages[-20:]:  # Show last 20 messages
            html_lines.append(f'<span style="color: {color};">{message}</span>')

        self._detail_log.setHtml("<br>".join(html_lines))

        # Scroll to bottom
        scrollbar = self._detail_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _get_timestamp(self):
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")

    def clear(self):
        """Clear all progress information."""
        self._files_processed = 0
        self._total_files = 0
        self._roms_found = 0
        self._current_operation = ""
        self._detail_messages = []

        self.set_progress(0)
        self.update_status("Ready")
        self.update_operation("Idle")
        self.update_file_progress(0, 0)
        self.update_rom_count(0)
        self.update_ra_matches(0)
        self.update_current_file("")
        self._detail_log.clear()

    def set_completed(self):
        """Set the widget to show completion state."""
        self.set_progress(100)
        self.update_status("Scan completed")
        self.update_operation("Completed")
        self.add_detail_message(f"Scan completed: {self._roms_found} ROMs found", "success")

        # Keep expand button functional
        self._expand_button.setEnabled(True)

    def update_download_progress(
        self, bytes_downloaded: int, total_bytes: int = 0, speed_bps: float = 0
    ):
        """Update download progress information.

        Args:
            bytes_downloaded: Number of bytes downloaded
            total_bytes: Total size in bytes (0 if unknown)
            speed_bps: Download speed in bytes per second
        """
        if speed_bps > 0:
            # Format speed
            if speed_bps > 1024 * 1024:
                speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s"
            elif speed_bps > 1024:
                speed_str = f"{speed_bps / 1024:.1f} KB/s"
            else:
                speed_str = f"{speed_bps:.0f} B/s"

            if total_bytes > 0:
                progress_pct = (bytes_downloaded / total_bytes) * 100
                self._download_label.setText(f"Downloading: {progress_pct:.0f}% @ {speed_str}")
            else:
                mb_downloaded = bytes_downloaded / (1024 * 1024)
                self._download_label.setText(f"Downloaded: {mb_downloaded:.1f} MB @ {speed_str}")
        elif bytes_downloaded > 0:
            mb_downloaded = bytes_downloaded / (1024 * 1024)
            self._download_label.setText(f"Downloaded: {mb_downloaded:.1f} MB")
        else:
            self._download_label.setText("")

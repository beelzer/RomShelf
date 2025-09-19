"""Floating scan progress dialog that appears below the main window."""

import logging
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..themes import get_theme_manager


class ScanProgressDialog(QDialog):
    """Floating dialog showing detailed scan progress."""

    # Signal emitted when dialog is closed
    dialog_closed = Signal()

    def __init__(self, parent=None):
        """Initialize the scan progress dialog."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Window flags to make it tool window that stays on top
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self.setWindowTitle("Scan Progress Details")
        self.setMinimumSize(600, 400)

        # State
        self._detail_messages = []
        self._max_detail_messages = 1000

        self._setup_ui()

        # Position below parent window if possible
        if parent:
            self._position_below_parent()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
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
        self._new_roms_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._new_roms_label)

        self._modified_roms_label = QLabel("Modified: 0")
        self._modified_roms_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._modified_roms_label)

        self._removed_roms_label = QLabel("Removed: 0")
        self._removed_roms_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._removed_roms_label)

        self._existing_roms_label = QLabel("Existing: 0")
        self._existing_roms_label.setStyleSheet("padding-left: 10px;")
        left_layout.addWidget(self._existing_roms_label)

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
        self._detail_text.setStyleSheet("")
        right_layout.addWidget(self._detail_text)

        # Add panels to frame
        frame_layout.addWidget(left_panel)
        frame_layout.addWidget(right_panel, 1)  # Right panel gets stretch

        # Add frame to main layout
        layout.addWidget(frame)

        # Close button at bottom
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        self._apply_theme()

    def apply_theme(self) -> None:
        """Public hook to refresh themed styling."""
        self._apply_theme()
        self._refresh_detail_text()

    def _apply_theme(self) -> None:
        """Apply the current palette to child widgets."""
        theme_manager = get_theme_manager()
        palette = theme_manager.get_palette()
        status_colors = theme_manager.get_status_colors()

        text_color = palette.text
        success_color = status_colors.get("success", palette.success)
        warning_color = status_colors.get("warning", palette.warning)
        error_color = status_colors.get("error", palette.error)
        existing_color = palette.text_secondary
        detail_overlay = theme_manager.color_with_alpha("overlay", 0.35)
        border_color = palette.border

        if self._new_roms_label:
            self._new_roms_label.setStyleSheet(f"color: {success_color}; padding-left: 10px;")
        if self._modified_roms_label:
            self._modified_roms_label.setStyleSheet(f"color: {warning_color}; padding-left: 10px;")
        if self._removed_roms_label:
            self._removed_roms_label.setStyleSheet(f"color: {error_color}; padding-left: 10px;")
        if self._existing_roms_label:
            self._existing_roms_label.setStyleSheet(f"color: {existing_color}; padding-left: 10px;")

        if self._detail_text:
            self._detail_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {detail_overlay};
                    color: {text_color};
                    font-family: Consolas, 'Courier New', monospace;
                    font-size: 10pt;
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)

    def _refresh_detail_text(self) -> None:
        """Rebuild the HTML log using the active theme colors."""
        if not self._detail_text:
            return

        theme_manager = get_theme_manager()
        status_colors = theme_manager.get_status_colors()
        timestamp_color = theme_manager.get_color("text_secondary")
        default_color = status_colors.get("info", theme_manager.get_color("text"))

        html_lines: list[str] = []
        for timestamp, message, level in self._detail_messages[-self._max_detail_messages :]:
            color = status_colors.get(level, default_color)
            html_lines.append(
                f'<span style="color: {timestamp_color}">[{timestamp}]</span> '
                f'<span style="color: {color}">{message}</span>'
            )

        self._detail_text.setHtml("<br>".join(html_lines))
        scrollbar = self._detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _position_below_parent(self):
        """Position dialog below parent window."""
        if not self.parent():
            return

        parent = self.parent()
        # Get parent geometry
        parent_rect = parent.geometry()

        # Calculate position below parent
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + parent_rect.height() + 10  # 10px gap

        self.move(x, y)

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

    def add_detail_message(self, message, message_type="info"):
        """Add a detailed message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        level = message_type.lower()

        # Track message meta so we can re-render on theme changes
        self._detail_messages.append((timestamp, message, level))

        if len(self._detail_messages) > self._max_detail_messages:
            self._detail_messages = self._detail_messages[-self._max_detail_messages :]

        self._refresh_detail_text()

    def closeEvent(self, event):
        """Handle dialog close event."""
        self.dialog_closed.emit()
        super().closeEvent(event)

"""Dockable scan progress widget that appears below the main window."""

import logging
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..themes import get_theme_manager


class ScanProgressDock(QDockWidget):
    """Dockable widget showing detailed scan progress."""

    def __init__(self, parent=None):
        """Initialize the scan progress dock."""
        super().__init__("", parent)  # Empty title
        self.logger = logging.getLogger(__name__)

        # Configure dock widget - no title bar, no close button
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget())  # Hide title bar completely
        self.setContentsMargins(0, 0, 0, 0)

        # State
        self._detail_messages: list[tuple[str, str, str]] = []
        self._max_detail_messages = 1000
        self._is_expanded = True
        self._current_operation = "Idle"

        # UI elements
        self._main_container: QWidget | None = None
        self._status_icon: QLabel | None = None
        self._operation_label: QLabel | None = None
        self._progress_bar: QProgressBar | None = None
        self._stats_container: QWidget | None = None
        self._toggle_button: QPushButton | None = None
        self._cancel_button: QPushButton | None = None
        self._detail_panel: QWidget | None = None
        self._detail_text: QTextEdit | None = None

        # Statistics labels
        self._total_label: QLabel | None = None
        self._new_label: QLabel | None = None
        self._modified_label: QLabel | None = None
        self._removed_label: QLabel | None = None
        self._rate_label: QLabel | None = None

        self._setup_ui()

        # Animation timer for pulsing effect during scan
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse_animation)

        # Start hidden until scan begins
        self.hide()

    def _setup_ui(self) -> None:
        """Set up the user interface with a modern design."""
        main_widget = QWidget()
        self.setWidget(main_widget)

        # Main vertical layout with minimal padding
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create the main container with border
        self._main_container = QFrame()
        self._main_container.setObjectName("scanProgressContainer")
        container_layout = QVBoxLayout(self._main_container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(12)

        # Top section: Status bar with progress
        status_bar = self._create_status_bar()
        container_layout.addWidget(status_bar)

        # Middle section: Statistics strip
        self._stats_container = self._create_stats_strip()
        container_layout.addWidget(self._stats_container)

        # Bottom section: Collapsible detail panel
        self._detail_panel = self._create_detail_panel()
        container_layout.addWidget(self._detail_panel)

        main_layout.addWidget(self._main_container)

        # Set initial size
        self.setMinimumHeight(120)
        self.setMaximumHeight(400)

        self._apply_theme()

    def _create_status_bar(self) -> QWidget:
        """Create the main status bar with operation info and progress."""
        status_widget = QWidget()
        status_widget.setObjectName("statusBar")
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Left: Status icon and operation text
        status_container = QHBoxLayout()
        status_container.setSpacing(8)

        # Animated status icon
        self._status_icon = QLabel("⚡")
        self._status_icon.setObjectName("statusIcon")
        self._status_icon.setFixedSize(24, 24)
        self._status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_container.addWidget(self._status_icon)

        # Operation label
        self._operation_label = QLabel("Ready to scan")
        self._operation_label.setObjectName("operationLabel")
        status_container.addWidget(self._operation_label)

        layout.addLayout(status_container)

        # Center: Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("scanProgressBar")
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFixedHeight(20)
        layout.addWidget(self._progress_bar, 1)

        # Right: Action buttons
        button_container = QHBoxLayout()
        button_container.setSpacing(8)

        # Toggle details button
        self._toggle_button = QPushButton()
        self._toggle_button.setObjectName("toggleButton")
        self._toggle_button.setFixedSize(32, 32)
        self._toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_button.clicked.connect(self._toggle_expanded)
        self._toggle_button.setToolTip("Show/Hide Details")
        button_container.addWidget(self._toggle_button)

        # Cancel button
        self._cancel_button = QPushButton()
        self._cancel_button.setObjectName("cancelButton")
        self._cancel_button.setFixedSize(32, 32)
        self._cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_button.setToolTip("Cancel Scan")
        self._cancel_button.setVisible(False)  # Hidden until scan starts
        button_container.addWidget(self._cancel_button)

        layout.addLayout(button_container)

        return status_widget

    def _create_stats_strip(self) -> QWidget:
        """Create the statistics strip showing scan results."""
        stats_widget = QWidget()
        stats_widget.setObjectName("statsStrip")
        layout = QHBoxLayout(stats_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # Create stat items
        stats = [
            ("Total", self._create_stat_item("Total", "0", "totalStat")),
            ("New", self._create_stat_item("New", "0", "newStat")),
            ("Modified", self._create_stat_item("Modified", "0", "modifiedStat")),
            ("Removed", self._create_stat_item("Removed", "0", "removedStat")),
            ("Rate", self._create_stat_item("Rate", "0/s", "rateStat")),
        ]

        for label, widget in stats:
            layout.addWidget(widget)
            if label == "Total":
                self._total_label = widget.findChild(QLabel, "value")
            elif label == "New":
                self._new_label = widget.findChild(QLabel, "value")
            elif label == "Modified":
                self._modified_label = widget.findChild(QLabel, "value")
            elif label == "Removed":
                self._removed_label = widget.findChild(QLabel, "value")
            elif label == "Rate":
                self._rate_label = widget.findChild(QLabel, "value")

        layout.addStretch()

        return stats_widget

    def _create_stat_item(self, label: str, value: str, object_name: str) -> QWidget:
        """Create a single statistics item."""
        item = QWidget()
        item.setObjectName(object_name)
        layout = QVBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("label")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)

        # Value
        value_widget = QLabel(value)
        value_widget.setObjectName("value")
        value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_widget)

        return item

    def _create_detail_panel(self) -> QWidget:
        """Create the collapsible detail panel."""
        panel = QWidget()
        panel.setObjectName("detailPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section header
        header = QLabel("Activity Log")
        header.setObjectName("detailHeader")
        layout.addWidget(header)

        # Log text area
        self._detail_text = QTextEdit()
        self._detail_text.setObjectName("detailText")
        self._detail_text.setReadOnly(True)
        self._detail_text.setMinimumHeight(100)
        self._detail_text.setMaximumHeight(200)
        layout.addWidget(self._detail_text)

        return panel

    def _pulse_animation(self) -> None:
        """Create a pulsing animation for the status icon during scanning."""
        if self._status_icon:
            # Simple rotation of different status characters
            current = self._status_icon.text()
            icons = ["⚡", "⚙️", "🔄", "📊"]
            try:
                idx = icons.index(current)
                self._status_icon.setText(icons[(idx + 1) % len(icons)])
            except ValueError:
                self._status_icon.setText(icons[0])

    def _toggle_expanded(self) -> None:
        """Toggle the expanded state of the detail panel."""
        self.set_expanded(not self._is_expanded)

    def set_expanded(self, expanded: bool) -> None:
        """Expand or collapse the detail panel."""
        if not self._detail_panel:
            return

        self._is_expanded = expanded

        if expanded:
            self._detail_panel.show()
            self.setMinimumHeight(250)
            self.setMaximumHeight(400)
        else:
            self._detail_panel.hide()
            self.setMinimumHeight(120)
            self.setMaximumHeight(120)

        self._update_toggle_button()

    def _update_toggle_button(self) -> None:
        """Update the toggle button icon based on expanded state."""
        if not self._toggle_button:
            return

        style = self.style()
        if style:
            icon = style.standardIcon(
                QStyle.StandardPixmap.SP_ArrowUp
                if self._is_expanded
                else QStyle.StandardPixmap.SP_ArrowDown
            )
            self._toggle_button.setIcon(icon)

    def start_scan(self, scan_type: str = "ROMs") -> None:
        """Start showing scan progress."""
        self.show()
        self.clear()

        self._current_operation = f"Scanning {scan_type}..."
        if self._operation_label:
            self._operation_label.setText(self._current_operation)

        if self._progress_bar:
            self._progress_bar.setMaximum(0)  # Indeterminate progress

        if self._cancel_button:
            self._cancel_button.setVisible(True)

        # Start pulsing animation
        self._pulse_timer.start(500)

        self.add_detail_message(f"Started {scan_type} scan", "info")

    def stop_scan(self) -> None:
        """Stop showing scan progress."""
        self._pulse_timer.stop()

        if self._status_icon:
            self._status_icon.setText("✅")

        if self._operation_label:
            self._operation_label.setText("Scan complete")

        if self._progress_bar:
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(100)

        if self._cancel_button:
            self._cancel_button.setVisible(False)

        self.add_detail_message("Scan completed successfully", "success")

    def clear(self) -> None:
        """Clear all progress information."""
        self._detail_messages.clear()

        if self._detail_text:
            self._detail_text.clear()

        if self._progress_bar:
            self._progress_bar.setValue(0)
            self._progress_bar.setMaximum(100)

        if self._operation_label:
            self._operation_label.setText("Ready to scan")

        if self._status_icon:
            self._status_icon.setText("⚡")

        self.update_scan_changes(0, 0, 0, 0)
        self.update_file_progress(0, 0)

        self.set_expanded(True)

    def update_scan_changes(self, new=None, modified=None, removed=None, existing=None) -> None:
        """Update scan change statistics."""
        if self._new_label and new is not None:
            self._new_label.setText(str(new))

        if self._modified_label and modified is not None:
            self._modified_label.setText(str(modified))

        if self._removed_label and removed is not None:
            self._removed_label.setText(str(removed))

        if self._total_label and all(x is not None for x in [new, modified, existing]):
            total = (new or 0) + (modified or 0) + (existing or 0)
            self._total_label.setText(str(total))

    def update_file_progress(self, current, total) -> None:
        """Update file processing progress."""
        if self._progress_bar and total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)
            percentage = (current / total) * 100
            self._progress_bar.setFormat(f"{current}/{total} ({percentage:.0f}%)")

        if self._operation_label:
            self._operation_label.setText(f"Processing: {current}/{total} files")

    def update_rom_count(self, count) -> None:
        """Update the number of ROMs found."""
        pass  # Integrated into total count

    def update_ra_matches(self, count) -> None:
        """Update RetroAchievements match count."""
        # Could add to detail messages
        if count > 0:
            self.add_detail_message(f"Found {count} RetroAchievements matches", "success")

    def add_detail_message(self, message, message_type="info") -> None:
        """Add a detailed message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._detail_messages.append((timestamp, message, message_type))

        if len(self._detail_messages) > self._max_detail_messages:
            self._detail_messages = self._detail_messages[-self._max_detail_messages :]

        self._refresh_detail_text()

    def _refresh_detail_text(self) -> None:
        """Refresh the detail text display."""
        if not self._detail_text:
            return

        theme = get_theme_manager().get_current_theme()
        if theme:
            colors = theme.colors
            color_map = {
                "info": colors.info,
                "success": colors.success,
                "warning": colors.warning,
                "error": colors.error,
            }
            timestamp_color = colors.text_secondary
        else:
            color_map = {
                "info": "#ffffff",
                "success": "#4CAF50",
                "warning": "#FFA726",
                "error": "#EF5350",
            }
            timestamp_color = "#888888"

        html_lines = []
        for timestamp, message, message_type in self._detail_messages:
            color = color_map.get(message_type.lower(), "#ffffff")
            html_lines.append(
                f'<span style="color: {timestamp_color}">[{timestamp}]</span> '
                f'<span style="color: {color}">{message}</span>'
            )

        self._detail_text.setHtml("<br>".join(html_lines))
        scrollbar = self._detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_completed(self) -> None:
        """Mark the scan as completed."""
        self.stop_scan()

    def apply_theme(self) -> None:
        """Public hook to refresh theme styling."""
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Apply the current theme to all UI elements."""
        theme = get_theme_manager().get_current_theme()

        if theme:
            colors = theme.colors
            text_color = colors.text
            secondary_text = colors.text_secondary
            surface_color = colors.surface
            border_color = colors.border
            success_color = colors.success
            warning_color = colors.warning
            error_color = colors.error
            primary_color = colors.primary
            hover_color = colors.hover
        else:
            text_color = "#e0e0e0"
            secondary_text = "#b0b0b0"
            surface_color = "#2b2b2b"
            border_color = "rgba(255, 255, 255, 0.1)"
            success_color = "#4CAF50"
            warning_color = "#FFA726"
            error_color = "#EF5350"
            primary_color = "#2196F3"
            hover_color = "rgba(255, 255, 255, 0.08)"

        # Main container with subtle border
        if self._main_container:
            self._main_container.setStyleSheet(f"""
                #scanProgressContainer {{
                    background-color: {surface_color};
                    border-top: 2px solid {border_color};
                }}
            """)

        # Status bar styling
        if self._status_icon:
            self._status_icon.setStyleSheet(f"""
                #statusIcon {{
                    background-color: {primary_color};
                    border-radius: 12px;
                    color: white;
                    font-size: 14px;
                }}
            """)

        if self._operation_label:
            self._operation_label.setStyleSheet(f"""
                #operationLabel {{
                    color: {text_color};
                    font-weight: 600;
                    font-size: 13px;
                }}
            """)

        # Modern progress bar
        if self._progress_bar:
            self._progress_bar.setStyleSheet(f"""
                #scanProgressBar {{
                    border: none;
                    border-radius: 10px;
                    background-color: rgba(255, 255, 255, 0.05);
                    text-align: center;
                    color: {text_color};
                    font-size: 11px;
                }}
                #scanProgressBar::chunk {{
                    border-radius: 10px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {primary_color},
                        stop:1 {success_color});
                }}
            """)

        # Action buttons
        button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {border_color};
                border-radius: 16px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border-color: {primary_color};
            }}
        """

        if self._toggle_button:
            self._toggle_button.setStyleSheet(button_style)

        if self._cancel_button:
            self._cancel_button.setStyleSheet(button_style)
            # Set cancel icon
            style = self.style()
            if style:
                self._cancel_button.setIcon(
                    style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
                )

        # Statistics styling
        if self._stats_container:
            # Style each stat item
            stat_items = self._stats_container.findChildren(QWidget)
            for item in stat_items:
                name = item.objectName()
                if name == "totalStat":
                    item.setStyleSheet(f"""
                        #totalStat #label {{
                            color: {secondary_text};
                            font-size: 10px;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }}
                        #totalStat #value {{
                            color: {text_color};
                            font-size: 18px;
                            font-weight: bold;
                        }}
                    """)
                elif name == "newStat":
                    item.setStyleSheet(f"""
                        #newStat #label {{
                            color: {secondary_text};
                            font-size: 10px;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }}
                        #newStat #value {{
                            color: {success_color};
                            font-size: 18px;
                            font-weight: bold;
                        }}
                    """)
                elif name == "modifiedStat":
                    item.setStyleSheet(f"""
                        #modifiedStat #label {{
                            color: {secondary_text};
                            font-size: 10px;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }}
                        #modifiedStat #value {{
                            color: {warning_color};
                            font-size: 18px;
                            font-weight: bold;
                        }}
                    """)
                elif name == "removedStat":
                    item.setStyleSheet(f"""
                        #removedStat #label {{
                            color: {secondary_text};
                            font-size: 10px;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }}
                        #removedStat #value {{
                            color: {error_color};
                            font-size: 18px;
                            font-weight: bold;
                        }}
                    """)
                elif name == "rateStat":
                    item.setStyleSheet(f"""
                        #rateStat #label {{
                            color: {secondary_text};
                            font-size: 10px;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }}
                        #rateStat #value {{
                            color: {primary_color};
                            font-size: 18px;
                            font-weight: bold;
                        }}
                    """)

        # Detail panel styling
        if self._detail_panel:
            header = self._detail_panel.findChild(QLabel, "detailHeader")
            if header:
                header.setStyleSheet(f"""
                    #detailHeader {{
                        color: {text_color};
                        font-weight: 600;
                        font-size: 12px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        padding: 8px 0px 4px 0px;
                        border-top: 1px solid {border_color};
                    }}
                """)

        if self._detail_text:
            self._detail_text.setStyleSheet(f"""
                #detailText {{
                    background-color: rgba(0, 0, 0, 0.2);
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                    padding: 8px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                }}
            """)

        self._update_toggle_button()

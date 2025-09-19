"""Dockable scan progress widget that appears below the main window."""

import logging
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
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

        # UI elements initialised in _setup_ui
        self._toggle_button: QPushButton | None = None
        self._content_frame: QFrame | None = None
        self._changes_label: QLabel | None = None
        self._progress_section_label: QLabel | None = None
        self._log_section_label: QLabel | None = None
        self._new_roms_label: QLabel | None = None
        self._modified_roms_label: QLabel | None = None
        self._removed_roms_label: QLabel | None = None
        self._existing_roms_label: QLabel | None = None
        self._files_label: QLabel | None = None
        self._roms_label: QLabel | None = None
        self._ra_label: QLabel | None = None
        self._detail_text: QTextEdit | None = None
        self._layout_margins = None
        self._expanded_min_height = 180
        self._expanded_max_height = 400

        self._setup_ui()

        # Start hidden until scan begins
        self.hide()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        main_widget = QWidget()
        self.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)
        self._layout_margins = layout.contentsMargins()

        # Create the main horizontal layout that stays visible
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Left side with toggle button that always stays visible
        left_container = QWidget()
        left_container.setMaximumWidth(250)
        left_container_layout = QVBoxLayout(left_container)
        left_container_layout.setContentsMargins(0, 0, 0, 0)
        left_container_layout.setSpacing(4)

        # Add toggle button at the top of the left column
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)

        self._toggle_button = QPushButton()
        self._toggle_button.setFlat(True)
        self._toggle_button.setFixedSize(24, 24)
        self._toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_button.clicked.connect(self._toggle_expanded)
        button_row.addWidget(self._toggle_button)

        button_label = QLabel("Scan Details")
        button_row.addWidget(button_label)
        button_row.addStretch()

        left_container_layout.addLayout(button_row)

        # Collapsible content frame for left statistics
        self._left_content_frame = QFrame()
        self._left_content_frame.setFrameStyle(QFrame.Shape.NoFrame)
        left_content_layout = QVBoxLayout(self._left_content_frame)
        left_content_layout.setContentsMargins(0, 8, 0, 0)
        left_content_layout.setSpacing(4)

        self._changes_label = QLabel("Changes:")
        left_content_layout.addWidget(self._changes_label)

        self._new_roms_label = QLabel("New: 0")
        left_content_layout.addWidget(self._new_roms_label)

        self._modified_roms_label = QLabel("Modified: 0")
        left_content_layout.addWidget(self._modified_roms_label)

        self._removed_roms_label = QLabel("Removed: 0")
        left_content_layout.addWidget(self._removed_roms_label)

        self._existing_roms_label = QLabel("Existing: 0")
        left_content_layout.addWidget(self._existing_roms_label)

        left_content_layout.addSpacing(20)

        self._progress_section_label = QLabel("Progress:")
        left_content_layout.addWidget(self._progress_section_label)

        self._files_label = QLabel("Files checked: 0/0")
        left_content_layout.addWidget(self._files_label)

        self._roms_label = QLabel("ROMs validated: 0")
        left_content_layout.addWidget(self._roms_label)

        self._ra_label = QLabel("RA matches: 0")
        left_content_layout.addWidget(self._ra_label)

        left_content_layout.addStretch()

        # Add the collapsible content to the left container
        left_container_layout.addWidget(self._left_content_frame)

        # Right panel - Detailed log
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(6)

        self._log_section_label = QLabel("Scan Log:")
        right_layout.addWidget(self._log_section_label)

        # Collapsible content frame for right panel
        self._right_content_frame = QFrame()
        self._right_content_frame.setFrameStyle(QFrame.Shape.NoFrame)
        right_content_layout = QVBoxLayout(self._right_content_frame)
        right_content_layout.setContentsMargins(0, 0, 0, 0)
        right_content_layout.setSpacing(0)

        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setViewportMargins(0, 0, 0, 0)
        self._detail_text.document().setDocumentMargin(8)
        right_content_layout.addWidget(self._detail_text)

        right_layout.addWidget(self._right_content_frame)

        # Add panels to main layout
        main_layout.addWidget(left_container)
        main_layout.addWidget(right_panel, 1)

        # Add the main layout to the dock
        layout.addLayout(main_layout)

        # Store content frame reference for compatibility
        self._content_frame = self._left_content_frame

        content_hint = (
            self._left_content_frame.sizeHint().height() if self._left_content_frame else 0
        )
        top_margin = self._layout_margins.top() if self._layout_margins else 0
        bottom_margin = self._layout_margins.bottom() if self._layout_margins else 0
        self._expanded_min_height = max(180, content_hint + top_margin + bottom_margin)
        self._expanded_max_height = max(self._expanded_max_height, self._expanded_min_height + 200)
        self.setMinimumHeight(self._expanded_min_height)
        self.setMaximumHeight(self._expanded_max_height)
        self._update_toggle_button_icon()
        self._apply_theme()

    def apply_theme(self) -> None:
        """Public hook to refresh theme styling."""
        self._apply_theme()

    def _apply_theme(self) -> None:
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
            info_color = colors.info
            hover_color = colors.hover
        else:
            # Fallback palette for when no theme is active
            text_color = "#e0e0e0"
            secondary_text = "#b0b0b0"
            surface_color = "#2b2b2b"
            border_color = "rgba(255, 255, 255, 0.1)"
            success_color = "#4CAF50"
            warning_color = "#FFA726"
            error_color = "#EF5350"
            info_color = "#ffffff"
            hover_color = "rgba(255, 255, 255, 0.08)"

        if self._changes_label:
            self._changes_label.setStyleSheet(f"font-weight: bold; color: {text_color};")
        if self._progress_section_label:
            self._progress_section_label.setStyleSheet(f"font-weight: bold; color: {text_color};")
        if self._log_section_label:
            self._log_section_label.setStyleSheet(f"font-weight: bold; color: {text_color};")

        if self._new_roms_label:
            self._new_roms_label.setStyleSheet(f"color: {success_color}; padding-left: 10px;")
        if self._modified_roms_label:
            self._modified_roms_label.setStyleSheet(f"color: {warning_color}; padding-left: 10px;")
        if self._removed_roms_label:
            self._removed_roms_label.setStyleSheet(f"color: {error_color}; padding-left: 10px;")
        if self._existing_roms_label:
            self._existing_roms_label.setStyleSheet(f"color: {secondary_text}; padding-left: 10px;")

        if self._files_label:
            self._files_label.setStyleSheet(f"color: {secondary_text}; padding-left: 10px;")
        if self._roms_label:
            self._roms_label.setStyleSheet(f"color: {secondary_text}; padding-left: 10px;")
        if self._ra_label:
            self._ra_label.setStyleSheet(f"color: {secondary_text}; padding-left: 10px;")

        if self._toggle_button:
            self._toggle_button.setStyleSheet(
                f"""
                QPushButton {{
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    background-color: transparent;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                """
            )

        if self._detail_text:
            self._detail_text.setStyleSheet(
                f"""
                QTextEdit {{
                    background-color: {surface_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 0;
                    font-family: inherit;
                    font-size: inherit;
                }}
                """
            )

        self._update_toggle_button_icon()
        self._refresh_detail_text(
            info_color, success_color, warning_color, error_color, secondary_text
        )

    def _update_toggle_button_icon(self) -> None:
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

        tooltip = "Collapse details" if self._is_expanded else "Expand details"
        self._toggle_button.setToolTip(tooltip)

    def _toggle_expanded(self) -> None:
        self.set_expanded(not self._is_expanded)

    def set_expanded(self, expanded: bool) -> None:
        """Expand or collapse the dock content."""
        if not self._left_content_frame or not self._right_content_frame:
            self._is_expanded = expanded
            self._update_toggle_button_icon()
            return

        if expanded:
            self._left_content_frame.show()
            self._right_content_frame.show()
            self.setMinimumHeight(self._expanded_min_height)
            self.setMaximumHeight(self._expanded_max_height)
        else:
            self._left_content_frame.hide()
            self._right_content_frame.hide()
            # When collapsed, keep button visible
            margins = self._layout_margins
            top_margin = margins.top() if margins else 0
            bottom_margin = margins.bottom() if margins else 0
            button_height = self._toggle_button.sizeHint().height() if self._toggle_button else 24
            label_height = (
                self._log_section_label.sizeHint().height() if self._log_section_label else 16
            )
            collapsed_height = top_margin + bottom_margin + max(button_height, label_height) + 8
            self.setMinimumHeight(collapsed_height)
            self.setMaximumHeight(collapsed_height)

        self._is_expanded = expanded
        self._update_toggle_button_icon()
        self.updateGeometry()

    def _refresh_detail_text(
        self,
        info_color: str,
        success_color: str,
        warning_color: str,
        error_color: str,
        timestamp_color: str,
    ) -> None:
        if not self._detail_text:
            return

        color_map = {
            "info": info_color,
            "success": success_color,
            "warning": warning_color,
            "error": error_color,
        }

        html_lines = []
        for timestamp, message, message_type in self._detail_messages:
            color = color_map.get(message_type.lower(), info_color)
            html_lines.append(
                f'<span style="color: {timestamp_color}">[{timestamp}]</span> '
                f'<span style="color: {color}">{message}</span>'
            )

        self._detail_text.setHtml("<br>".join(html_lines))
        scrollbar = self._detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self) -> None:
        """Clear all progress information."""
        self._detail_messages.clear()
        if self._detail_text:
            self._detail_text.clear()
        self.update_scan_changes(0, 0, 0, 0)
        self.update_file_progress(0, 0)
        self.update_rom_count(0)
        self.update_ra_matches(0)
        self.set_expanded(True)

    def update_scan_changes(self, new=None, modified=None, removed=None, existing=None) -> None:
        """Update scan change statistics."""
        if self._new_roms_label and new is not None:
            self._new_roms_label.setText(f"New: {new}")
        if self._modified_roms_label and modified is not None:
            self._modified_roms_label.setText(f"Modified: {modified}")
        if self._removed_roms_label and removed is not None:
            self._removed_roms_label.setText(f"Removed: {removed}")
        if self._existing_roms_label and existing is not None:
            self._existing_roms_label.setText(f"Existing: {existing}")

    def update_file_progress(self, current, total) -> None:
        """Update file processing progress."""
        if self._files_label:
            self._files_label.setText(f"Files checked: {current}/{total}")

    def update_rom_count(self, count) -> None:
        """Update the number of ROMs found."""
        if self._roms_label:
            self._roms_label.setText(f"ROMs validated: {count}")

    def update_ra_matches(self, count) -> None:
        """Update RetroAchievements match count."""
        if self._ra_label:
            self._ra_label.setText(f"RA matches: {count}")

    def add_detail_message(self, message, message_type="info") -> None:
        """Add a detailed message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._detail_messages.append((timestamp, message, message_type))

        if len(self._detail_messages) > self._max_detail_messages:
            self._detail_messages = self._detail_messages[-self._max_detail_messages :]

        theme = get_theme_manager().get_current_theme()
        if theme:
            colors = theme.colors
            self._refresh_detail_text(
                colors.info,
                colors.success,
                colors.warning,
                colors.error,
                colors.text_secondary,
            )
        else:
            self._refresh_detail_text(
                "#ffffff",
                "#4CAF50",
                "#FFA726",
                "#EF5350",
                "#888888",
            )

    def set_completed(self) -> None:
        """Mark the scan as completed."""
        self.add_detail_message("Scan completed", "success")

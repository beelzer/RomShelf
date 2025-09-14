"""Platforms settings page."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.settings import Settings
from ...platforms.platform_registry import PlatformRegistry
from ..themes.themed_widget import ThemeHelper
from .settings_base import SettingsPage, normalize_path_display


class PlatformsPage(SettingsPage):
    """Master platform directory management page."""

    def __init__(self, settings_manager=None, parent: QWidget | None = None) -> None:
        """Initialize the platforms page."""
        self._directory_table = None
        self._settings = None
        self._settings_manager = settings_manager
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Set up the master platform directory management UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Platform Directory Management")
        ThemeHelper.apply_header_style(header_label)
        layout.addWidget(header_label)

        description_label = QLabel(
            "Manage ROM directories for all platforms. Use 'Bulk Import' to automatically "
            "detect and assign platform directories from a parent folder."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        layout.addSpacing(10)

        # Buttons
        button_layout = QHBoxLayout()
        self._bulk_import_button = QPushButton("Bulk Import")
        self._bulk_import_button.setToolTip(
            "Select a parent directory to auto-detect platform subdirectories"
        )
        self._refresh_button = QPushButton("Refresh")

        button_layout.addWidget(self._bulk_import_button)
        button_layout.addWidget(self._refresh_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Directory table
        self._directory_table = QTableWidget()
        self._directory_table.setColumnCount(2)
        self._directory_table.setHorizontalHeaderLabels(["Platform", "ROM Directories"])

        # Configure table
        header = self._directory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self._directory_table.setAlternatingRowColors(True)
        self._directory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._directory_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Set up tooltips and interaction
        self._directory_table.setToolTip(
            "Right-click for options • Double-click directories to edit"
        )

        layout.addWidget(self._directory_table)

        # Connect signals
        self._bulk_import_button.clicked.connect(self._bulk_import_directories)
        self._refresh_button.clicked.connect(self._refresh_table)
        self._directory_table.customContextMenuRequested.connect(self._show_context_menu)
        self._directory_table.cellDoubleClicked.connect(self._on_cell_double_click)

        # Refresh table if settings are already loaded
        if self._settings is not None:
            self._refresh_table()

    def load_settings(self, settings: Settings) -> None:
        """Load settings and populate the directory table."""
        self._settings = settings
        if self._directory_table is not None:
            self._refresh_table()

    def save_settings(self, settings: Settings) -> None:
        """Save settings - updates are saved immediately through individual platform dialogs."""
        pass  # Settings are updated immediately when directories are modified

    def _refresh_table(self) -> None:
        """Refresh the directory table with current settings."""
        if not self._settings:
            return

        registry = PlatformRegistry()
        platforms = registry.get_all_platforms()

        self._directory_table.setRowCount(len(platforms))

        for row, platform in enumerate(platforms):
            # Platform name with icon/status
            platform_item = QTableWidgetItem(platform.name)
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            platform_item.setData(
                Qt.ItemDataRole.UserRole, platform.platform_id
            )  # Store platform ID
            self._directory_table.setItem(row, 0, platform_item)

            # ROM directories with better formatting
            platform_settings = self._settings.platform_settings.get(platform.platform_id, {})
            directories = platform_settings.get("rom_directories", [])

            if directories:
                # Show number of directories and first one as preview
                if len(directories) == 1:
                    dir_text = directories[0]
                else:
                    dir_text = f"{directories[0]} (+{len(directories)-1} more)"

                # Create tooltip with all directories
                tooltip = f"Configured directories ({len(directories)}):\n" + "\n".join(directories)
            else:
                dir_text = "No directories configured"
                tooltip = "Right-click or double-click to add directories"

            dir_item = QTableWidgetItem(dir_text)
            dir_item.setFlags(dir_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            dir_item.setToolTip(tooltip)
            dir_item.setData(Qt.ItemDataRole.UserRole, directories)  # Store directory list

            # Add visual styling for configured vs unconfigured
            if directories:
                # Green text for configured platforms
                dir_item.setForeground(QColor(0, 128, 0))
            else:
                # Gray italic text for unconfigured
                font = dir_item.font()
                font.setItalic(True)
                dir_item.setFont(font)
                dir_item.setForeground(QColor(128, 128, 128))

            self._directory_table.setItem(row, 1, dir_item)

        # Auto-resize rows to content
        self._directory_table.resizeRowsToContents()

    def _show_context_menu(self, position) -> None:
        """Show context menu for table operations."""

        item = self._directory_table.itemAt(position)
        if not item:
            return

        row = item.row()
        platform_item = self._directory_table.item(row, 0)
        platform_id = platform_item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        # Add directory action
        add_action = menu.addAction("Add Directory")
        add_action.triggered.connect(lambda: self._add_directory(platform_id))

        # Remove directory action (only if directories exist)
        directories = self._directory_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if directories:
            remove_action = menu.addAction("Remove Directory")
            remove_action.triggered.connect(lambda: self._remove_directory(platform_id))

            menu.addSeparator()
            clear_action = menu.addAction("Clear All Directories")
            clear_action.triggered.connect(lambda: self._clear_directories(platform_id))

        # Show menu at cursor position
        menu.exec(self._directory_table.mapToGlobal(position))

    def _on_cell_double_click(self, row: int, column: int) -> None:
        """Handle double-click on table cells."""
        platform_item = self._directory_table.item(row, 0)
        platform_id = platform_item.data(Qt.ItemDataRole.UserRole)

        if column == 1:  # Double-clicked on directories column
            directories = self._directory_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            if directories:
                self._edit_directories(platform_id, directories)
            else:
                self._add_directory(platform_id)

    def _edit_directories(self, platform_id: str, directories: list) -> None:
        """Edit the list of directories for a platform."""
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Directories")
        dialog.setModal(True)
        dialog.resize(500, 300)

        layout = QVBoxLayout(dialog)

        # Instructions
        label = QLabel(f"Directories for {self._get_platform_name(platform_id)}:")
        layout.addWidget(label)

        # Directory list
        dir_list = QListWidget()
        for directory in directories:
            dir_list.addItem(normalize_path_display(str(directory)))
        layout.addWidget(dir_list)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        def add_dir():
            directory = QFileDialog.getExistingDirectory(dialog, "Select ROM Directory")
            if directory:
                dir_list.addItem(normalize_path_display(directory))

        def remove_dir():
            current_row = dir_list.currentRow()
            if current_row >= 0:
                dir_list.takeItem(current_row)

        add_btn.clicked.connect(add_dir)
        remove_btn.clicked.connect(remove_dir)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Save changes if accepted
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_directories = []
            for i in range(dir_list.count()):
                new_directories.append(dir_list.item(i).text())

            # Update settings
            if platform_id not in self._settings.platform_settings:
                self._settings.platform_settings[platform_id] = {}
            self._settings.platform_settings[platform_id]["rom_directories"] = new_directories

            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _clear_directories(self, platform_id: str) -> None:
        """Clear all directories for a platform."""

        platform_name = self._get_platform_name(platform_id)
        reply = QMessageBox.question(
            self,
            "Clear Directories",
            f"Clear all ROM directories for {platform_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if platform_id in self._settings.platform_settings:
                self._settings.platform_settings[platform_id]["rom_directories"] = []
            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _get_platform_name(self, platform_id: str) -> str:
        """Get platform display name from ID."""
        registry = PlatformRegistry()
        platform = registry.get_platform(platform_id)
        return platform.name if platform else platform_id

    def _add_directory(self, platform_id: str) -> None:
        """Add a directory to the specified platform."""
        directory = QFileDialog.getExistingDirectory(self, "Select ROM Directory")
        if directory:
            # Update the platform settings
            if platform_id not in self._settings.platform_settings:
                self._settings.platform_settings[platform_id] = {}

            if "rom_directories" not in self._settings.platform_settings[platform_id]:
                self._settings.platform_settings[platform_id]["rom_directories"] = []

            self._settings.platform_settings[platform_id]["rom_directories"].append(directory)

            # Refresh table and emit change
            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _remove_directory(self, platform_id: str) -> None:
        """Remove directories from the specified platform."""
        platform_settings = self._settings.platform_settings.get(platform_id, {})
        directories = platform_settings.get("rom_directories", [])

        if not directories:
            return

        # Let user choose which directory to remove
        directory, ok = QInputDialog.getItem(
            self, "Remove Directory", "Select directory to remove:", directories, 0, False
        )

        if ok and directory:
            directories.remove(directory)
            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _bulk_import_directories(self) -> None:
        """Bulk import directories by scanning a parent folder and auto-assigning to platforms."""
        parent_dir = QFileDialog.getExistingDirectory(
            self, "Select Parent Directory Containing Platform Folders"
        )
        if not parent_dir:
            return

        # Scan for potential platform directories
        matches = self._detect_platform_directories(Path(parent_dir))

        if not matches:
            QMessageBox.information(
                self,
                "No Platform Directories Found",
                f"No subdirectories matching platform names were found in:\n{parent_dir}",
            )
            return

        # Show confirmation dialog and get selected directories
        selected_matches = self._confirm_bulk_import(matches)
        if selected_matches:
            # Apply the selected matches
            for platform_id, directories in selected_matches.items():
                if platform_id not in self._settings.platform_settings:
                    self._settings.platform_settings[platform_id] = {}

                if "rom_directories" not in self._settings.platform_settings[platform_id]:
                    self._settings.platform_settings[platform_id]["rom_directories"] = []

                # Add directories that aren't already present
                existing = self._settings.platform_settings[platform_id]["rom_directories"]
                for directory in directories:
                    if str(directory) not in existing:
                        existing.append(str(directory))

            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _detect_platform_directories(self, parent_dir: Path) -> dict[str, list[Path]]:
        """Detect potential platform directories and group by platform ID."""
        matches = {}
        registry = PlatformRegistry()
        platforms = registry.get_all_platforms()

        # Build platform name mapping with specific patterns
        platform_patterns = {}
        for platform in platforms:
            patterns = []

            # Add exact name and ID matches
            patterns.append(platform.name.lower())
            patterns.append(platform.platform_id.lower())

            # Map to exact directory names from user's ROM structure
            if platform.platform_id == "n64":
                patterns = ["nintendo 64"]
            elif platform.platform_id == "gameboy":
                patterns = ["nintendo game boy"]
            elif platform.platform_id == "gbc":
                patterns = ["nintendo game boy color"]
            elif platform.platform_id == "gba":
                patterns = ["nintendo game boy advance"]
            elif platform.platform_id == "snes":
                patterns = ["nintendo snes"]
            elif platform.platform_id == "psx":
                patterns = ["sony playstation"]

            platform_patterns[platform.platform_id] = patterns

        # Scan subdirectories with better matching
        try:
            for item in parent_dir.iterdir():
                if item.is_dir():
                    dir_name = item.name.lower()

                    # Try to find the best match (longest/most specific first)
                    best_match = None
                    best_match_length = 0

                    for platform_id, patterns in platform_patterns.items():
                        for pattern in patterns:
                            # Simple exact match only
                            if pattern == dir_name:
                                if len(pattern) > best_match_length:
                                    best_match = platform_id
                                    best_match_length = len(pattern)

                    if best_match:
                        if best_match not in matches:
                            matches[best_match] = []
                        matches[best_match].append(item)
        except (OSError, PermissionError):
            pass

        return matches

    def _confirm_bulk_import(self, matches: dict[str, list[Path]]) -> dict[str, list[Path]]:
        """Show confirmation dialog for bulk import matches. Returns selected matches."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Directories to Import")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Instructions
        label = QLabel(
            "Select which directories to import. Uncheck any directories you don't want to add:"
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        # Selection controls
        controls_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_none_btn = QPushButton("Select None")

        controls_layout.addWidget(select_all_btn)
        controls_layout.addWidget(select_none_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Table showing matches with checkboxes
        total_matches = sum(len(dirs) for dirs in matches.values())
        table = QTableWidget(total_matches, 3)
        table.setHorizontalHeaderLabels(["Import", "Platform", "Directory Path"])

        # Set row height to properly contain dropdown widgets
        table.verticalHeader().setDefaultSectionSize(35)

        # Configure table columns
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Checkbox column
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )  # Platform column - fixed width
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Path column
        header.resizeSection(1, 130)  # Set Platform column to 130px to accommodate dropdown

        # Populate table
        registry = PlatformRegistry()
        row = 0
        checkboxes = []
        platform_dropdowns = []
        row_data = []  # Store (original_platform_id, directory) for each row

        for platform_id, directories in matches.items():
            platform = registry.get_platform(platform_id)
            platform_name = platform.name if platform else platform_id

            for directory in directories:
                # Checkbox with centered container
                checkbox = QCheckBox()
                checkbox.setChecked(True)  # Default to checked
                # Fix checkbox styling in table cells
                checkbox.setStyleSheet("""
                    QCheckBox {
                        background: transparent;
                        padding: 5px;
                    }
                    QCheckBox::indicator {
                        width: 18px;
                        height: 18px;
                    }
                """)

                # Create a container widget to center the checkbox
                checkbox_container = QWidget()
                checkbox_container.setStyleSheet("background: transparent;")
                checkbox_layout = QHBoxLayout(checkbox_container)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.addStretch()
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.addStretch()

                table.setCellWidget(row, 0, checkbox_container)
                checkboxes.append(checkbox)

                # Platform dropdown
                platform_dropdown = QComboBox()
                # Remove all padding to make dropdown flush with cell edges
                platform_dropdown.setStyleSheet("""
                    QComboBox {
                        padding: 0px;
                        margin: 0px;
                        border: none;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox QAbstractItemView {
                        padding: 4px;
                        background-color: palette(base);
                        border: 1px solid palette(mid);
                        selection-background-color: palette(highlight);
                        selection-color: palette(highlighted-text);
                    }
                """)
                platform_dropdown.addItem("-- Select Platform --", "")
                all_platforms = registry.get_all_platforms()
                for p in all_platforms:
                    platform_dropdown.addItem(p.name, p.platform_id)

                # Set the suggested platform as default
                suggested_index = platform_dropdown.findData(platform_id)
                if suggested_index >= 0:
                    platform_dropdown.setCurrentIndex(suggested_index)

                # Prevent "-- Select Platform --" from being selected
                def on_selection_changed(index):
                    if (
                        platform_dropdown.itemData(index) == ""
                    ):  # Empty data means "-- Select Platform --"
                        # Revert to previous valid selection or first real platform
                        for i in range(1, platform_dropdown.count()):  # Skip index 0
                            if platform_dropdown.itemData(i) != "":
                                platform_dropdown.setCurrentIndex(i)
                                break

                platform_dropdown.currentIndexChanged.connect(on_selection_changed)

                # Create container to properly center the dropdown in the cell
                dropdown_container = QWidget()
                dropdown_container.setStyleSheet("background: transparent;")
                dropdown_layout = QHBoxLayout(dropdown_container)
                dropdown_layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
                dropdown_layout.addWidget(platform_dropdown)

                table.setCellWidget(row, 1, dropdown_container)
                # Make dropdown fit within cell
                platform_dropdown.setFixedWidth(
                    130
                )  # Full column width since container has no margins
                # Make the dropdown list wider when opened to show full names
                platform_dropdown.view().setMinimumWidth(250)
                platform_dropdowns.append(platform_dropdown)

                # Directory path
                table.setItem(row, 2, QTableWidgetItem(str(directory)))

                # Store data for later retrieval
                row_data.append((platform_id, directory))
                row += 1

        # Connect selection controls
        def select_all():
            for cb in checkboxes:
                cb.setChecked(True)

        def select_none():
            for cb in checkboxes:
                cb.setChecked(False)

        select_all_btn.clicked.connect(select_all)
        select_none_btn.clicked.connect(select_none)

        layout.addWidget(table)

        # Import summary
        summary_label = QLabel()

        def update_summary():
            selected_count = sum(1 for cb in checkboxes if cb.isChecked())
            summary_label.setText(f"Selected: {selected_count} of {total_matches} directories")

        # Update summary when checkboxes change
        for cb in checkboxes:
            cb.toggled.connect(update_summary)
        update_summary()  # Initial update

        layout.addWidget(summary_label)

        # Buttons
        button_layout = QHBoxLayout()
        import_button = QPushButton("Import Selected")
        cancel_button = QPushButton("Cancel")

        # Create a button container widget to center buttons properly
        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.addWidget(import_button)
        button_container_layout.addWidget(cancel_button)

        # Center the button container
        button_layout.addStretch()
        button_layout.addWidget(button_container)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Connect buttons
        import_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        # Show dialog and process results
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Build selected matches using dropdown selections
            selected_matches = {}
            for i, (original_platform_id, directory) in enumerate(row_data):
                if checkboxes[i].isChecked():
                    # Get the selected platform from dropdown
                    selected_platform_id = platform_dropdowns[i].currentData()
                    if selected_platform_id:  # Skip if no platform selected
                        if selected_platform_id not in selected_matches:
                            selected_matches[selected_platform_id] = []
                        selected_matches[selected_platform_id].append(directory)
            return selected_matches
        else:
            return {}  # User cancelled

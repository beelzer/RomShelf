"""Settings dialog with sidebar navigation."""

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.settings import PlatformSettings, Settings, SettingsManager
from ..platforms.base_platform import PlatformSetting, SettingType
from ..platforms.platform_registry import PlatformRegistry


def _normalize_path_display(path_str: str) -> str:
    """Normalize path for consistent display on Windows."""
    try:
        # Convert to Path and back to string to ensure consistent separators
        return str(Path(path_str).resolve())
    except (OSError, ValueError):
        # Fallback to original string if path normalization fails
        return path_str


class SettingsPage(QWidget):
    """Base class for settings pages."""

    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the settings page."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        pass

    def load_settings(self, settings: Settings) -> None:
        """Load settings into the page."""
        pass

    def save_settings(self, settings: Settings) -> None:
        """Save settings from the page."""
        pass


class InterfacePage(SettingsPage):
    """Interface settings page."""

    def _setup_ui(self) -> None:
        """Set up the interface settings UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)

        self._theme_group = QButtonGroup(self)
        self._light_radio = QRadioButton("Light")
        self._dark_radio = QRadioButton("Dark")

        self._theme_group.addButton(self._light_radio, 0)
        self._theme_group.addButton(self._dark_radio, 1)

        theme_controls = QHBoxLayout()
        theme_controls.addWidget(self._light_radio)
        theme_controls.addWidget(self._dark_radio)
        theme_controls.addStretch()

        theme_layout.addLayout(theme_controls)
        layout.addWidget(theme_group)

        # Font size
        font_group = QGroupBox("Font Size")
        font_layout = QVBoxLayout(font_group)

        font_controls = QHBoxLayout()
        self._font_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_slider.setRange(8, 14)
        self._font_slider.setValue(9)

        self._font_value_label = QLabel("9pt")
        self._font_value_label.setMinimumWidth(40)

        font_controls.addWidget(self._font_slider)
        font_controls.addWidget(self._font_value_label)

        font_layout.addLayout(font_controls)
        layout.addWidget(font_group)

        # Table row height
        row_height_group = QGroupBox("Table Row Height")
        row_height_layout = QVBoxLayout(row_height_group)

        row_height_controls = QHBoxLayout()
        self._row_height_slider = QSlider(Qt.Orientation.Horizontal)
        self._row_height_slider.setRange(18, 32)
        self._row_height_slider.setValue(24)

        self._row_height_value_label = QLabel("24px")
        self._row_height_value_label.setMinimumWidth(40)

        row_height_controls.addWidget(self._row_height_slider)
        row_height_controls.addWidget(self._row_height_value_label)

        row_height_layout.addLayout(row_height_controls)
        layout.addWidget(row_height_group)

        # Region preference
        region_group = QGroupBox("Preferred Region Priority")
        region_layout = QVBoxLayout(region_group)

        self._region_combo = QComboBox()
        self._region_combo.addItems(["USA", "Europe", "Japan", "World"])
        self._region_combo.setCurrentText("USA")
        region_layout.addWidget(self._region_combo)

        layout.addWidget(region_group)

        # Duplicate handling
        duplicate_group = QGroupBox("Duplicate Handling Strategy")
        duplicate_layout = QVBoxLayout(duplicate_group)

        self._duplicate_combo = QComboBox()
        self._duplicate_combo.addItem("Keep First Found", "keep_first")
        self._duplicate_combo.addItem("Keep All Duplicates", "keep_all")
        self._duplicate_combo.addItem("Prefer Region Priority", "prefer_region")
        self._duplicate_combo.setCurrentIndex(0)
        duplicate_layout.addWidget(self._duplicate_combo)

        layout.addWidget(duplicate_group)

        # Connect signals
        self._light_radio.toggled.connect(lambda: self.settings_changed.emit())
        self._dark_radio.toggled.connect(lambda: self.settings_changed.emit())
        self._font_slider.valueChanged.connect(lambda v: self._font_value_label.setText(f"{v}pt"))
        self._font_slider.valueChanged.connect(lambda: self.settings_changed.emit())
        self._row_height_slider.valueChanged.connect(lambda v: self._row_height_value_label.setText(f"{v}px"))
        self._row_height_slider.valueChanged.connect(lambda: self.settings_changed.emit())
        self._region_combo.currentTextChanged.connect(lambda: self.settings_changed.emit())
        self._duplicate_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())

    def load_settings(self, settings: Settings) -> None:
        """Load settings into the interface page."""
        if settings.theme == "light":
            self._light_radio.setChecked(True)
        else:
            self._dark_radio.setChecked(True)

        self._font_slider.setValue(settings.font_size)
        self._font_value_label.setText(f"{settings.font_size}pt")

        self._row_height_slider.setValue(settings.table_row_height)
        self._row_height_value_label.setText(f"{settings.table_row_height}px")

        self._region_combo.setCurrentText(settings.preferred_region)

        # Set duplicate handling combo
        for i in range(self._duplicate_combo.count()):
            if self._duplicate_combo.itemData(i) == settings.duplicate_handling:
                self._duplicate_combo.setCurrentIndex(i)
                break

    def save_settings(self, settings: Settings) -> None:
        """Save settings from the interface page."""
        # Check if widgets still exist before accessing them
        try:
            if hasattr(self, '_light_radio') and self._light_radio is not None:
                settings.theme = "light" if self._light_radio.isChecked() else "dark"
            if hasattr(self, '_font_slider') and self._font_slider is not None:
                settings.font_size = self._font_slider.value()
            if hasattr(self, '_row_height_slider') and self._row_height_slider is not None:
                settings.table_row_height = self._row_height_slider.value()
            if hasattr(self, '_region_combo') and self._region_combo is not None:
                settings.preferred_region = self._region_combo.currentText()
            if hasattr(self, '_duplicate_combo') and self._duplicate_combo is not None:
                current_data = self._duplicate_combo.currentData()
                if current_data:
                    settings.duplicate_handling = current_data
        except RuntimeError:
            # Widget was deleted, skip saving these values
            pass


class RetroAchievementsPage(SettingsPage):
    """RetroAchievements settings page."""

    def __init__(self, settings_manager=None, parent: QWidget | None = None) -> None:
        """Initialize the RetroAchievements page."""
        self._settings_manager = settings_manager
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Set up the RetroAchievements settings UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add header with description
        header_label = QLabel("RetroAchievements Integration")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(header_label)

        description_label = QLabel(
            "Configure your RetroAchievements credentials to enable precise hash-based ROM matching.\n"
            "This allows clicking the RA icon to open the exact achievement page for your ROM."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: gray; margin-bottom: 15px;")
        layout.addWidget(description_label)

        # API Credentials group
        credentials_group = QGroupBox("API Credentials")
        credentials_layout = QVBoxLayout(credentials_group)

        # Username field
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setMinimumWidth(100)
        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("Your RetroAchievements username")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self._username_edit)
        credentials_layout.addLayout(username_layout)

        # API Key field
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_label.setMinimumWidth(100)
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setPlaceholderText("Your RetroAchievements API key")
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self._api_key_edit)
        credentials_layout.addLayout(api_key_layout)

        # Show/Hide API key button
        show_hide_layout = QHBoxLayout()
        show_hide_layout.addStretch()
        self._show_api_key_btn = QPushButton("Show API Key")
        self._show_api_key_btn.setMaximumWidth(120)
        self._show_api_key_btn.clicked.connect(self._toggle_api_key_visibility)
        show_hide_layout.addWidget(self._show_api_key_btn)
        credentials_layout.addLayout(show_hide_layout)

        layout.addWidget(credentials_group)

        # Instructions group
        instructions_group = QGroupBox("How to Get API Credentials")
        instructions_layout = QVBoxLayout(instructions_group)

        instructions_text = QLabel(
            "1. Visit <a href='https://retroachievements.org/settings'>RetroAchievements Settings</a><br>"
            "2. Log in to your account<br>"
            "3. Look for the 'Authentication' section<br>"
            "4. Copy your 'Web API Key'<br>"
            "5. Enter your username and API key above"
        )
        instructions_text.setOpenExternalLinks(True)
        instructions_text.setWordWrap(True)
        instructions_layout.addWidget(instructions_text)

        layout.addWidget(instructions_group)

        # Test connection button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self._test_connection_btn = QPushButton("Test Connection")
        self._test_connection_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self._test_connection_btn)
        layout.addLayout(test_layout)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        # Connect change signals
        self._username_edit.textChanged.connect(lambda: self.settings_changed.emit())
        self._api_key_edit.textChanged.connect(lambda: self.settings_changed.emit())

    def _toggle_api_key_visibility(self) -> None:
        """Toggle API key field visibility."""
        if self._api_key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_api_key_btn.setText("Hide API Key")
        else:
            self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_api_key_btn.setText("Show API Key")

    def _test_connection(self) -> None:
        """Test the RetroAchievements API connection."""
        username = self._username_edit.text().strip()
        api_key = self._api_key_edit.text().strip()

        if not username or not api_key:
            self._status_label.setText("⚠️ Please enter both username and API key")
            self._status_label.setStyleSheet("color: orange;")
            return

        self._status_label.setText("🔄 Testing connection...")
        self._status_label.setStyleSheet("color: blue;")
        self._test_connection_btn.setEnabled(False)

        # Test the connection in a simple way
        try:
            import urllib.error
            import urllib.request
            from urllib.parse import urlencode

            params = urlencode({
                'z': username,
                'y': api_key,
                'i': 7,  # Nintendo 64 system
                'h': 1,
                'f': 1
            })

            url = f"https://retroachievements.org/API/API_GetGameList.php?{params}"
            request = urllib.request.Request(url, headers={'User-Agent': 'RomShelf/1.0'})

            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    self._status_label.setText("✅ Connection successful! Credentials are working.")
                    self._status_label.setStyleSheet("color: green;")
                else:
                    self._status_label.setText(f"❌ Connection failed with status code: {response.status}")
                    self._status_label.setStyleSheet("color: red;")

        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._status_label.setText("❌ Authentication failed. Please check your username and API key.")
            else:
                self._status_label.setText(f"❌ HTTP Error: {e.code}")
            self._status_label.setStyleSheet("color: red;")
        except Exception as e:
            self._status_label.setText(f"❌ Connection error: {e!s}")
            self._status_label.setStyleSheet("color: red;")

        self._test_connection_btn.setEnabled(True)

    def load_settings(self, settings: Settings) -> None:
        """Load settings into the page."""
        try:
            self._username_edit.setText(getattr(settings, 'retroachievements_username', ''))
            self._api_key_edit.setText(getattr(settings, 'retroachievements_api_key', ''))
        except RuntimeError:
            # Widget was deleted
            pass

    def save_settings(self, settings: Settings) -> None:
        """Save settings from the page."""
        try:
            settings.retroachievements_username = self._username_edit.text().strip()
            settings.retroachievements_api_key = self._api_key_edit.text().strip()
        except RuntimeError:
            # Widget was deleted
            pass


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
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
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
        self._bulk_import_button.setToolTip("Select a parent directory to auto-detect platform subdirectories")
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
        self._directory_table.setToolTip("Right-click for options • Double-click directories to edit")

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

        from ..platforms.platform_registry import PlatformRegistry
        registry = PlatformRegistry()
        platforms = registry.get_all_platforms()

        self._directory_table.setRowCount(len(platforms))

        for row, platform in enumerate(platforms):
            # Platform name with icon/status
            platform_item = QTableWidgetItem(platform.name)
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            platform_item.setData(Qt.ItemDataRole.UserRole, platform.platform_id)  # Store platform ID
            self._directory_table.setItem(row, 0, platform_item)

            # ROM directories with better formatting
            platform_settings = self._settings.platform_settings.get(platform.platform_id, {})
            directories = platform_settings.get('rom_directories', [])

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
        from PySide6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QPushButton, QVBoxLayout

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Directories")
        dialog.setModal(True)
        dialog.resize(500, 300)

        layout = QVBoxLayout(dialog)

        # Instructions
        from PySide6.QtWidgets import QLabel
        label = QLabel(f"Directories for {self._get_platform_name(platform_id)}:")
        layout.addWidget(label)

        # Directory list
        dir_list = QListWidget()
        for directory in directories:
            dir_list.addItem(_normalize_path_display(str(directory)))
        layout.addWidget(dir_list)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        def add_dir():
            from PySide6.QtWidgets import QFileDialog
            directory = QFileDialog.getExistingDirectory(dialog, "Select ROM Directory")
            if directory:
                dir_list.addItem(_normalize_path_display(directory))

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
            self._settings.platform_settings[platform_id]['rom_directories'] = new_directories

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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if platform_id in self._settings.platform_settings:
                self._settings.platform_settings[platform_id]['rom_directories'] = []
            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _get_platform_name(self, platform_id: str) -> str:
        """Get platform display name from ID."""
        from ..platforms.platform_registry import PlatformRegistry
        registry = PlatformRegistry()
        platform = registry.get_platform(platform_id)
        return platform.name if platform else platform_id

    def _add_directory(self, platform_id: str) -> None:
        """Add a directory to the specified platform."""
        from PySide6.QtWidgets import QFileDialog

        directory = QFileDialog.getExistingDirectory(self, "Select ROM Directory")
        if directory:
            # Update the platform settings
            if platform_id not in self._settings.platform_settings:
                self._settings.platform_settings[platform_id] = {}

            if 'rom_directories' not in self._settings.platform_settings[platform_id]:
                self._settings.platform_settings[platform_id]['rom_directories'] = []

            self._settings.platform_settings[platform_id]['rom_directories'].append(directory)

            # Refresh table and emit change
            self._refresh_table()
            self.settings_changed.emit()
            # Save settings immediately
            if self._settings_manager:
                self._settings_manager.save()

    def _remove_directory(self, platform_id: str) -> None:
        """Remove directories from the specified platform."""
        platform_settings = self._settings.platform_settings.get(platform_id, {})
        directories = platform_settings.get('rom_directories', [])

        if not directories:
            return

        from PySide6.QtWidgets import QInputDialog

        # Let user choose which directory to remove
        directory, ok = QInputDialog.getItem(
            self,
            "Remove Directory",
            "Select directory to remove:",
            directories,
            0,
            False
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
        from PySide6.QtWidgets import QFileDialog

        parent_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Parent Directory Containing Platform Folders"
        )
        if not parent_dir:
            return

        # Scan for potential platform directories
        matches = self._detect_platform_directories(Path(parent_dir))

        if not matches:
            QMessageBox.information(
                self,
                "No Platform Directories Found",
                f"No subdirectories matching platform names were found in:\n{parent_dir}"
            )
            return

        # Show confirmation dialog and get selected directories
        selected_matches = self._confirm_bulk_import(matches)
        if selected_matches:
            # Apply the selected matches
            for platform_id, directories in selected_matches.items():
                if platform_id not in self._settings.platform_settings:
                    self._settings.platform_settings[platform_id] = {}

                if 'rom_directories' not in self._settings.platform_settings[platform_id]:
                    self._settings.platform_settings[platform_id]['rom_directories'] = []

                # Add directories that aren't already present
                existing = self._settings.platform_settings[platform_id]['rom_directories']
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
        from ..platforms.platform_registry import PlatformRegistry

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
            if platform.platform_id == 'n64':
                patterns = ['nintendo 64']
            elif platform.platform_id == 'gameboy':
                patterns = ['nintendo game boy']
            elif platform.platform_id == 'gbc':
                patterns = ['nintendo game boy color']
            elif platform.platform_id == 'gba':
                patterns = ['nintendo game boy advance']
            elif platform.platform_id == 'snes':
                patterns = ['nintendo snes']
            elif platform.platform_id == 'psx':
                patterns = ['sony playstation']

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
        from PySide6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDialog,
            QHBoxLayout,
            QHeaderView,
            QLabel,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QWidget,
        )

        from ..platforms.platform_registry import PlatformRegistry

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Directories to Import")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Instructions
        label = QLabel("Select which directories to import. Uncheck any directories you don't want to add:")
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Platform column - fixed width
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
                # Make dropdown fill the entire cell width
                # We'll set this after adding to the table to get the actual cell width
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
                    if platform_dropdown.itemData(index) == "":  # Empty data means "-- Select Platform --"
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
                platform_dropdown.setFixedWidth(130)  # Full column width since container has no margins
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


class PlatformSpecificPage(SettingsPage):
    """Platform-specific settings page with dynamic UI generation."""

    def __init__(self, platform_id: str, platform_name: str, parent: QWidget | None = None) -> None:
        """Initialize the platform-specific page."""
        self._platform_id = platform_id
        self._platform_name = platform_name
        self._setting_widgets: dict[str, Any] = {}  # Maps setting key to widget
        super().__init__(parent)

    def _setup_ui(self) -> None:
        """Set up the platform-specific settings UI dynamically."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        header = QLabel(f"{self._platform_name} Settings")
        layout.addWidget(header)

        # Get platform-specific settings
        try:
            registry = PlatformRegistry()
            platform = registry.get_platform(self._platform_id)
            if platform:
                platform_settings = platform.get_platform_settings()
                self._create_settings_ui(layout, platform_settings)
            else:
                error_label = QLabel(f"Platform '{self._platform_id}' not found.")
                error_label.setStyleSheet("color: red;")
                layout.addWidget(error_label)
        except Exception as e:
            error_label = QLabel(f"Error loading platform settings: {e}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)

    def _create_settings_ui(self, layout: QVBoxLayout, platform_settings: list[PlatformSetting]) -> None:
        """Create UI elements for platform settings."""
        # Group settings by type
        format_settings = []
        other_settings = []

        for setting in platform_settings:
            if setting.setting_type == SettingType.FORMAT_LIST:
                format_settings.append(setting)
            else:
                other_settings.append(setting)

        # Create format support section
        if format_settings:
            formats_group = QGroupBox("Format Support")
            formats_layout = QVBoxLayout(formats_group)

            for setting in format_settings:
                setting_widget = self._create_setting_section(setting)
                formats_layout.addWidget(setting_widget)

            layout.addWidget(formats_group)

        # Create other settings section
        if other_settings:
            other_group = QGroupBox("Configuration")
            other_layout = QVBoxLayout(other_group)
            other_layout.setContentsMargins(12, 8, 12, 8)
            other_layout.setSpacing(4)

            for setting in other_settings:
                if setting.setting_type == SettingType.DIRECTORY_LIST:
                    # Special compact layout for directory lists
                    self._create_compact_directory_section(other_layout, setting)
                else:
                    # Regular inline settings
                    setting_widget = self._create_setting_section(setting)
                    other_layout.addWidget(setting_widget)

            layout.addWidget(other_group)

    def _create_setting_section(self, setting: PlatformSetting) -> QWidget:
        """Create a section for any setting."""
        section = QWidget()
        layout = QHBoxLayout(section)
        # Use tighter vertical margins for directory lists, normal for others
        if setting.setting_type == SettingType.DIRECTORY_LIST:
            layout.setContentsMargins(8, 3, 8, 3)
        else:
            layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # Setting label with fixed width for alignment
        label = QLabel(setting.label)
        label.setMinimumWidth(180)
        label.setMaximumWidth(180)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Add description as tooltip
        if setting.description:
            label.setToolTip(setting.description)

        layout.addWidget(label)

        # Control widget
        widget = self._create_setting_widget(setting)
        if widget:
            self._setting_widgets[setting.key] = widget
            # Also add description as tooltip to the control widget
            if setting.description:
                widget.setToolTip(setting.description)
            layout.addWidget(widget)

        # Add stretch to fill remaining space
        layout.addStretch()

        return section

    def _create_setting_widget(self, setting: PlatformSetting) -> QWidget | None:
        """Create appropriate widget for a setting based on its type."""
        if setting.setting_type == SettingType.BOOLEAN:
            checkbox = QCheckBox()
            checkbox.setChecked(setting.default_value)
            checkbox.toggled.connect(lambda: self.settings_changed.emit())

            return checkbox

        elif setting.setting_type == SettingType.INTEGER:
            spinbox = QSpinBox()
            if setting.min_value is not None:
                spinbox.setMinimum(int(setting.min_value))
            if setting.max_value is not None:
                spinbox.setMaximum(int(setting.max_value))
            spinbox.setValue(setting.default_value)
            spinbox.valueChanged.connect(lambda: self.settings_changed.emit())
            return spinbox

        elif setting.setting_type == SettingType.FLOAT:
            spinbox = QDoubleSpinBox()
            if setting.min_value is not None:
                spinbox.setMinimum(float(setting.min_value))
            if setting.max_value is not None:
                spinbox.setMaximum(float(setting.max_value))
            spinbox.setValue(float(setting.default_value))
            spinbox.valueChanged.connect(lambda: self.settings_changed.emit())
            return spinbox

        elif setting.setting_type == SettingType.STRING:
            line_edit = QLineEdit()
            line_edit.setText(str(setting.default_value))
            line_edit.textChanged.connect(lambda: self.settings_changed.emit())
            return line_edit

        elif setting.setting_type == SettingType.CHOICE:
            combo_box = QComboBox()
            if setting.choices:
                combo_box.addItems(setting.choices)
                if setting.default_value in setting.choices:
                    combo_box.setCurrentText(setting.default_value)
            combo_box.currentTextChanged.connect(lambda: self.settings_changed.emit())

            return combo_box

        elif setting.setting_type in [SettingType.FILE_PATH, SettingType.DIRECTORY_PATH]:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)

            line_edit = QLineEdit()
            line_edit.setText(str(setting.default_value))
            line_edit.textChanged.connect(lambda: self.settings_changed.emit())

            browse_button = QPushButton("Browse...")

            def browse():
                if setting.setting_type == SettingType.FILE_PATH:
                    path, _ = QFileDialog.getOpenFileName(self, f"Select {setting.label}")
                else:
                    path = QFileDialog.getExistingDirectory(self, f"Select {setting.label}")
                if path:
                    line_edit.setText(path)

            browse_button.clicked.connect(browse)

            layout.addWidget(line_edit)
            layout.addWidget(browse_button)

            # Store line_edit as the main widget for value retrieval
            widget._value_widget = line_edit
            return widget

        elif setting.setting_type == SettingType.DIRECTORY_LIST:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(3)

            # List widget to show directories (more compact)
            dirs_list = QListWidget()
            dirs_list.setMaximumHeight(75)
            dirs_list.setMinimumHeight(45)

            # Add default directories if any
            if isinstance(setting.default_value, list):
                for directory in setting.default_value:
                    dirs_list.addItem(_normalize_path_display(str(directory)))

            # Button layout (more compact)
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(3)

            add_button = QPushButton("Add")
            add_button.setMaximumWidth(60)
            add_button.setMaximumHeight(24)
            bulk_import_button = QPushButton("Bulk Import")
            bulk_import_button.setMaximumWidth(100)
            bulk_import_button.setMaximumHeight(24)
            remove_button = QPushButton("Remove")
            remove_button.setMaximumWidth(80)
            remove_button.setMaximumHeight(24)

            def add_directory():
                directory = QFileDialog.getExistingDirectory(self, f"Select {setting.label}")
                if directory:
                    dirs_list.addItem(_normalize_path_display(directory))
                    self.settings_changed.emit()

            def remove_directory():
                current_row = dirs_list.currentRow()
                if current_row >= 0:
                    dirs_list.takeItem(current_row)
                    self.settings_changed.emit()

            def bulk_import():
                self._bulk_import_directories(dirs_list)

            add_button.clicked.connect(add_directory)
            bulk_import_button.clicked.connect(bulk_import)
            remove_button.clicked.connect(remove_directory)

            button_layout.addWidget(add_button)
            button_layout.addWidget(bulk_import_button)
            button_layout.addWidget(remove_button)
            button_layout.addStretch()

            layout.addWidget(dirs_list)
            layout.addLayout(button_layout)

            # Store dirs_list as the main widget for value retrieval
            widget._dirs_list = dirs_list
            return widget

        elif setting.setting_type == SettingType.FORMAT_LIST:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)

            # Create checkboxes for each format option
            checkboxes = {}
            if setting.choices:
                for format_ext in setting.choices:
                    checkbox = QCheckBox(format_ext.upper())
                    checkbox.setChecked(format_ext in setting.default_value)
                    checkbox.toggled.connect(lambda: self.settings_changed.emit())
                    layout.addWidget(checkbox)
                    checkboxes[format_ext] = checkbox

            # Store checkboxes for value retrieval
            widget._format_checkboxes = checkboxes
            return widget

        return None

    def _create_compact_directory_section(self, parent_layout: QVBoxLayout, setting: PlatformSetting) -> None:
        """Create a compact directory list section directly in the parent layout."""
        # Label
        label = QLabel(setting.label)
        if setting.description:
            label.setToolTip(setting.description)
        parent_layout.addWidget(label)

        # Directory list widget - very compact
        dirs_list = QListWidget()
        dirs_list.setMaximumHeight(60)
        dirs_list.setMinimumHeight(40)

        # Add default directories if any
        if isinstance(setting.default_value, list):
            for directory in setting.default_value:
                dirs_list.addItem(_normalize_path_display(str(directory)))

        parent_layout.addWidget(dirs_list)

        # Buttons in a horizontal layout - very compact
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)

        add_button = QPushButton("Add")
        add_button.setMaximumSize(60, 24)
        bulk_import_button = QPushButton("Bulk Import")
        bulk_import_button.setMaximumSize(100, 24)
        remove_button = QPushButton("Remove")
        remove_button.setMaximumSize(80, 24)

        def add_directory():
            directory = QFileDialog.getExistingDirectory(self, f"Select {setting.label}")
            if directory:
                dirs_list.addItem(_normalize_path_display(directory))
                self.settings_changed.emit()

        def remove_directory():
            current_row = dirs_list.currentRow()
            if current_row >= 0:
                dirs_list.takeItem(current_row)
                self.settings_changed.emit()

        def bulk_import():
            self._bulk_import_directories(dirs_list)

        add_button.clicked.connect(add_directory)
        bulk_import_button.clicked.connect(bulk_import)
        remove_button.clicked.connect(remove_directory)

        button_layout.addWidget(add_button)
        button_layout.addWidget(bulk_import_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()

        parent_layout.addWidget(button_container)

        # Store the list widget for value retrieval
        self._setting_widgets[setting.key] = dirs_list

    def load_settings(self, settings: Settings) -> None:
        """Load settings into the platform-specific page."""
        # Get platform settings (could be None if not set yet)
        platform_data = settings.platform_settings.get(self._platform_id, {})

        # If platform_data is a PlatformSettings object, convert to dict
        if isinstance(platform_data, PlatformSettings):
            platform_data = {
                'supports_archives': platform_data.supports_archives,
                'supports_multi_part': platform_data.supports_multi_part,
                'supports_normal': platform_data.supports_normal,
            }

        # Load values into widgets
        for setting_key, widget in self._setting_widgets.items():
            try:
                if setting_key in platform_data:
                    value = platform_data[setting_key]
                else:
                    # Use default from platform definition
                    registry = PlatformRegistry()
                    platform = registry.get_platform(self._platform_id)
                    if platform:
                        platform_settings = platform.get_platform_settings()
                        for setting in platform_settings:
                            if setting.key == setting_key:
                                value = setting.default_value
                                break
                        else:
                            continue
                    else:
                        continue

                # Set widget value based on type
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif hasattr(widget, '_value_widget'):  # File/directory picker
                    widget._value_widget.setText(str(value))
                elif hasattr(widget, '_dirs_list'):  # Directory list (old style)
                    # Value should be a list of directories
                    dirs_list = widget._dirs_list
                    dirs_list.clear()
                    if isinstance(value, list):
                        for directory in value:
                            dirs_list.addItem(_normalize_path_display(str(directory)))
                elif isinstance(widget, QListWidget):  # Directory list (compact style)
                    # Value should be a list of directories
                    widget.clear()
                    if isinstance(value, list):
                        for directory in value:
                            widget.addItem(_normalize_path_display(str(directory)))
                elif hasattr(widget, '_format_checkboxes'):  # Format list
                    # Value should be a list of enabled formats
                    enabled_formats = value if isinstance(value, list) else []
                    for format_ext, checkbox in widget._format_checkboxes.items():
                        checkbox.setChecked(format_ext in enabled_formats)

            except Exception as e:
                print(f"Error loading setting {setting_key}: {e}")

    def save_settings(self, settings: Settings) -> None:
        """Save settings from the platform-specific page."""
        try:
            platform_data = {}

            # Collect values from all widgets
            for setting_key, widget in self._setting_widgets.items():
                try:
                    if isinstance(widget, QCheckBox):
                        platform_data[setting_key] = widget.isChecked()
                    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                        platform_data[setting_key] = widget.value()
                    elif isinstance(widget, QLineEdit):
                        platform_data[setting_key] = widget.text()
                    elif isinstance(widget, QComboBox):
                        platform_data[setting_key] = widget.currentText()
                    elif hasattr(widget, '_value_widget'):  # File/directory picker
                        platform_data[setting_key] = widget._value_widget.text()
                    elif hasattr(widget, '_dirs_list'):  # Directory list (old style)
                        # Collect directories into a list
                        directories = []
                        dirs_list = widget._dirs_list
                        for i in range(dirs_list.count()):
                            directories.append(dirs_list.item(i).text())
                        platform_data[setting_key] = directories
                    elif isinstance(widget, QListWidget):  # Directory list (compact style)
                        # Collect directories into a list
                        directories = []
                        for i in range(widget.count()):
                            directories.append(widget.item(i).text())
                        platform_data[setting_key] = directories
                    elif hasattr(widget, '_format_checkboxes'):  # Format list
                        # Collect enabled formats into a list
                        enabled_formats = []
                        for format_ext, checkbox in widget._format_checkboxes.items():
                            if checkbox.isChecked():
                                enabled_formats.append(format_ext)
                        platform_data[setting_key] = enabled_formats
                except Exception as e:
                    print(f"Error saving setting {setting_key}: {e}")

            # Merge with existing platform settings to preserve rom_directories and other settings
            if self._platform_id not in settings.platform_settings:
                settings.platform_settings[self._platform_id] = {}

            # Preserve critical settings that this page doesn't manage
            existing_settings = settings.platform_settings[self._platform_id].copy()

            # Explicitly preserve rom_directories (managed by PlatformsPage)
            rom_directories = existing_settings.get('rom_directories', [])

            # Update with new settings from this page
            existing_settings.update(platform_data)

            # Ensure rom_directories is preserved
            existing_settings['rom_directories'] = rom_directories

            settings.platform_settings[self._platform_id] = existing_settings

        except RuntimeError:
            # Widget was deleted, skip saving these values
            pass

    def _bulk_import_directories(self, dirs_list: QListWidget) -> None:
        """Bulk import platform directories by scanning a parent folder."""
        from pathlib import Path

        from PySide6.QtWidgets import QFileDialog

        # Select parent directory
        parent_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Parent Directory Containing Platform Folders"
        )
        if not parent_dir:
            return

        # Scan for potential platform directories
        matches = self._detect_platform_directories(Path(parent_dir))

        if not matches:
            QMessageBox.information(
                self,
                "No Platform Directories Found",
                f"No subdirectories matching platform names were found in:\n{parent_dir}"
            )
            return

        # Show confirmation dialog
        if self._confirm_platform_matches(matches):
            # Add confirmed directories to the list
            for platform_name, directory in matches:
                dirs_list.addItem(_normalize_path_display(str(directory)))
            self.settings_changed.emit()

    def _detect_platform_directories(self, parent_dir: Path) -> list[tuple[str, Path]]:
        """Detect potential platform directories in parent folder."""
        from ..platforms.platform_registry import platform_registry

        matches = []
        platforms = platform_registry.get_all_platforms()

        # Build platform name mapping with specific patterns
        platform_patterns = {}
        for platform in platforms:
            patterns = []

            # Add exact name and ID matches
            patterns.append(platform.name.lower())
            patterns.append(platform.platform_id.lower())

            # Map to exact directory names from user's ROM structure
            if platform.platform_id == 'n64':
                patterns = ['nintendo 64']
            elif platform.platform_id == 'gameboy':
                patterns = ['nintendo game boy']
            elif platform.platform_id == 'gbc':
                patterns = ['nintendo game boy color']
            elif platform.platform_id == 'gba':
                patterns = ['nintendo game boy advance']
            elif platform.platform_id == 'snes':
                patterns = ['nintendo snes']
            elif platform.platform_id == 'psx':
                patterns = ['sony playstation']

            platform_patterns[platform.platform_id] = (platform.name, patterns)

        # Scan subdirectories with better matching
        try:
            for item in parent_dir.iterdir():
                if item.is_dir():
                    dir_name = item.name.lower()

                    # Try to find the best match (longest/most specific first)
                    best_match = None
                    best_match_name = None
                    best_match_length = 0

                    for platform_id, (platform_name, patterns) in platform_patterns.items():
                        for pattern in patterns:
                            # Simple exact match only
                            if pattern == dir_name:
                                if len(pattern) > best_match_length:
                                    best_match = platform_id
                                    best_match_name = platform_name
                                    best_match_length = len(pattern)

                    if best_match:
                        matches.append((best_match_name, item))
        except (OSError, PermissionError):
            pass

        return matches

    def _confirm_platform_matches(self, matches: list[tuple[str, Path]]) -> bool:
        """Show confirmation dialog for detected platform matches."""
        from PySide6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QHeaderView,
            QLabel,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm Platform Directory Matches")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Instructions
        label = QLabel("The following platform directories were detected. Please review and confirm:")
        label.setWordWrap(True)
        layout.addWidget(label)

        # Table showing matches
        table = QTableWidget(len(matches), 2)
        table.setHorizontalHeaderLabels(["Platform", "Directory Path"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i, (platform_name, directory) in enumerate(matches):
            table.setItem(i, 0, QTableWidgetItem(platform_name))
            table.setItem(i, 1, QTableWidgetItem(str(directory)))

        layout.addWidget(table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("Import All")
        cancel_button = QPushButton("Cancel")

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Connect buttons
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        return dialog.exec() == QDialog.DialogCode.Accepted


class SettingsDialog(QDialog):
    """Settings dialog with sidebar navigation."""

    # Signal emitted when settings are applied
    settings_applied = Signal()

    def __init__(self, settings_manager: SettingsManager, parent: QWidget | None = None) -> None:
        """Initialize the settings dialog."""
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._pages: dict[str, Any] = {}
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Main splitter
        splitter = QSplitter()
        layout.addWidget(splitter)

        # Left sidebar - Category tree
        self._category_tree = QTreeWidget()
        self._category_tree.setFixedWidth(200)
        self._category_tree.setHeaderHidden(True)
        self._category_tree.setRootIsDecorated(False)
        self._category_tree.currentItemChanged.connect(self._on_category_changed)

        # Add categories
        interface_item = QTreeWidgetItem(["Interface"])
        interface_item.setData(0, Qt.ItemDataRole.UserRole, "Interface")
        self._category_tree.addTopLevelItem(interface_item)

        # RetroAchievements category
        retroachievements_item = QTreeWidgetItem(["RetroAchievements"])
        retroachievements_item.setData(0, Qt.ItemDataRole.UserRole, "RetroAchievements")
        self._category_tree.addTopLevelItem(retroachievements_item)

        # Platforms with expandable sub-items
        platforms_item = QTreeWidgetItem(["Platforms"])
        platforms_item.setData(0, Qt.ItemDataRole.UserRole, "Platforms")
        self._category_tree.addTopLevelItem(platforms_item)

        # Add individual platforms as children
        registry = PlatformRegistry()
        platforms = registry.get_all_platforms()

        for platform in platforms:
            platform_item = QTreeWidgetItem([platform.name])
            platform_item.setData(0, Qt.ItemDataRole.UserRole, f"Platform:{platform.platform_id}")
            platforms_item.addChild(platform_item)

        # Expand platforms by default and select Interface
        platforms_item.setExpanded(True)
        self._category_tree.setCurrentItem(interface_item)

        splitter.addWidget(self._category_tree)

        # Right content area with stacked widget wrapped in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create a stacked widget to hold all pages
        self._stacked_widget = QStackedWidget()
        scroll_area.setWidget(self._stacked_widget)

        # Create base pages and add them to stacked widget
        self._pages["Interface"] = InterfacePage(self._stacked_widget)
        self._pages["RetroAchievements"] = RetroAchievementsPage(self._settings_manager, self._stacked_widget)
        self._pages["Platforms"] = PlatformsPage(self._settings_manager, self._stacked_widget)

        self._stacked_widget.addWidget(self._pages["Interface"])
        self._stacked_widget.addWidget(self._pages["RetroAchievements"])
        self._stacked_widget.addWidget(self._pages["Platforms"])

        # Create all platform-specific pages and add them to stacked widget
        for platform in platforms:
            page_key = f"Platform:{platform.platform_id}"
            platform_page = PlatformSpecificPage(platform.platform_id, platform.name, self._stacked_widget)
            self._pages[page_key] = platform_page
            self._stacked_widget.addWidget(platform_page)

        # Connect settings changed signals for all pages
        for page in self._pages.values():
            page.settings_changed.connect(self._on_settings_changed)

        # Set initial page
        self._stacked_widget.setCurrentWidget(self._pages["Interface"])
        self._current_page = self._pages["Interface"]

        splitter.addWidget(scroll_area)
        splitter.setSizes([200, 400])

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._ok_button = QPushButton("OK")
        self._cancel_button = QPushButton("Cancel")
        self._apply_button = QPushButton("Apply")

        self._ok_button.clicked.connect(self._on_ok_clicked)
        self._cancel_button.clicked.connect(self.reject)
        self._apply_button.clicked.connect(self._on_apply_clicked)
        self._apply_button.setEnabled(False)

        button_layout.addWidget(self._ok_button)
        button_layout.addWidget(self._cancel_button)
        button_layout.addWidget(self._apply_button)

        layout.addLayout(button_layout)

        self._scroll_area = scroll_area
        self._has_changes = False

    def _on_category_changed(self, current_item, previous_item) -> None:
        """Handle category selection changes."""
        if current_item is None:
            return

        page_key = current_item.data(0, Qt.ItemDataRole.UserRole)

        if page_key in self._pages:
            page = self._pages[page_key]
            self._stacked_widget.setCurrentWidget(page)
            self._current_page = page


    def _on_settings_changed(self) -> None:
        """Handle settings changes."""
        self._has_changes = True
        self._apply_button.setEnabled(True)

    def _on_ok_clicked(self) -> None:
        """Handle OK button click."""
        if self._has_changes:
            self._apply_settings()
        self.accept()

    def _on_apply_clicked(self) -> None:
        """Handle Apply button click."""
        self._apply_settings()
        self._has_changes = False
        self._apply_button.setEnabled(False)
        # Emit signal to notify parent that settings were applied
        self.settings_applied.emit()

    def _load_settings(self) -> None:
        """Load current settings into all pages."""
        settings = self._settings_manager.settings
        for page in self._pages.values():
            page.load_settings(settings)

    def _apply_settings(self) -> None:
        """Apply settings from all pages."""
        settings = self._settings_manager.settings
        for page in self._pages.values():
            page.save_settings(settings)
        self._settings_manager.save()

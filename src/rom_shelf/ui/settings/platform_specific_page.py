"""Platform-specific settings page with dynamic UI generation."""

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.settings import Settings
from ...platforms.base_platform import PlatformSetting, SettingType
from ...platforms.platform_registry import PlatformRegistry, platform_registry
from .settings_base import SettingsPage, normalize_path_display
from ..themes.themed_widget import ThemeHelper


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
                ThemeHelper.apply_status_style(error_label, "error")
                layout.addWidget(error_label)
        except Exception as e:
            error_label = QLabel(f"Error loading platform settings: {e}")
            ThemeHelper.apply_status_style(error_label, "error")
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
                    dirs_list.addItem(normalize_path_display(str(directory)))

            # Button layout (more compact)
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(3)

            add_button = QPushButton("Add")
            ThemeHelper.auto_size_button(add_button)
            bulk_import_button = QPushButton("Bulk Import")
            ThemeHelper.auto_size_button(bulk_import_button)
            remove_button = QPushButton("Remove")
            ThemeHelper.auto_size_button(remove_button)

            def add_directory():
                directory = QFileDialog.getExistingDirectory(self, f"Select {setting.label}")
                if directory:
                    dirs_list.addItem(normalize_path_display(directory))
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
                dirs_list.addItem(normalize_path_display(str(directory)))

        parent_layout.addWidget(dirs_list)

        # Buttons in a horizontal layout - very compact
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)

        add_button = QPushButton("Add")
        ThemeHelper.auto_size_button(add_button)
        bulk_import_button = QPushButton("Bulk Import")
        ThemeHelper.auto_size_button(bulk_import_button)
        remove_button = QPushButton("Remove")
        ThemeHelper.auto_size_button(remove_button)

        def add_directory():
            directory = QFileDialog.getExistingDirectory(self, f"Select {setting.label}")
            if directory:
                dirs_list.addItem(normalize_path_display(directory))
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
        if hasattr(platform_data, '__dict__'):
            platform_data = {
                'supports_archives': getattr(platform_data, 'supports_archives', True),
                'supports_multi_part': getattr(platform_data, 'supports_multi_part', True),
                'supports_normal': getattr(platform_data, 'supports_normal', True),
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
                            dirs_list.addItem(normalize_path_display(str(directory)))
                elif isinstance(widget, QListWidget):  # Directory list (compact style)
                    # Value should be a list of directories
                    widget.clear()
                    if isinstance(value, list):
                        for directory in value:
                            widget.addItem(normalize_path_display(str(directory)))
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
                dirs_list.addItem(normalize_path_display(str(directory)))
            self.settings_changed.emit()

    def _detect_platform_directories(self, parent_dir: Path) -> list[tuple[str, Path]]:
        """Detect potential platform directories in parent folder."""
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
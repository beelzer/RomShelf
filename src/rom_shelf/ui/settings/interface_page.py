"""Interface settings page."""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QVBoxLayout,
)

from ...core.settings import Settings
from ...utils.flag_icons import FlagIcons
from .settings_base import SettingsPage


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
        self._region_combo.setIconSize(QSize(20, 15))  # Set icon size for flags

        # Add region items with flag icons
        regions = ["USA", "Europe", "Japan", "World"]
        for region in regions:
            flag_icon = FlagIcons.get_flag_icon(region, QSize(20, 15))
            if flag_icon:
                self._region_combo.addItem(flag_icon, region)
            else:
                self._region_combo.addItem(region)

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
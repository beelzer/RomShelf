"""Demonstration page showcasing themed form controls."""

from __future__ import annotations

from PySide6.QtCore import QDate, QDateTime, Qt, QTime
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..themes import get_theme_manager
from .settings_base import Settings, SettingsPage, ThemeHelper


class FormDemoPage(SettingsPage):
    """Settings page that demonstrates themed form and input widgets."""

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(16)

        header = QLabel("Form and Input Showcase")
        ThemeHelper.apply_header_style(header, size=16)
        layout.addWidget(header)

        description = QLabel(
            "Interactive controls rendered with the current theme. "
            "Includes enabled, focused-ready, and disabled variations for quick visual checks."
        )
        description.setWordWrap(True)
        ThemeHelper.apply_description_style(description)
        layout.addWidget(description)

        layout.addWidget(self._build_text_inputs_section())
        layout.addWidget(self._build_selection_section())
        layout.addWidget(self._build_numeric_section())
        layout.addWidget(self._build_dates_section())
        layout.addWidget(self._build_buttons_section())
        layout.addWidget(self._build_multiline_section())
        layout.addWidget(self._build_progress_section())
        layout.addStretch()

    def load_settings(self, settings: Settings) -> None:
        """Override to satisfy the interface; demo page does not load settings."""

    def save_settings(self, settings: Settings) -> None:
        """Override to satisfy the interface; demo page does not persist settings."""

    def _build_group_box(self, title: str) -> QGroupBox:
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(12)
        box_layout.setContentsMargins(12, 12, 12, 12)
        return box

    def _build_text_inputs_section(self) -> QGroupBox:
        box = self._build_group_box("Text Inputs")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        standard = QLineEdit()
        standard.setPlaceholderText("Placeholder text")
        form.addRow("Standard", standard)

        password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        password.setText("secret")
        form.addRow("Password", password)

        search = QLineEdit()
        search.setClearButtonEnabled(True)
        search.setPlaceholderText("Search")
        form.addRow("Search", search)

        readonly = QLineEdit("Read-only value")
        readonly.setReadOnly(True)
        form.addRow("Read-only", readonly)

        disabled = QLineEdit("Disabled")
        disabled.setEnabled(False)
        form.addRow("Disabled", disabled)

        error = QLineEdit("Invalid value")
        palette = get_theme_manager().get_palette()
        error.setStyleSheet(f"border: 1px solid {palette.error};")
        form.addRow("Error highlight", error)

        box.layout().addLayout(form)
        return box

    def _build_selection_section(self) -> QGroupBox:
        box = self._build_group_box("Selection Controls")

        combo_row = QWidget()
        combo_layout = QFormLayout(combo_row)
        combo_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        combo = QComboBox()
        combo.addItems(["Option A", "Option B", "Option C"])
        combo_layout.addRow("ComboBox", combo)

        editable_combo = QComboBox()
        editable_combo.setEditable(True)
        editable_combo.addItems(["Editable", "Choice 1", "Choice 2"])
        combo_layout.addRow("Editable", editable_combo)

        disabled_combo = QComboBox()
        disabled_combo.addItems(["Unavailable"])
        disabled_combo.setEnabled(False)
        combo_layout.addRow("Disabled", disabled_combo)

        box.layout().addWidget(combo_row)

        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(12)

        unchecked = QCheckBox("Unchecked")
        checked = QCheckBox("Checked")
        checked.setChecked(True)
        mixed = QCheckBox("Partially checked")
        mixed.setTristate(True)
        mixed.setCheckState(Qt.CheckState.PartiallyChecked)
        disabled_check = QCheckBox("Disabled")
        disabled_check.setEnabled(False)
        disabled_check.setChecked(True)

        checkbox_layout.addWidget(unchecked)
        checkbox_layout.addWidget(checked)
        checkbox_layout.addWidget(mixed)
        checkbox_layout.addWidget(disabled_check)
        checkbox_layout.addStretch()

        box.layout().addWidget(checkbox_container)

        radio_container = QWidget()
        radio_layout = QHBoxLayout(radio_container)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(12)

        radio_group = QButtonGroup(self)
        radio_default = QRadioButton("Default")
        radio_selected = QRadioButton("Selected")
        radio_selected.setChecked(True)
        radio_disabled = QRadioButton("Disabled")
        radio_disabled.setEnabled(False)

        radio_group.addButton(radio_default)
        radio_group.addButton(radio_selected)
        radio_group.addButton(radio_disabled)

        radio_layout.addWidget(radio_default)
        radio_layout.addWidget(radio_selected)
        radio_layout.addWidget(radio_disabled)
        radio_layout.addStretch()

        box.layout().addWidget(radio_container)
        return box

    def _build_numeric_section(self) -> QGroupBox:
        box = self._build_group_box("Numeric Inputs")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setValue(42)
        form.addRow("SpinBox", spin)

        double_spin = QDoubleSpinBox()
        double_spin.setDecimals(2)
        double_spin.setRange(-10.0, 10.0)
        double_spin.setValue(3.14)
        form.addRow("DoubleSpin", double_spin)

        slider_row = QWidget()
        slider_layout = QHBoxLayout(slider_row)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(8)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(65)

        slider_disabled = QSlider(Qt.Orientation.Horizontal)
        slider_disabled.setRange(0, 100)
        slider_disabled.setValue(20)
        slider_disabled.setEnabled(False)

        slider_layout.addWidget(slider)
        slider_layout.addWidget(slider_disabled)
        form.addRow("Sliders", slider_row)

        dial_row = QWidget()
        dial_layout = QHBoxLayout(dial_row)
        dial_layout.setContentsMargins(0, 0, 0, 0)
        dial_layout.setSpacing(8)

        dial = QDial()
        dial.setValue(30)
        dial_disabled = QDial()
        dial_disabled.setValue(70)
        dial_disabled.setEnabled(False)

        dial_layout.addWidget(dial)
        dial_layout.addWidget(dial_disabled)
        form.addRow("Dials", dial_row)

        box.layout().addLayout(form)
        return box

    def _build_dates_section(self) -> QGroupBox:
        box = self._build_group_box("Date & Time")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        date_edit = QDateEdit(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        form.addRow("Date", date_edit)

        time_edit = QTimeEdit(QTime.currentTime())
        form.addRow("Time", time_edit)

        date_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        date_time_edit.setCalendarPopup(True)
        form.addRow("DateTime", date_time_edit)

        disabled_date = QDateEdit(QDate(1995, 9, 12))
        disabled_date.setEnabled(False)
        form.addRow("Disabled", disabled_date)

        box.layout().addLayout(form)
        return box

    def _build_buttons_section(self) -> QGroupBox:
        box = self._build_group_box("Buttons & Tooling")
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        primary = QPushButton("Primary")
        primary.setDefault(True)

        secondary = QPushButton("Secondary")

        destructive = QPushButton("Destructive")
        palette = get_theme_manager().get_palette()
        destructive.setStyleSheet(
            f"""
            QPushButton {{
                border: 1px solid {palette.error};
                color: {palette.error};
            }}
            QPushButton:hover {{
                background-color: {palette.hover};
            }}
            """
        )

        disabled_btn = QPushButton("Disabled")
        disabled_btn.setEnabled(False)

        tool_button = QToolButton()
        tool_button.setText("Tool")

        row_layout.addWidget(primary)
        row_layout.addWidget(secondary)
        row_layout.addWidget(destructive)
        row_layout.addWidget(disabled_btn)
        row_layout.addWidget(tool_button)
        row_layout.addStretch()

        box.layout().addWidget(row)
        return box

    def _build_multiline_section(self) -> QGroupBox:
        box = self._build_group_box("Multiline & Lists")
        layout = box.layout()

        plain_text = QPlainTextEdit("Plain text area\nLine two")
        plain_text.setFixedHeight(80)
        layout.addWidget(plain_text)

        rich_text = QTextEdit()
        rich_text.setHtml(
            "<b>Rich text</b> with <i>formatting</i> and <span style='color:#ff6b35;'>color</span>."
        )
        rich_text.setFixedHeight(100)
        layout.addWidget(rich_text)

        list_widget = QListWidget()
        list_widget.addItem("First item")
        selected_item = QListWidgetItem("Selected item")
        list_widget.addItem(selected_item)
        list_widget.setCurrentItem(selected_item)
        disabled_item = QListWidgetItem("Disabled item")
        disabled_item.setFlags(Qt.ItemFlags())
        list_widget.addItem(disabled_item)
        layout.addWidget(list_widget)

        return box

    def _build_progress_section(self) -> QGroupBox:
        box = self._build_group_box("Progress & Status")
        layout = box.layout()

        determinate = QProgressBar()
        determinate.setValue(65)
        layout.addWidget(determinate)

        indeterminate = QProgressBar()
        indeterminate.setRange(0, 0)
        layout.addWidget(indeterminate)

        return box

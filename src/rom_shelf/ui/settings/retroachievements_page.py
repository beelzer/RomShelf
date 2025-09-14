"""RetroAchievements settings page."""

import urllib.error
import urllib.request
from urllib.parse import urlencode

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.settings import Settings
from ..themes.themed_widget import ThemeHelper
from .settings_base import SettingsPage


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
        ThemeHelper.apply_header_style(header_label)
        layout.addWidget(header_label)

        description_label = QLabel(
            "Configure your RetroAchievements credentials to enable precise hash-based ROM matching.\n"
            "This allows clicking the RA icon to open the exact achievement page for your ROM."
        )
        description_label.setWordWrap(True)
        ThemeHelper.apply_description_style(description_label)
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
            ThemeHelper.apply_status_style(self._status_label, "warning")
            return

        self._status_label.setText("🔄 Testing connection...")
        ThemeHelper.apply_status_style(self._status_label, "info")
        self._test_connection_btn.setEnabled(False)

        # Test the connection in a simple way
        try:
            params = urlencode(
                {
                    "z": username,
                    "y": api_key,
                    "i": 7,  # Nintendo 64 system
                    "h": 1,
                    "f": 1,
                }
            )

            url = f"https://retroachievements.org/API/API_GetGameList.php?{params}"
            request = urllib.request.Request(url, headers={"User-Agent": "RomShelf/1.0"})

            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    self._status_label.setText("✅ Connection successful! Credentials are working.")
                    ThemeHelper.apply_status_style(self._status_label, "success")
                else:
                    self._status_label.setText(
                        f"❌ Connection failed with status code: {response.status}"
                    )
                    ThemeHelper.apply_status_style(self._status_label, "error")

        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._status_label.setText(
                    "❌ Authentication failed. Please check your username and API key."
                )
            else:
                self._status_label.setText(f"❌ HTTP Error: {e.code}")
            ThemeHelper.apply_status_style(self._status_label, "error")
        except Exception as e:
            self._status_label.setText(f"❌ Connection error: {e!s}")
            ThemeHelper.apply_status_style(self._status_label, "error")

        self._test_connection_btn.setEnabled(True)

    def load_settings(self, settings: Settings) -> None:
        """Load settings into the page."""
        try:
            self._username_edit.setText(getattr(settings, "retroachievements_username", ""))
            self._api_key_edit.setText(getattr(settings, "retroachievements_api_key", ""))
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

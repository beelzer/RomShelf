"""Main application entry point."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .core.settings import SettingsManager
from .ui.main import MainWindow


def main() -> int:
    """Main application function."""
    app = QApplication(sys.argv)
    app.setApplicationName("ROM Shelf")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ROM Shelf")

    # Initialize settings
    settings_path = Path("data") / "settings.json"
    settings_manager = SettingsManager(settings_path)

    # Create and show main window
    window = MainWindow(settings_manager)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

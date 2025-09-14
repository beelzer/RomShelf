"""Main application entry point."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .core.settings import SettingsManager
from .services import ServiceContainer
from .ui.main import MainWindow


def main() -> int:
    """Main application function."""
    app = QApplication(sys.argv)
    app.setApplicationName("ROM Shelf")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ROM Shelf")

    # Initialize settings and service container
    settings_path = Path("data") / "settings.json"
    settings_manager = SettingsManager(settings_path)
    service_container = ServiceContainer(settings_manager)

    # Create and show main window with services
    window = MainWindow(service_container)
    window.show()

    # Run application
    result = app.exec()

    # Cleanup services
    service_container.cleanup()

    return result


if __name__ == "__main__":
    sys.exit(main())

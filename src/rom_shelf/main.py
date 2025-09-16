"""Main application entry point."""

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .core.logging_config import setup_logging
from .core.settings import SettingsManager
from .services import ServiceContainer
from .ui.main import MainWindow


def main() -> int:
    """Main application function."""
    # Initialize logging first
    logging_config = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting RomShelf application")

    app = QApplication(sys.argv)
    app.setApplicationName("ROM Shelf")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ROM Shelf")

    # Initialize settings and service container
    try:
        settings_path = Path("data") / "settings.json"
        settings_manager = SettingsManager(settings_path)
        service_container = ServiceContainer(settings_manager)
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

    # Create and show main window with services
    try:
        window = MainWindow(service_container)
        window.show()
        logger.info("Main window displayed")
    except Exception as e:
        logger.error(f"Failed to create main window: {e}", exc_info=True)
        raise

    # Run application
    result = app.exec()

    # Cleanup services
    try:
        service_container.cleanup()
        logger.info("Services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)

    logger.info("Application shutting down")
    return result


if __name__ == "__main__":
    sys.exit(main())

"""Centralized logging configuration for RomShelf."""

import logging
import logging.handlers
import os
import sys
from enum import Enum
from pathlib import Path


class Environment(Enum):
    """Application environment modes."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"
    DEBUG = "debug"


class LoggingConfig:
    """Manages application-wide logging configuration."""

    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"

    def __init__(self, log_dir: Path | None = None):
        """Initialize logging configuration.

        Args:
            log_dir: Directory for log files. If None, uses default location.
        """
        self.environment = self._detect_environment()
        self.log_dir = log_dir or self._get_default_log_dir()
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Store original stderr for critical errors
        self._original_stderr = sys.stderr

    def _detect_environment(self) -> Environment:
        """Detect the current environment from environment variables or defaults.

        Returns:
            The detected environment.
        """
        env_var = os.environ.get("ROMSHELF_ENV", "").lower()

        if env_var == "test" or "pytest" in sys.modules:
            return Environment.TEST
        elif env_var == "debug" or os.environ.get("ROMSHELF_DEBUG", "").lower() == "true":
            return Environment.DEBUG
        elif env_var == "production":
            return Environment.PRODUCTION
        else:
            # Default to development
            return Environment.DEVELOPMENT

    def _get_default_log_dir(self) -> Path:
        """Get the default log directory based on the operating system.

        Returns:
            Path to the log directory.
        """
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\RomShelf\logs
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        elif sys.platform == "darwin":
            # macOS: ~/Library/Logs/RomShelf
            base = Path.home() / "Library" / "Logs"
        else:
            # Linux: ~/.local/share/RomShelf/logs
            base = Path.home() / ".local" / "share"

        return base / "RomShelf" / "logs"

    def setup_logging(self) -> None:
        """Configure logging for the entire application."""
        # Clear any existing handlers
        root = logging.getLogger()
        root.handlers = []

        # Set base level based on environment
        if self.environment == Environment.DEBUG:
            root.setLevel(logging.DEBUG)
            log_format = self.DETAILED_FORMAT
        elif self.environment == Environment.TEST:
            root.setLevel(logging.WARNING)
            log_format = self.DEFAULT_FORMAT
        elif self.environment == Environment.PRODUCTION:
            root.setLevel(logging.INFO)
            log_format = self.DEFAULT_FORMAT
        else:  # DEVELOPMENT
            root.setLevel(logging.DEBUG)
            log_format = self.DETAILED_FORMAT

        # Console handler (always present)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))

        # Adjust console output based on environment
        if self.environment == Environment.PRODUCTION:
            console_handler.setLevel(logging.WARNING)
        elif self.environment == Environment.TEST:
            console_handler.setLevel(logging.ERROR)
        else:
            console_handler.setLevel(logging.INFO)

        root.addHandler(console_handler)

        # File handlers (not in test environment)
        if self.environment != Environment.TEST:
            # Main log file with rotation
            main_log_file = self.log_dir / "romshelf.log"
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(logging.Formatter(self.DETAILED_FORMAT))
            file_handler.setLevel(logging.DEBUG)
            root.addHandler(file_handler)

            # Error log file
            error_log_file = self.log_dir / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8",
            )
            error_handler.setFormatter(logging.Formatter(self.DETAILED_FORMAT))
            error_handler.setLevel(logging.ERROR)
            root.addHandler(error_handler)

        # Log initial configuration
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured for environment: {self.environment.value}")
        logger.info(f"Log directory: {self.log_dir}")
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Platform: {sys.platform}")

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the given name.

        Args:
            name: The name for the logger (typically __name__).

        Returns:
            A configured logger instance.
        """
        return logging.getLogger(name)

    def configure_external_libraries(self) -> None:
        """Configure logging levels for external libraries."""
        # Reduce noise from external libraries
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

        # Qt/PySide6 logging
        if self.environment != Environment.DEBUG:
            logging.getLogger("PySide6").setLevel(logging.WARNING)

    def cleanup(self) -> None:
        """Clean up old log files."""
        if self.environment == Environment.TEST:
            return

        try:
            # Keep only the last 30 days of logs
            import time

            current_time = time.time()
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < current_time - (30 * 24 * 60 * 60):
                    log_file.unlink()
        except Exception as e:
            # Don't fail if cleanup fails
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to clean up old logs: {e}")


# Global instance
_config: LoggingConfig | None = None


def setup_logging(log_dir: Path | None = None) -> LoggingConfig:
    """Initialize and configure application logging.

    Args:
        log_dir: Optional custom log directory.

    Returns:
        The logging configuration instance.
    """
    global _config
    if _config is None:
        _config = LoggingConfig(log_dir)
        _config.setup_logging()
        _config.configure_external_libraries()
        _config.cleanup()
    return _config


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: The logger name (typically __name__).

    Returns:
        A configured logger instance.
    """
    if _config is None:
        setup_logging()
    return logging.getLogger(name)


def get_environment() -> Environment:
    """Get the current environment.

    Returns:
        The current environment mode.
    """
    if _config is None:
        setup_logging()
    return _config.environment

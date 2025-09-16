"""Configuration validation and environment management for RomShelf."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class PlatformConfig(BaseModel):
    """Platform-specific configuration."""

    name: str
    enabled: bool = True
    rom_extensions: list[str] = Field(default_factory=list)
    rom_paths: list[str] = Field(default_factory=list)
    emulator_path: str | None = None

    @field_validator("rom_extensions")
    def validate_extensions(self, v: list[str]) -> list[str]:
        """Ensure extensions start with a dot."""
        return [ext if ext.startswith(".") else f".{ext}" for ext in v]

    @field_validator("rom_paths")
    def validate_paths(self, v: list[str]) -> list[str]:
        """Validate that ROM paths exist."""
        valid_paths = []
        for path_str in v:
            path = Path(path_str)
            if path.exists():
                valid_paths.append(str(path.absolute()))
            else:
                logger = logging.getLogger(__name__)
                logger.warning(f"ROM path does not exist: {path_str}")
        return valid_paths


class DatabaseConfig(BaseModel):
    """Database configuration."""

    path: str = Field(default="romshelf.db")
    version: int = Field(default=1, ge=1)
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(default=3600, ge=60)
    connection_timeout: float = Field(default=5.0, ge=1.0)
    max_connections: int = Field(default=10, ge=1, le=100)
    wal_mode: bool = True  # Write-Ahead Logging for better concurrency

    @field_validator("path")
    def validate_db_path(self, v: str) -> str:
        """Ensure database path is writable."""
        db_path = Path(v)
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_path.absolute())


class ScannerConfig(BaseModel):
    """Scanner configuration."""

    num_workers: int = Field(default=4, ge=1, le=32)
    batch_size: int = Field(default=100, ge=10, le=1000)
    skip_hidden: bool = True
    follow_symlinks: bool = False
    max_file_size_mb: int = Field(default=500, ge=1)
    archive_extraction_timeout: int = Field(default=30, ge=5)
    stream_archive_threshold_mb: int = Field(default=100, ge=10)
    temp_dir: str | None = None

    @field_validator("temp_dir")
    def validate_temp_dir(self, v: str | None) -> str | None:
        """Validate temp directory if provided."""
        if v:
            temp_path = Path(v)
            if not temp_path.exists():
                temp_path.mkdir(parents=True, exist_ok=True)
            if not temp_path.is_dir() or not os.access(temp_path, os.W_OK):
                raise ValueError(f"Temp directory is not writable: {v}")
            return str(temp_path.absolute())
        return v


class UIConfig(BaseModel):
    """UI configuration."""

    theme: str = Field(default="dark")
    language: str = Field(default="en")
    show_splash_screen: bool = True
    remember_window_position: bool = True
    default_view: str = Field(default="grid")
    items_per_page: int = Field(default=50, ge=10, le=500)
    enable_animations: bool = True

    @field_validator("theme")
    def validate_theme(self, v: str) -> str:
        """Validate theme name."""
        valid_themes = {"light", "dark", "auto", "high_contrast"}
        if v.lower() not in valid_themes:
            raise ValueError(f"Invalid theme: {v}. Must be one of {valid_themes}")
        return v.lower()

    @field_validator("default_view")
    def validate_view(self, v: str) -> str:
        """Validate default view."""
        valid_views = {"grid", "list", "table", "tiles"}
        if v.lower() not in valid_views:
            raise ValueError(f"Invalid view: {v}. Must be one of {valid_views}")
        return v.lower()


class PerformanceConfig(BaseModel):
    """Performance tuning configuration."""

    enable_multithreading: bool = True
    cache_thumbnails: bool = True
    thumbnail_cache_size_mb: int = Field(default=500, ge=50, le=5000)
    lazy_load_threshold: int = Field(default=100, ge=10)
    db_vacuum_interval_days: int = Field(default=7, ge=1)
    memory_limit_mb: int = Field(default=1024, ge=256)
    io_buffer_size_kb: int = Field(default=64, ge=8, le=1024)


class RetroAchievementsConfig(BaseModel):
    """RetroAchievements configuration."""

    enabled: bool = False
    username: str | None = None
    api_key: str | None = None
    auto_identify: bool = True
    cache_ttl_hours: int = Field(default=24, ge=1)
    rate_limit_requests_per_second: float = Field(default=1.0, ge=0.1, le=10.0)


class AppConfig(BaseModel):
    """Main application configuration."""

    version: str = Field(default="1.0.0")
    platforms: dict[str, PlatformConfig] = Field(default_factory=dict)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    retroachievements: RetroAchievementsConfig = Field(default_factory=RetroAchievementsConfig)
    debug_mode: bool = False
    auto_update: bool = True
    telemetry_enabled: bool = False


class ConfigValidator:
    """Validates and manages application configuration."""

    def __init__(self, config_path: Path | None = None):
        """Initialize the configuration validator.

        Args:
            config_path: Path to the configuration file.
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self.config: AppConfig | None = None
        self._validation_errors: list[str] = []

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        import sys

        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".config"

        config_dir = base / "RomShelf"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def load_config(self) -> AppConfig:
        """Load and validate configuration from file.

        Returns:
            Validated configuration object.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    config_data = json.load(f)
                self.config = self._validate_config(config_data)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in configuration file: {e}")
                self.config = self._get_default_config()
            except ValidationError as e:
                self.logger.error(f"Configuration validation failed: {e}")
                self.config = self._get_default_config()
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                self.config = self._get_default_config()
        else:
            self.logger.info("No configuration file found, using defaults")
            self.config = self._get_default_config()
            self.save_config()

        return self.config

    def _validate_config(self, config_data: dict[str, Any]) -> AppConfig:
        """Validate configuration data.

        Args:
            config_data: Raw configuration dictionary.

        Returns:
            Validated configuration object.

        Raises:
            ValidationError: If validation fails.
        """
        try:
            config = AppConfig(**config_data)
            self._perform_additional_validation(config)
            return config
        except ValidationError as e:
            self._validation_errors = [str(err) for err in e.errors()]
            raise

    def _perform_additional_validation(self, config: AppConfig) -> None:
        """Perform additional validation beyond Pydantic."""
        errors = []

        # Check for conflicting settings
        if config.performance.memory_limit_mb < config.performance.thumbnail_cache_size_mb:
            errors.append(
                "Memory limit is less than thumbnail cache size. "
                "This may cause performance issues."
            )

        # Validate RetroAchievements settings
        if config.retroachievements.enabled:
            if not config.retroachievements.username or not config.retroachievements.api_key:
                errors.append("RetroAchievements is enabled but credentials are missing")

        # Check database settings
        if config.database.max_connections < config.scanner.num_workers:
            self.logger.warning(
                "Database max_connections is less than scanner workers. "
                "This may cause connection pool exhaustion."
            )

        if errors:
            for error in errors:
                self.logger.warning(f"Configuration warning: {error}")

    def _get_default_config(self) -> AppConfig:
        """Get default configuration."""
        return AppConfig()

    def save_config(self) -> None:
        """Save current configuration to file."""
        if not self.config:
            self.logger.error("No configuration to save")
            return

        try:
            config_data = self.config.model_dump()

            # Save configuration as-is

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors from last validation attempt.

        Returns:
            List of error messages.
        """
        return self._validation_errors

    def update_setting(self, path: str, value: Any) -> bool:
        """Update a specific setting using dot notation.

        Args:
            path: Dot-separated path to setting (e.g., "scanner.num_workers").
            value: New value for the setting.

        Returns:
            True if successful, False otherwise.
        """
        if not self.config:
            return False

        try:
            parts = path.split(".")
            config_dict = self.config.model_dump()

            # Navigate to the setting
            current = config_dict
            for part in parts[:-1]:
                if part not in current:
                    self.logger.error(f"Invalid setting path: {path}")
                    return False
                current = current[part]

            # Update the value
            current[parts[-1]] = value

            # Validate the new configuration
            self.config = self._validate_config(config_dict)
            self.save_config()

            self.logger.info(f"Updated setting {path} = {value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update setting {path}: {e}")
            return False


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass

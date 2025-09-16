"""Settings service - centralized settings management and validation."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..core.settings import Settings, SettingsManager


class SettingsService:
    """Service for centralized settings management and validation."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        """Initialize the settings service."""
        self.logger = logging.getLogger(__name__)
        self._settings_manager = settings_manager
        self._change_callbacks: list[Callable[[], None]] = []

    @property
    def settings(self) -> Settings:
        """Get the current settings."""
        return self._settings_manager.settings

    def add_change_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when settings change."""
        self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[], None]) -> None:
        """Remove a settings change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def _notify_changes(self) -> None:
        """Notify all registered callbacks of settings changes."""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in settings change callback: {e}")

    def save_settings(self) -> bool:
        """Save current settings to disk."""
        try:
            self._settings_manager.save()
            self._notify_changes()
            return True
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False

    def reload_settings(self) -> bool:
        """Reload settings from disk."""
        try:
            # Create a new settings manager to reload from disk
            self._settings_manager = SettingsManager(self._settings_manager.settings_file)
            self._notify_changes()
            return True
        except Exception as e:
            self.logger.error(f"Error reloading settings: {e}")
            return False

    # Theme and UI Settings
    def get_theme(self) -> str:
        """Get the current theme."""
        return self.settings.theme

    def set_theme(self, theme: str) -> None:
        """Set the application theme."""
        if theme in ["light", "dark"]:
            self.settings.theme = theme

    def get_font_size(self) -> int:
        """Get the current font size."""
        return self.settings.font_size

    def set_font_size(self, size: int) -> None:
        """Set the application font size."""
        if 8 <= size <= 14:
            self.settings.font_size = size

    def get_table_row_height(self) -> int:
        """Get the table row height."""
        return self.settings.table_row_height

    def set_table_row_height(self, height: int) -> None:
        """Set the table row height."""
        if 18 <= height <= 32:
            self.settings.table_row_height = height

    def get_preferred_region(self) -> str:
        """Get the preferred region."""
        return self.settings.preferred_region

    def set_preferred_region(self, region: str) -> None:
        """Set the preferred region."""
        if region in ["USA", "Europe", "Japan", "World"]:
            self.settings.preferred_region = region

    def get_duplicate_handling(self) -> str:
        """Get the duplicate handling strategy."""
        return self.settings.duplicate_handling

    def set_duplicate_handling(self, strategy: str) -> None:
        """Set the duplicate handling strategy."""
        valid_strategies = ["keep_first", "keep_all", "prefer_region"]
        if strategy in valid_strategies:
            self.settings.duplicate_handling = strategy

    # RetroAchievements Settings
    def get_retroachievements_username(self) -> str:
        """Get RetroAchievements username."""
        return getattr(self.settings, "retroachievements_username", "")

    def set_retroachievements_username(self, username: str) -> None:
        """Set RetroAchievements username."""
        self.settings.retroachievements_username = username.strip()

    def get_retroachievements_api_key(self) -> str:
        """Get RetroAchievements API key."""
        return getattr(self.settings, "retroachievements_api_key", "")

    def set_retroachievements_api_key(self, api_key: str) -> None:
        """Set RetroAchievements API key."""
        self.settings.retroachievements_api_key = api_key.strip()

    def has_retroachievements_credentials(self) -> bool:
        """Check if RetroAchievements credentials are configured."""
        username = self.get_retroachievements_username()
        api_key = self.get_retroachievements_api_key()
        return bool(username and api_key)

    # Platform Settings
    def get_platform_settings(self, platform_id: str) -> dict[str, Any]:
        """Get settings for a specific platform."""
        return self.settings.platform_settings.get(platform_id, {})

    def set_platform_setting(self, platform_id: str, key: str, value: Any) -> None:
        """Set a specific platform setting."""
        if platform_id not in self.settings.platform_settings:
            self.settings.platform_settings[platform_id] = {}
        self.settings.platform_settings[platform_id][key] = value

    def get_platform_directories(self, platform_id: str) -> list[str]:
        """Get ROM directories for a specific platform."""
        platform_settings = self.get_platform_settings(platform_id)
        return platform_settings.get("rom_directories", [])

    def set_platform_directories(self, platform_id: str, directories: list[str]) -> None:
        """Set ROM directories for a specific platform."""
        # Validate that directories exist
        valid_directories = []
        for directory in directories:
            path = Path(directory)
            if path.exists() and path.is_dir():
                valid_directories.append(str(path.resolve()))
            else:
                self.logger.warning(f"Directory does not exist: {directory}")

        self.set_platform_setting(platform_id, "rom_directories", valid_directories)

    def add_platform_directory(self, platform_id: str, directory: str) -> bool:
        """Add a directory to a platform's ROM directories."""
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return False

        directories = self.get_platform_directories(platform_id)
        directory_str = str(path.resolve())

        if directory_str not in directories:
            directories.append(directory_str)
            self.set_platform_directories(platform_id, directories)
            return True

        return False

    def remove_platform_directory(self, platform_id: str, directory: str) -> bool:
        """Remove a directory from a platform's ROM directories."""
        directories = self.get_platform_directories(platform_id)
        directory_str = str(Path(directory).resolve())

        if directory_str in directories:
            directories.remove(directory_str)
            self.set_platform_directories(platform_id, directories)
            return True

        return False

    def clear_platform_directories(self, platform_id: str) -> None:
        """Clear all directories for a platform."""
        self.set_platform_setting(platform_id, "rom_directories", [])

    def get_platform_scan_subdirectories(self, platform_id: str) -> bool:
        """Get whether to scan subdirectories for a platform."""
        platform_settings = self.get_platform_settings(platform_id)
        return platform_settings.get("scan_subdirectories", True)

    def set_platform_scan_subdirectories(self, platform_id: str, scan_subdirs: bool) -> None:
        """Set whether to scan subdirectories for a platform."""
        self.set_platform_setting(platform_id, "scan_subdirectories", scan_subdirs)

    def get_platform_handle_archives(self, platform_id: str) -> bool:
        """Get whether to handle archives for a platform."""
        platform_settings = self.get_platform_settings(platform_id)
        return platform_settings.get("handle_archives", True)

    def set_platform_handle_archives(self, platform_id: str, handle_archives: bool) -> None:
        """Set whether to handle archives for a platform."""
        self.set_platform_setting(platform_id, "handle_archives", handle_archives)

    def get_platform_supported_formats(self, platform_id: str) -> list[str]:
        """Get supported formats for a platform."""
        platform_settings = self.get_platform_settings(platform_id)
        return platform_settings.get("supported_formats", [])

    def set_platform_supported_formats(self, platform_id: str, formats: list[str]) -> None:
        """Set supported formats for a platform."""
        self.set_platform_setting(platform_id, "supported_formats", formats)

    # Validation Methods
    def validate_retroachievements_credentials(self) -> tuple[bool, str]:
        """Validate RetroAchievements credentials."""
        username = self.get_retroachievements_username()
        api_key = self.get_retroachievements_api_key()

        if not username:
            return False, "Username is required"
        if not api_key:
            return False, "API key is required"
        if len(api_key) < 10:
            return False, "API key appears to be too short"

        return True, "Credentials appear valid"

    def get_configured_platforms(self) -> list[str]:
        """Get list of platform IDs that have ROM directories configured."""
        configured = []
        for platform_id, settings in self.settings.platform_settings.items():
            if settings.get("rom_directories"):
                configured.append(platform_id)
        return configured

    def has_any_platform_directories(self) -> bool:
        """Check if any platform has directories configured."""
        return len(self.get_configured_platforms()) > 0

    def get_total_directory_count(self) -> int:
        """Get total number of directories configured across all platforms."""
        total = 0
        for platform_settings in self.settings.platform_settings.values():
            directories = platform_settings.get("rom_directories", [])
            total += len(directories)
        return total

    def export_settings(self, file_path: Path) -> bool:
        """Export current settings to a file."""
        try:
            # Create a copy of settings and save to specified path
            backup_manager = SettingsManager(file_path)
            backup_manager.settings = self.settings
            backup_manager.save()
            return True
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: Path) -> bool:
        """Import settings from a file."""
        try:
            if not file_path.exists():
                return False

            # Load settings from file
            temp_manager = SettingsManager(file_path)

            # Update current settings
            self.settings.__dict__.update(temp_manager.settings.__dict__)
            self._notify_changes()
            return True
        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False

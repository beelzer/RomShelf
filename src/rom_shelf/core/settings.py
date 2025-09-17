"""Settings management for the ROM Shelf application."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PlatformSettings:
    """Platform-specific settings."""

    supports_archives: bool = True
    supports_multi_part: bool = True
    supports_normal: bool = True


@dataclass
class Settings:
    """Application settings data class."""

    theme: str = "dark"
    font_size: int = 9
    table_row_height: int = 24
    preferred_region: str = "USA"
    duplicate_handling: str = "keep_first"  # keep_first, keep_all, prefer_region
    retroachievements_username: str = ""
    retroachievements_api_key: str = ""
    platform_settings: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def ra_username(self) -> str:
        """Alias for retroachievements_username."""
        return self.retroachievements_username

    @property
    def ra_api_key(self) -> str:
        """Alias for retroachievements_api_key."""
        return self.retroachievements_api_key

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "theme": self.theme,
            "font_size": self.font_size,
            "table_row_height": self.table_row_height,
            "preferred_region": self.preferred_region,
            "duplicate_handling": self.duplicate_handling,
            "retroachievements_username": self.retroachievements_username,
            "retroachievements_api_key": self.retroachievements_api_key,
            "platform_settings": self.platform_settings.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        # Platform settings are now stored as dictionaries directly
        platform_settings = data.get("platform_settings", {})

        settings = cls(
            theme=data.get("theme", "dark"),
            font_size=data.get("font_size", 9),
            table_row_height=data.get("table_row_height", 24),
            preferred_region=data.get("preferred_region", "USA"),
            duplicate_handling=data.get("duplicate_handling", "keep_first"),
            retroachievements_username=data.get("retroachievements_username", ""),
            retroachievements_api_key=data.get("retroachievements_api_key", ""),
            platform_settings=platform_settings,
        )

        # Initialize platform settings with defaults if they don't exist
        settings._initialize_platform_defaults()

        return settings

    def _initialize_platform_defaults(self) -> None:
        """Initialize platform settings with defaults from platform implementations."""
        # This method is now a no-op - platforms will register themselves
        # using register_platform_defaults() when they are loaded
        pass

    def register_platform_defaults(self, platform_id: str, platform_settings_def: list) -> None:
        """Register default settings for a platform."""
        # Always initialize if platform doesn't exist or is empty
        if platform_id not in self.platform_settings or not self.platform_settings[platform_id]:
            # Create defaults dict from platform settings definition
            defaults = {}
            for setting in platform_settings_def:
                defaults[setting.key] = setting.default_value

            self.platform_settings[platform_id] = defaults

    def save(self, file_path: Path) -> None:
        """Save settings to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> "Settings":
        """Load settings from file."""
        if not file_path.exists():
            return cls()  # Return default settings

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return cls()  # Return default settings on error


class SettingsManager:
    """Manages application settings."""

    def __init__(self, settings_path: Path) -> None:
        """Initialize the settings manager."""
        self._settings_path = settings_path
        self._settings = Settings.load(settings_path)

    @property
    def settings(self) -> Settings:
        """Get current settings."""
        return self._settings

    def save(self) -> None:
        """Save current settings to file."""
        self._settings.save(self._settings_path)

    def update_settings(self, **kwargs: Any) -> None:
        """Update settings with new values."""
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
        self.save()


# Global settings instance
_global_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _global_settings
    if _global_settings is None:
        _global_settings = Settings()
    return _global_settings


def set_settings(settings: Settings) -> None:
    """Set the global settings instance."""
    global _global_settings
    _global_settings = settings

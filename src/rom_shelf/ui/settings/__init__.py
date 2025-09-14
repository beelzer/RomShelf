"""Settings UI components."""

from .interface_page import InterfacePage
from .platform_specific_page import PlatformSpecificPage
from .platforms_page import PlatformsPage
from .retroachievements_page import RetroAchievementsPage
from .settings_base import SettingsPage, normalize_path_display
from .settings_dialog import SettingsDialog

__all__ = [
    "SettingsDialog",
    "InterfacePage",
    "RetroAchievementsPage",
    "PlatformsPage",
    "PlatformSpecificPage",
    "SettingsPage",
    "normalize_path_display",
]

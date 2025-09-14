"""Settings UI components."""

from .settings_dialog import SettingsDialog
from .interface_page import InterfacePage
from .retroachievements_page import RetroAchievementsPage
from .platforms_page import PlatformsPage
from .platform_specific_page import PlatformSpecificPage
from .settings_base import SettingsPage, normalize_path_display

__all__ = [
    "SettingsDialog",
    "InterfacePage",
    "RetroAchievementsPage",
    "PlatformsPage",
    "PlatformSpecificPage",
    "SettingsPage",
    "normalize_path_display",
]
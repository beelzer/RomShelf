"""Platform-specific ROM handling modules."""

# Import core platform infrastructure
from .base_platform import BasePlatform, PlatformSetting, SettingType, TableColumn
from .platform_decorators import register_platform
from .platform_families import (
    CartridgeBasedPlatform,
    ConsolePlatform,
    DiscBasedPlatform,
    HandheldPlatform,
    PlatformFamily,
)
from .platform_registry import platform_registry
from .validation import ROMValidator, ValidationChain

__all__ = [
    "BasePlatform",
    "PlatformSetting",
    "SettingType",
    "TableColumn",
    "register_platform",
    "CartridgeBasedPlatform",
    "ConsolePlatform",
    "DiscBasedPlatform",
    "HandheldPlatform",
    "PlatformFamily",
    "platform_registry",
    "ValidationChain",
    "ROMValidator",
]

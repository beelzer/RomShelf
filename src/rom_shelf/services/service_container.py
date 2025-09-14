"""Service container for dependency injection and service management."""

from pathlib import Path
from typing import Optional

from ..core.settings import SettingsManager
from .database_service import DatabaseService
from .platform_service import PlatformService
from .rom_scanning_service import ROMScanningService
from .search_service import SearchService
from .settings_service import SettingsService


class ServiceContainer:
    """Container for managing application services with dependency injection."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        """Initialize the service container."""
        self._settings_manager = settings_manager

        # Initialize services (lazy loading)
        self._settings_service: Optional[SettingsService] = None
        self._platform_service: Optional[PlatformService] = None
        self._database_service: Optional[DatabaseService] = None
        self._rom_scanning_service: Optional[ROMScanningService] = None
        self._search_service: Optional[SearchService] = None

    @property
    def settings_service(self) -> SettingsService:
        """Get the settings service."""
        if self._settings_service is None:
            self._settings_service = SettingsService(self._settings_manager)
        return self._settings_service

    @property
    def platform_service(self) -> PlatformService:
        """Get the platform service."""
        if self._platform_service is None:
            self._platform_service = PlatformService()
        return self._platform_service

    @property
    def database_service(self) -> DatabaseService:
        """Get the database service."""
        if self._database_service is None:
            self._database_service = DatabaseService()
        return self._database_service

    @property
    def rom_scanning_service(self) -> ROMScanningService:
        """Get the ROM scanning service."""
        if self._rom_scanning_service is None:
            self._rom_scanning_service = ROMScanningService()
        return self._rom_scanning_service

    @property
    def search_service(self) -> SearchService:
        """Get the search service."""
        if self._search_service is None:
            self._search_service = SearchService()
        return self._search_service

    def get_all_services(self) -> dict:
        """Get all services for debugging/inspection."""
        return {
            'settings_service': self.settings_service,
            'platform_service': self.platform_service,
            'database_service': self.database_service,
            'rom_scanning_service': self.rom_scanning_service,
            'search_service': self.search_service,
        }

    def cleanup(self) -> None:
        """Cleanup all services."""
        # Stop any ongoing operations
        if self._rom_scanning_service and self._rom_scanning_service.is_scanning():
            self._rom_scanning_service.stop_scan()

        # Save any pending data
        if self._settings_service:
            self._settings_service.save_settings()

        if self._database_service:
            self._database_service.save_database()
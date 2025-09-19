"""Scan orchestration that decouples ROM discovery from the main window."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, Signal

from ...core.rom_scanner import ROMScannerThread
from ...platforms.core.platform_registry import platform_registry as default_platform_registry


@dataclass(frozen=True, slots=True)
class PlatformSummary:
    """Lightweight description of a platform scan configuration."""

    platform_id: str
    name: str
    directories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScanStartContext:
    """Information broadcast when a new scan kicks off."""

    total_directories: int
    platform_count: int
    platforms: tuple[PlatformSummary, ...]


@dataclass(frozen=True, slots=True)
class RomFoundEvent:
    """Event payload describing a single ROM discovery."""

    entry: Any
    is_new: bool
    platform_name: str
    new_count: int
    existing_count: int
    roms_by_platform: dict[str, int]
    ra_matches_by_platform: dict[str, int]


@dataclass(frozen=True, slots=True)
class ScanCompletionContext:
    """Aggregate information when a scan completes."""

    entries: Sequence[Any]
    new_count: int
    existing_count: int
    roms_by_platform: dict[str, int]
    ra_matches_by_platform: dict[str, int]


class ROMScanController(QObject):
    """Owns the ROM scanner thread and surfaces high-level events."""

    scan_started = Signal(object)
    rom_found = Signal(object)
    scan_progress = Signal(object)
    scan_completed = Signal(object)
    scan_failed = Signal(str)

    def __init__(
        self,
        settings_service,
        platform_registry=default_platform_registry,
        parent: QObject | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self._platform_registry = platform_registry
        self._logger = logger or logging.getLogger(__name__)

        self._scanner_thread: ROMScannerThread | None = None
        self._rom_database = None

        self._new_rom_count = 0
        self._existing_rom_count = 0
        self._roms_by_platform: dict[str, int] = {}
        self._ra_matches_by_platform: dict[str, int] = {}

    def has_configured_platforms(self) -> bool:
        """Return True if at least one platform has directories configured."""
        return self._settings_service.has_any_platform_directories()

    def is_running(self) -> bool:
        """Return True while a scan thread is active."""
        return bool(self._scanner_thread and self._scanner_thread.isRunning())

    def start_scan(self) -> bool:
        """Begin scanning according to the current settings.

        Returns True when a scan thread was started, False otherwise.
        """
        platform_configs, summaries, total_directories = self._build_platform_configs()

        if not platform_configs:
            msg = "No ROM directories configured for any platform. Check Settings."
            self._logger.info(msg)
            self.scan_failed.emit(msg)
            return False

        self.stop_scan()
        self._reset_counters()
        self._prime_rom_database()

        self._scanner_thread = ROMScannerThread(platform_configs)
        self._connect_thread_signals(self._scanner_thread)

        context = ScanStartContext(
            total_directories=total_directories,
            platform_count=len(platform_configs),
            platforms=tuple(summaries),
        )
        self.scan_started.emit(context)

        self._scanner_thread.start()
        self._logger.info(
            "Started scanning %s directories across %s platforms...",
            total_directories,
            len(platform_configs),
        )
        return True

    def stop_scan(self) -> None:
        """Terminate any running scanner thread."""
        if not self._scanner_thread:
            return

        thread = self._scanner_thread
        self._scanner_thread = None

        if thread.isRunning():
            self._logger.info("Stopping ROM scanner thread...")
            try:
                thread.scanner.stop_scan()
            except Exception:
                self._logger.exception("Failed to request scanner shutdown")
            thread.quit()
            thread.wait(5000)
            if thread.isRunning():
                self._logger.warning("Thread didn't stop gracefully, terminating...")
                thread.terminate()
                thread.wait(1000)

        thread.deleteLater()

    # Internal helpers -----------------------------------------------------------------

    def _reset_counters(self) -> None:
        self._new_rom_count = 0
        self._existing_rom_count = 0
        self._roms_by_platform = {}
        self._ra_matches_by_platform = {}

    def _prime_rom_database(self) -> None:
        try:
            from ..core.rom_database import get_rom_database

            self._rom_database = get_rom_database()
        except Exception:
            self._logger.debug("RetroAchievements database unavailable", exc_info=True)
            self._rom_database = None

    def _build_platform_configs(self) -> tuple[list[dict[str, Any]], list[PlatformSummary], int]:
        settings = self._settings_service.settings
        platform_configs: list[dict[str, Any]] = []
        summaries: list[PlatformSummary] = []
        total_directories = 0

        for platform in self._platform_registry.get_all_platforms():
            platform_settings = settings.platform_settings.get(platform.platform_id, {})
            directories: list[str] = platform_settings.get("rom_directories", [])

            if not directories:
                continue

            config = {
                "platform": platform,
                "directories": directories,
                "scan_subdirectories": platform_settings.get("scan_subdirectories", True),
                "handle_archives": platform_settings.get("handle_archives", True),
                "supported_formats": platform_settings.get(
                    "supported_formats", platform.get_supported_handlers()
                ),
                "supported_archives": platform_settings.get(
                    "supported_archives", platform.get_archive_content_extensions()
                ),
            }
            platform_configs.append(config)

            summaries.append(
                PlatformSummary(
                    platform_id=platform.platform_id,
                    name=getattr(platform, "name", platform.platform_id),
                    directories=tuple(directories),
                )
            )
            total_directories += len(directories)

        return platform_configs, summaries, total_directories

    def _connect_thread_signals(self, thread: ROMScannerThread) -> None:
        thread.scanner.rom_found.connect(self._handle_rom_found)
        thread.scanner.scan_completed.connect(self._handle_scan_completed)
        thread.scanner.scan_error.connect(self._handle_scan_error)
        thread.scanner.progress_updated.connect(self._handle_scan_progress)

    # Thread callbacks -----------------------------------------------------------------

    def _handle_rom_found(self, rom_entry) -> None:
        is_new = bool(getattr(rom_entry, "is_new_to_database", False))
        if is_new:
            self._new_rom_count += 1
        else:
            self._existing_rom_count += 1

        platform_name = getattr(rom_entry, "platform_name", rom_entry.platform_id)
        self._roms_by_platform[platform_name] = self._roms_by_platform.get(platform_name, 0) + 1

        if self._rom_database:
            try:
                fingerprint = self._rom_database.get_fingerprint(
                    rom_entry.file_path, getattr(rom_entry, "internal_path", None)
                )
                if fingerprint and getattr(fingerprint, "ra_game_id", None):
                    self._ra_matches_by_platform[platform_name] = (
                        self._ra_matches_by_platform.get(platform_name, 0) + 1
                    )
            except Exception:
                self._logger.debug("Unable to resolve RetroAchievements fingerprint", exc_info=True)

        event = RomFoundEvent(
            entry=rom_entry,
            is_new=is_new,
            platform_name=platform_name,
            new_count=self._new_rom_count,
            existing_count=self._existing_rom_count,
            roms_by_platform=dict(self._roms_by_platform),
            ra_matches_by_platform=dict(self._ra_matches_by_platform),
        )
        self.rom_found.emit(event)

    def _handle_scan_completed(self, all_entries: Iterable[Any]) -> None:
        entries = list(all_entries)
        context = ScanCompletionContext(
            entries=entries,
            new_count=self._new_rom_count,
            existing_count=self._existing_rom_count,
            roms_by_platform=dict(self._roms_by_platform),
            ra_matches_by_platform=dict(self._ra_matches_by_platform),
        )
        self.scan_completed.emit(context)
        self._cleanup_thread()

    def _handle_scan_error(self, error_msg: str) -> None:
        message = str(error_msg)
        self._logger.error("Scan error: %s", message)
        self.scan_failed.emit(message)
        self._cleanup_thread()

    def _handle_scan_progress(self, progress) -> None:
        self.scan_progress.emit(progress)

    def _cleanup_thread(self) -> None:
        if not self._scanner_thread:
            return

        thread = self._scanner_thread
        self._scanner_thread = None
        thread.quit()
        thread.wait()
        thread.deleteLater()

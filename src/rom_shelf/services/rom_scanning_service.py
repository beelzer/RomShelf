"""ROM scanning service - business logic for ROM discovery and validation."""

import concurrent.futures
import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..core.archive_processor import ArchiveProcessor
from ..core.extension_handler import FileHandlingType, extension_registry

# TODO: Replace with platform-specific multi-file handling
from ..core.rom_database import get_rom_database
from ..models.rom_entry import ROMEntry
from ..platforms.core.base_platform import BasePlatform
from .retroachievements_service import RetroAchievementsService


class ScanProgress:
    """Progress information for ROM scanning."""

    def __init__(self) -> None:
        """Initialize scan progress."""
        self.current_file = ""
        self.files_processed = 0
        self.total_files = 0
        self.rom_entries_found = 0

    def __str__(self) -> str:
        """String representation of scan progress."""
        return f"Progress: {self.files_processed}/{self.total_files} files, {self.rom_entries_found} ROMs found"


class ScanConfiguration:
    """Configuration for ROM scanning operations."""

    def __init__(self) -> None:
        """Initialize scan configuration with defaults."""
        self.scan_subdirectories: bool = True
        self.handle_archives: bool = True
        self.max_workers: int = min(32, (os.cpu_count() or 1) + 4)
        self.supported_formats: list[str] = []
        self.supported_archives: list[str] = []


class ROMScanningService:
    """Service for ROM discovery and validation operations."""

    def __init__(self) -> None:
        """Initialize the ROM scanning service."""
        self.logger = logging.getLogger(__name__)
        self._archive_processor = ArchiveProcessor()
        # TODO: Replace with platform-specific multi-file handling
        self._rom_database = get_rom_database()
        self._ra_service = RetroAchievementsService()
        self._is_scanning = False
        self._should_stop = False
        self._progress_lock = threading.Lock()
        self._ra_match_count = 0

        # Callbacks for UI communication
        self._progress_callback: Callable[[ScanProgress], None] | None = None
        self._rom_found_callback: Callable[[ROMEntry], None] | None = None
        self._error_callback: Callable[[str], None] | None = None

    def set_progress_callback(self, callback: Callable[[ScanProgress], None]) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback

    def set_rom_found_callback(self, callback: Callable[[ROMEntry], None]) -> None:
        """Set callback for when ROMs are found."""
        self._rom_found_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for error reporting."""
        self._error_callback = callback

    def is_scanning(self) -> bool:
        """Check if a scan is currently in progress."""
        return self._is_scanning

    def stop_scan(self) -> None:
        """Signal the scanner to stop."""
        self._should_stop = True

    def scan_platform_directories(self, platform_configs: list[dict[str, Any]]) -> list[ROMEntry]:
        """
        Scan directories for ROMs based on platform configurations.

        Args:
            platform_configs: List of platform configuration dictionaries containing:
                - platform: BasePlatform instance
                - directories: List of directory paths to scan
                - scan_subdirectories: Whether to scan subdirectories
                - handle_archives: Whether to process archive files
                - supported_formats: List of supported file extensions
                - supported_archives: List of supported archive extensions

        Returns:
            List of found ROM entries
        """
        if self._is_scanning:
            if self._error_callback:
                self._error_callback("Scan already in progress")
            return []

        try:
            self._is_scanning = True
            self._should_stop = False

            return self._execute_scan(platform_configs)

        except Exception as e:
            if self._error_callback:
                self._error_callback(f"Scan error: {e}")
            return []
        finally:
            self._is_scanning = False
            self._should_stop = False

    def _execute_scan(self, platform_configs: list[dict[str, Any]]) -> list[ROMEntry]:
        """Execute the actual scanning operation."""
        all_entries = []
        progress = ScanProgress()

        # Count total files first
        self._count_total_files(platform_configs, progress)

        if self._progress_callback:
            self._progress_callback(progress)

        # Scan each platform
        for config in platform_configs:
            if self._should_stop:
                break

            platform_entries = self._scan_platform_config(config, progress)
            all_entries.extend(platform_entries)

        return all_entries

    def _count_total_files(
        self, platform_configs: list[dict[str, Any]], progress: ScanProgress
    ) -> None:
        """Count total files that will be scanned."""
        for config in platform_configs:
            directories = config.get("directories", [])
            scan_subdirs = config.get("scan_subdirectories", True)

            for directory_path in directories:
                try:
                    path = Path(directory_path)
                    if not path.exists():
                        continue

                    if scan_subdirs:
                        files = list(path.rglob("*"))
                    else:
                        files = list(path.iterdir())

                    progress.total_files += len([f for f in files if f.is_file()])
                except Exception:
                    continue

    def _scan_platform_config(
        self, config: dict[str, Any], progress: ScanProgress
    ) -> list[ROMEntry]:
        """Scan directories for a specific platform configuration."""
        platform: BasePlatform = config["platform"]
        directories = config.get("directories", [])
        scan_subdirs = config.get("scan_subdirectories", True)
        handle_archives = config.get("handle_archives", True)
        supported_formats = config.get("supported_formats", [])
        supported_archives = config.get("supported_archives", [])
        max_workers = config.get("max_workers", min(32, (os.cpu_count() or 1) + 4))

        platform_entries = []

        for directory_path in directories:
            if self._should_stop:
                break

            try:
                path = Path(directory_path)
                if not path.exists():
                    continue

                self.logger.info(f"Scanning directory: {path} (exists: {path.exists()})")

                # Get all files in directory
                if scan_subdirs:
                    files = [f for f in path.rglob("*") if f.is_file()]
                else:
                    files = [f for f in path.iterdir() if f.is_file()]

                self.logger.debug(f"Found {len(files)} files in {path}")

                if not files:
                    continue

                # Process files in parallel
                entries = self._process_files_parallel(
                    files,
                    platform,
                    handle_archives,
                    supported_formats,
                    supported_archives,
                    progress,
                    max_workers,
                )

                platform_entries.extend(entries)

            except Exception as e:
                if self._error_callback:
                    self._error_callback(f"Error scanning {directory_path}: {e}")
                continue

        return platform_entries

    def _process_files_parallel(
        self,
        files: list[Path],
        platform: BasePlatform,
        handle_archives: bool,
        supported_formats: list[str],
        supported_archives: list[str],
        progress: ScanProgress,
        max_workers: int,
    ) -> list[ROMEntry]:
        """Process files in parallel using thread pool."""
        self.logger.info(f"Starting multi-threaded scan with {max_workers} workers")
        start_time = time.time()

        entries = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file processing tasks
            future_to_file = {}
            for file_path in files:
                if self._should_stop:
                    break

                future = executor.submit(
                    self._process_single_file,
                    file_path,
                    platform,
                    handle_archives,
                    supported_formats,
                    supported_archives,
                )
                future_to_file[future] = file_path

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                if self._should_stop:
                    break

                try:
                    rom_entries = future.result()
                    if rom_entries:
                        entries.extend(rom_entries)
                        for entry in rom_entries:
                            if self._rom_found_callback:
                                self._rom_found_callback(entry)

                except Exception as e:
                    file_path = future_to_file[future]
                    self.logger.error(f"Error processing {file_path}: {e}")

                # Update progress
                with self._progress_lock:
                    progress.files_processed += 1
                    progress.rom_entries_found = len(entries)

                    if self._progress_callback:
                        self._progress_callback(progress)

        elapsed = time.time() - start_time
        if elapsed > 0:
            rate = len(files) / elapsed
            self.logger.info(
                f"Multi-threaded scan completed in {elapsed:.2f}s ({rate:.1f} files/second)"
            )

        return entries

    def _process_single_file(
        self,
        file_path: Path,
        platform: BasePlatform,
        handle_archives: bool,
        supported_formats: list[str],
        supported_archives: list[str],
    ) -> list[ROMEntry]:
        """Process a single file and return ROM entries if valid."""
        try:
            # Determine how to handle this file
            handling_type = extension_registry.get_handling_type(file_path.suffix.lower())

            if handling_type == FileHandlingType.ARCHIVE and handle_archives:
                # Process archive file
                return self._process_archive_file(file_path, platform, supported_archives)
            elif handling_type == FileHandlingType.MULTI_PART:
                # Process multi-part file
                return self._process_multi_part_file(file_path, platform, supported_formats)
            elif handling_type == FileHandlingType.SINGLE:
                # Process single ROM file
                return self._process_single_rom_file(file_path, platform, supported_formats)
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return []

    def _process_archive_file(
        self, file_path: Path, platform: BasePlatform, supported_archives: list[str]
    ) -> list[ROMEntry]:
        """Process an archive file."""
        if not self._archive_processor.is_supported_archive(file_path):
            return []

        # Extract and validate archive contents
        archive_contents = self._archive_processor.get_archive_contents(file_path)
        if not archive_contents:
            return []

        # Find ROM files in archive
        rom_files = []
        for content_file in archive_contents:
            if any(content_file.lower().endswith(ext) for ext in supported_archives):
                rom_files.append(content_file)

        if not rom_files:
            return []

        # Create ROM entries for valid files in archive
        entries = []
        for rom_file in rom_files:
            if platform.validate_file(file_path, rom_file):
                entry = self._create_rom_entry(file_path, platform, rom_file)
                if entry:
                    entries.append(entry)

        return entries

    def _process_multi_part_file(
        self, file_path: Path, platform: BasePlatform, supported_formats: list[str]
    ) -> list[ROMEntry]:
        """Process a multi-part ROM file."""
        # TODO: Replace with platform-specific multi-file validation
        # For now, process all files as they are
        pass

        if platform.validate_file(file_path):
            entry = self._create_rom_entry(file_path, platform)
            return [entry] if entry else []

        return []

    def _process_single_rom_file(
        self, file_path: Path, platform: BasePlatform, supported_formats: list[str]
    ) -> list[ROMEntry]:
        """Process a single ROM file."""
        if platform.validate_file(file_path):
            entry = self._create_rom_entry(file_path, platform)
            return [entry] if entry else []

        return []

    def _create_rom_entry(
        self, file_path: Path, platform: BasePlatform, internal_path: str | None = None
    ) -> ROMEntry | None:
        """Create a ROM entry for a validated file."""
        try:
            # Get or create fingerprint in database
            fingerprint = self._rom_database.get_fingerprint(file_path, internal_path)

            # Create new fingerprint if needed
            if not fingerprint:
                fingerprint = self._rom_database.create_rom_fingerprint(
                    file_path, internal_path, platform.id
                )
                self._rom_database.add_fingerprint(fingerprint)

            # Check if we need to look up RA data
            if fingerprint and not fingerprint.ra_game_id:
                # Only check RA if we haven't checked recently (within 24 hours)
                current_time = time.time()
                if current_time - fingerprint.ra_last_check > 86400:  # 24 hours
                    # Try to identify ROM in RetroAchievements
                    ra_info = self._ra_service.identify_rom(
                        file_path,
                        platform.id,
                        file_path.stem,  # Use filename without extension as display name
                    )

                    if ra_info:
                        # Update fingerprint with RA data
                        fingerprint.ra_game_id = ra_info["game_id"]
                        fingerprint.ra_hash = ra_info["hash"]
                        fingerprint.ra_title = ra_info["title"]
                        fingerprint.ra_last_check = current_time
                        self._rom_database.add_fingerprint(fingerprint)

                        self.logger.info(
                            f"Matched ROM to RA game: {ra_info['title']} (ID: {ra_info['game_id']})"
                        )

                        # Update match count
                        with self._progress_lock:
                            self._ra_match_count += 1
                    else:
                        # Mark that we checked but found no match
                        fingerprint.ra_last_check = current_time
                        self._rom_database.add_fingerprint(fingerprint)

            # Parse the ROM file
            rom_entry = platform.parse_rom_file(file_path, fingerprint.md5_hash, internal_path)

            if rom_entry:
                self.logger.debug(f"Found ROM: {rom_entry.display_name} ({rom_entry.platform_id})")

            return rom_entry

        except Exception as e:
            self.logger.error(f"Error creating ROM entry for {file_path}: {e}")
            return None

    def get_scan_statistics(self) -> dict[str, Any]:
        """Get scanning statistics."""
        return {
            "is_scanning": self._is_scanning,
            "database_entries": len(self._rom_database.fingerprints) if self._rom_database else 0,
            "ra_matches": self._ra_match_count,
        }

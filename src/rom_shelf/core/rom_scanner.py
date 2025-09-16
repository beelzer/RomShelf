"""ROM scanning functionality with archive and multi-file support."""

import concurrent.futures
import logging
import os
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from ..models.rom_entry import ROMEntry
from ..platforms.core.base_platform import BasePlatform
from .archive_processor import ArchiveProcessor
from .extension_handler import FileHandlingType, extension_registry

# Removed multi_file_validator - now handled by platforms
from .rom_database import FingerprintStatus, get_rom_database


class ScanProgress:
    """Progress information for ROM scanning."""

    def __init__(self) -> None:
        """Initialize scan progress."""
        self.current_file = ""
        self.files_processed = 0
        self.total_files = 0
        self.rom_entries_found = 0


class ROMScanner(QObject):
    """Scans directories for ROM files."""

    # Signals
    progress_updated = Signal(object)  # ScanProgress
    rom_found = Signal(object)  # ROMEntry
    scan_completed = Signal(list)  # List[ROMEntry]
    scan_error = Signal(str)  # Error message

    def __init__(self) -> None:
        """Initialize the ROM scanner."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._archive_processor = ArchiveProcessor()
        # Multi-file validation now handled by platforms
        self._rom_database = get_rom_database()
        self._is_scanning = False
        self._should_stop = False
        self._progress_lock = threading.Lock()
        self._max_workers = min(
            32, (os.cpu_count() or 1) + 4
        )  # Use more threads for I/O-bound work

    def scan_platforms(self, platform_configs: list[dict]) -> None:
        """Start scanning with platform-specific directory configurations."""
        if self._is_scanning:
            return

        self._is_scanning = True
        self._should_stop = False

        try:
            all_entries = []
            progress = ScanProgress()

            # Collect all files from all platform directories
            all_files = []
            platform_file_map = {}  # Maps file paths to their platforms

            for config in platform_configs:
                platform = config["platform"]
                directories = config.get("directories", [])
                scan_subdirectories = config.get("scan_subdirectories", True)

                platform_files = []
                for directory in directories:
                    # Normalize path - handle both forward and backward slashes
                    dir_path = Path(directory).resolve()
                    self.logger.info(
                        f"Scanning directory: {dir_path} (exists: {dir_path.exists()})"
                    )
                    if dir_path.exists() and dir_path.is_dir():
                        files = self._collect_files(dir_path, scan_subdirectories)
                        self.logger.debug(f"Found {len(files)} files in {dir_path}")
                        platform_files.extend(files)
                    else:
                        self.logger.warning(
                            f"Directory does not exist or is not accessible: {dir_path}"
                        )

                # Map files to their platform
                for file_path in platform_files:
                    if file_path not in platform_file_map:
                        platform_file_map[file_path] = []
                    platform_file_map[file_path].append(config)

                all_files.extend(platform_files)

            # Remove duplicates while preserving platform mapping
            unique_files = list(set(all_files))
            progress.total_files = len(unique_files)

            # Process files using multi-threading for better performance
            all_entries = self._process_files_multithreaded(
                unique_files, platform_file_map, progress
            )

            self.scan_completed.emit(all_entries)

            # Database auto-commits in SQLite
            self.logger.info(f"Scan completed with {len(all_entries)} ROM entries")

        except Exception as e:
            self.scan_error.emit(str(e))

        finally:
            self._is_scanning = False
            self._archive_processor.cleanup()

    def stop_scan(self) -> None:
        """Stop the current scan."""
        self._should_stop = True

    def _process_files_multithreaded(
        self, unique_files: list[Path], platform_file_map: dict, progress: ScanProgress
    ) -> list[ROMEntry]:
        """Process files using multiple threads for improved performance.

        Args:
            unique_files: List of file paths to process
            platform_file_map: Maps file paths to their platform configs
            progress: Shared progress object

        Returns:
            List of all ROM entries found
        """
        all_entries: list[ROMEntry] = []
        processed_files_lock = threading.Lock()
        processed_files: set[Path] = set()

        def process_single_file(file_path: Path) -> list[ROMEntry]:
            """Process a single file and return ROM entries."""
            if self._should_stop:
                return []

            file_entries: list[ROMEntry] = []

            # Thread-safe progress update
            with self._progress_lock:
                progress.current_file = str(file_path)
                progress.files_processed += 1
                self.progress_updated.emit(progress)

            # Skip if already processed (thread-safe check)
            with processed_files_lock:
                if file_path in processed_files:
                    return []
                processed_files.add(file_path)

            # Get relevant platform configs for this file
            relevant_configs = platform_file_map.get(file_path, [])

            for config in relevant_configs:
                if self._should_stop:
                    break

                platform = config["platform"]
                handle_archives = config.get("handle_archives", True)

                # Create thread-local processed files set for this file's processing
                local_processed = set()

                try:
                    # Process the file with this specific platform and its settings
                    entries = self._process_file(
                        file_path, [platform], handle_archives, local_processed, config
                    )

                    file_entries.extend(entries)

                    # Update global processed files with any related files found
                    with processed_files_lock:
                        processed_files.update(local_processed)

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {e}")
                    continue

            return file_entries

        try:
            # Use ThreadPoolExecutor for parallel file processing
            scan_start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                self.logger.info(f"Starting multi-threaded scan with {self._max_workers} workers")

                # Submit all files for processing
                future_to_file = {
                    executor.submit(process_single_file, file_path): file_path
                    for file_path in unique_files
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_file):
                    if self._should_stop:
                        # Cancel remaining futures
                        for remaining_future in future_to_file:
                            remaining_future.cancel()
                        break

                    try:
                        entries = future.result()
                        for entry in entries:
                            all_entries.append(entry)
                            with self._progress_lock:
                                progress.rom_entries_found += 1
                            self.rom_found.emit(entry)

                    except Exception as e:
                        file_path = future_to_file[future]
                        self.logger.error(f"Error processing {file_path}: {e}")

            scan_time = time.time() - scan_start_time
            files_per_second = len(unique_files) / scan_time if scan_time > 0 else 0
            self.logger.info(
                f"Multi-threaded scan completed in {scan_time:.2f}s ({files_per_second:.1f} files/second)"
            )

        except Exception as e:
            self.logger.error(f"Error in multithreaded processing: {e}")
            self.scan_error.emit(str(e))

        return all_entries

    def _check_or_create_fingerprint(
        self, file_path: Path, platform_id: str, internal_path: str = None
    ) -> bool:
        """Check if ROM fingerprint exists and is valid, create if needed.

        Args:
            file_path: Path to ROM file or archive
            platform_id: Platform identifier
            internal_path: Internal path for archive files

        Returns:
            True if ROM should be processed (new or changed), False if unchanged
        """
        try:
            # Check if fingerprint exists
            fingerprint = self._rom_database.get_fingerprint(file_path, internal_path)

            if fingerprint:
                # Verify fingerprint is still valid
                status = self._rom_database.verify_fingerprint(fingerprint)
                if status == FingerprintStatus.VALID:
                    # File unchanged, skip processing
                    self.logger.debug(f"Skipping unchanged file: {file_path.name}")
                    return False  # Don't process this file
                elif status in [FingerprintStatus.CHANGED, FingerprintStatus.CORRUPTED]:
                    # File changed, need to update fingerprint
                    self.logger.info(f"ROM file changed, updating: {file_path.name}")

            # Create new fingerprint for new or changed files
            new_fingerprint = self._rom_database.create_rom_fingerprint(
                file_path, internal_path=internal_path, platform=platform_id
            )

            # Store fingerprint in database
            self._rom_database.add_fingerprint(new_fingerprint)
            return True  # Process this file

        except Exception as e:
            self.logger.error(f"Database error for {file_path}: {e}")
            # Continue processing even if database fails
            return True  # Process on error to be safe

    def _collect_files(self, directory: Path, scan_subdirectories: bool) -> list[Path]:
        """Collect all files in directory."""
        files = []

        try:
            if scan_subdirectories:
                for root, _, filenames in os.walk(directory):
                    root_path = Path(root)
                    for filename in filenames:
                        files.append(root_path / filename)
            else:
                files.extend([f for f in directory.iterdir() if f.is_file()])
        except (OSError, PermissionError):
            pass  # Skip inaccessible directories

        return files

    def _process_file(
        self,
        file_path: Path,
        platforms: list[BasePlatform],
        handle_archives: bool,
        processed_files: set[Path],
        config: dict = None,
    ) -> list[ROMEntry]:
        """Process a single file and return ROM entries."""
        processed_files.add(file_path)
        entries: list[ROMEntry] = []

        # Get extension handler
        handler = extension_registry.get_handler_for_file(file_path)
        if not handler:
            return entries

        # Process based on handler type
        if handler.handling_type == FileHandlingType.DIRECT:
            # Direct ROM file
            entries.extend(self._process_direct_file(file_path, platforms, config))

        elif handler.handling_type == FileHandlingType.ARCHIVE and handle_archives:
            # Archive file
            entries.extend(self._process_archive_file(file_path, platforms, config))

        elif handler.handling_type == FileHandlingType.MULTI_FILE:
            # Multi-file ROM
            entries.extend(self._process_multi_file(file_path, platforms, processed_files, config))

        return entries

    def _process_direct_file(
        self, file_path: Path, platforms: list[BasePlatform], config: dict = None
    ) -> list[ROMEntry]:
        """Process a direct ROM file."""
        entries: list[ROMEntry] = []
        extension = file_path.suffix.lower()

        # Find platforms that support this extension
        for platform in platforms:
            # Check if extension is supported by platform
            supported_formats = platform.supported_handlers
            if config:
                # Use user's format settings if available
                supported_formats = config.get("supported_formats", platform.supported_handlers)

            if extension in supported_formats:
                if platform.validate_rom(file_path):
                    # Check/create database fingerprint
                    # Always create ROM entry, even for unchanged files
                    self._check_or_create_fingerprint(file_path, platform.platform_id)

                    entry = platform.create_rom_entry(file_path)
                    entries.append(entry)

        return entries

    def _process_archive_file(
        self, file_path: Path, platforms: list[BasePlatform], config: dict = None
    ) -> list[ROMEntry]:
        """Process an archive file."""
        entries: list[ROMEntry] = []

        if not self._archive_processor.can_process_archive(file_path):
            return entries

        # Get archive contents
        contents = self._archive_processor.get_archive_contents(file_path)

        # Find platforms that might have ROMs in this archive
        potential_platforms = set()
        for content_file in contents:
            content_ext = Path(content_file).suffix.lower()
            for platform in platforms:
                # Check user's format settings for archive contents
                supported_formats = platform.archive_content_extensions
                if config:
                    supported_formats = config.get(
                        "supported_formats", platform.archive_content_extensions
                    )

                if content_ext in supported_formats:
                    potential_platforms.add(platform)

        if not potential_platforms:
            return entries

        # Extract relevant files based on user's format settings
        extract_extensions = set()
        for platform in potential_platforms:
            supported_formats = platform.archive_content_extensions
            if config:
                supported_formats = config.get(
                    "supported_formats", platform.archive_content_extensions
                )
            extract_extensions.update(supported_formats)

        extracted_files = self._archive_processor.extract_files(file_path, list(extract_extensions))

        # Process extracted files
        for extracted_file in extracted_files:
            for platform in potential_platforms:
                content_ext = extracted_file.extracted_path.suffix.lower()

                # Check user's format settings for this extracted file
                supported_formats = platform.archive_content_extensions
                if config:
                    supported_formats = config.get(
                        "supported_formats", platform.archive_content_extensions
                    )

                if content_ext in supported_formats and platform.validate_rom(
                    extracted_file.extracted_path
                ):
                    # Check/create database fingerprint for archive content
                    # Always create ROM entry, even for unchanged files
                    self._check_or_create_fingerprint(
                        file_path, platform.platform_id, extracted_file.original_path
                    )

                    entry = platform.create_rom_entry(
                        file_path,  # Original archive path
                        internal_path=extracted_file.original_path,
                        is_archive=True,
                    )
                    # Update display name to use extracted filename
                    entry.display_name = extracted_file.extracted_path.stem

                    # Update file type to use the internal ROM format instead of archive format
                    internal_extension = Path(extracted_file.original_path).suffix.lower()
                    if internal_extension == ".sfc":
                        entry.metadata["file_type"] = "SFC"
                    elif internal_extension == ".smc":
                        entry.metadata["file_type"] = "SMC"
                    elif internal_extension:
                        entry.metadata["file_type"] = internal_extension.upper()[
                            1:
                        ]  # Remove the dot and uppercase
                    entries.append(entry)

        return entries

    def _process_multi_file(
        self,
        file_path: Path,
        platforms: list[BasePlatform],
        processed_files: set[Path],
        config: dict = None,
    ) -> list[ROMEntry]:
        """Process a multi-file ROM."""
        entries: list[ROMEntry] = []

        # Check if this is a primary file for a multi-file set using platforms
        primary_file = None
        related_files = [file_path]

        for platform in platforms:
            primary = platform.find_multi_file_primary(file_path)
            if primary:
                primary_file = primary
                related_files = platform.get_related_files(primary_file)
                break

        if not primary_file:
            return entries

        # Mark all related files as processed
        for related_file in related_files:
            processed_files.add(related_file)

        # Find platforms that support this file type
        extension = primary_file.suffix.lower()
        for platform in platforms:
            # Check user's format settings
            supported_formats = platform.supported_handlers
            if config:
                supported_formats = config.get("supported_formats", platform.supported_handlers)

            if extension in supported_formats:
                if platform.validate_rom(primary_file):
                    # Check/create database fingerprint for multi-file ROM
                    # Always create ROM entry, even for unchanged files
                    self._check_or_create_fingerprint(primary_file, platform.platform_id)

                    entry = platform.create_rom_entry(
                        primary_file,
                        related_files=related_files[1:],  # Exclude primary file
                    )
                    entries.append(entry)

        return entries


class ROMScannerThread(QThread):
    """Thread for running ROM scans with platform-specific configurations."""

    def __init__(self, platform_configs: list[dict]) -> None:
        """Initialize the scanner thread with platform configurations."""
        super().__init__()
        self._platform_configs = platform_configs
        self._scanner = ROMScanner()

    def run(self) -> None:
        """Run the scan in the thread."""
        self._scanner.scan_platforms(self._platform_configs)

    @property
    def scanner(self) -> ROMScanner:
        """Get the scanner instance."""
        return self._scanner

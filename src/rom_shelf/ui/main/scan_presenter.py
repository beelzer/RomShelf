"""Presentation-layer helpers for scan progress feedback."""

from __future__ import annotations

import logging

from .scan_controller import (
    RomFoundEvent,
    ScanCompletionContext,
    ScanStartContext,
)


class ScanUiPresenter:
    """Updates toolbars and dock widgets in response to scan events."""

    def __init__(self, toolbar_manager, scan_dock, logger: logging.Logger | None = None) -> None:
        self._toolbar_manager = toolbar_manager
        self._scan_dock = scan_dock
        self._logger = logger or logging.getLogger(__name__)

        self._last_progress_update = 0
        self._current_progress_percentage = 0
        self._platforms_announced: set[str] = set()

    # Event hooks ----------------------------------------------------------------------

    def on_scan_started(self, context: ScanStartContext) -> None:
        self._logger.debug("Scan started: %s platforms", context.platform_count)
        self._last_progress_update = 0
        self._current_progress_percentage = 0
        self._platforms_announced.clear()

        self._toolbar_manager.show_progress_bar()
        self._toolbar_manager.set_progress_indeterminate(True)

        message = f"Scanning {context.total_directories} directories across {context.platform_count} platforms..."
        self._toolbar_manager.update_status(message)

        if not self._scan_dock:
            return

        self._scan_dock.clear()
        platform_names = sorted({platform.name for platform in context.platforms})
        if platform_names:
            self._scan_dock.add_detail_message(
                f"Starting scan of {len(platform_names)} platforms: {', '.join(platform_names)}",
                "info",
            )
        self._scan_dock.add_detail_message("Scanning directories...", "info")
        self._scan_dock.set_expanded(True)
        self._scan_dock.show()

    def on_rom_found(self, event: RomFoundEvent) -> None:
        if self._scan_dock:
            self._scan_dock.update_scan_changes(
                new=event.new_count,
                existing=event.existing_count,
            )

            platform_total = event.roms_by_platform.get(event.platform_name, 0)
            if platform_total == 1 and event.platform_name not in self._platforms_announced:
                self._platforms_announced.add(event.platform_name)
                self._scan_dock.add_detail_message(
                    f"Found ROMs for {event.platform_name}",
                    "info",
                )

    def on_scan_progress(self, progress) -> None:
        # RetroAchievements sub-events are handled separately
        if hasattr(progress, "ra_event_type") and progress.ra_event_type:
            self._handle_ra_progress(progress)
            return

        if not self._should_update_progress(progress.files_processed, progress.total_files):
            return

        self._last_progress_update = progress.files_processed

        if progress.total_files > 0 and progress.files_processed <= progress.total_files:
            file_progress = (progress.files_processed / progress.total_files) * 95
            percentage = int(file_progress)
            if percentage > self._current_progress_percentage:
                if self._current_progress_percentage == 0:
                    self._toolbar_manager.set_progress_indeterminate(False)
                self._logger.debug(
                    "Progress: %s/%s (%s%%)",
                    progress.files_processed,
                    progress.total_files,
                    percentage,
                )
                self._toolbar_manager.update_progress(percentage)
                self._current_progress_percentage = percentage
        else:
            if progress.total_files == 0:
                self._logger.debug("Files processed: %s (total unknown)", progress.files_processed)
            if self._current_progress_percentage == 0:
                self._toolbar_manager.set_progress_indeterminate(True)

        file_name = None
        if progress.current_file:
            file_name = progress.current_file.split("/")[-1].split("\\")[-1]

        self._toolbar_manager.update_scan_details(
            operation=None,
            current_file=progress.current_file,
            files_processed=progress.files_processed,
            total_files=progress.total_files,
            roms_found=progress.rom_entries_found,
        )

        if file_name and progress.total_files > 0:
            if getattr(progress, "current_platform", None):
                status = (
                    f"{progress.current_platform}: {file_name} "
                    f"({progress.files_processed}/{progress.total_files})"
                )
            else:
                status = (
                    f"Scanning: {file_name} " f"({progress.files_processed}/{progress.total_files})"
                )
        else:
            status = f"Files processed: {progress.files_processed}"
        self._toolbar_manager.update_status(status)

    def on_scan_completed(self, context: ScanCompletionContext) -> None:
        self._logger.info("Scan completed. Found %s total ROMs.", len(context.entries))
        self._toolbar_manager.hide_progress_bar()

        if not self._scan_dock:
            return

        self._scan_dock.update_scan_changes(
            new=context.new_count,
            modified=0,
            removed=0,
            existing=context.existing_count,
        )

        self._scan_dock.add_detail_message("-" * 50, "info")
        self._scan_dock.add_detail_message(
            "SCAN COMPLETE - Platform Summary:",
            "success",
        )

        total_ra_matches = 0
        for platform, count in sorted(context.roms_by_platform.items()):
            ra_count = context.ra_matches_by_platform.get(platform, 0)
            total_ra_matches += ra_count
            if ra_count:
                detail = (
                    f"  - {platform}: {count} ROM{'s' if count != 1 else ''} "
                    f"({ra_count} with achievements)"
                )
            else:
                detail = f"  - {platform}: {count} ROM{'s' if count != 1 else ''}"
            self._scan_dock.add_detail_message(detail, "info")

        self._scan_dock.add_detail_message(
            f"Total: {len(context.entries)} ROMs found",
            "success",
        )

        if total_ra_matches:
            match_percentage = (
                (total_ra_matches / len(context.entries)) * 100 if context.entries else 0
            )
            self._scan_dock.add_detail_message(
                f"RetroAchievements: {total_ra_matches} matches ({match_percentage:.1f}%)",
                "success",
            )

        self._scan_dock.set_completed()

        self._toolbar_manager.update_status(f"Scan complete: {len(context.entries)} ROMs")

    def on_scan_failed(self, message: str) -> None:
        self._toolbar_manager.hide_progress_bar()
        self._toolbar_manager.update_status(message)

        if self._scan_dock:
            self._scan_dock.add_detail_message(message, "error")
            self._scan_dock.stop_scan()

    # Internal helpers -----------------------------------------------------------------

    def _should_update_progress(self, files_processed: int, total_files: int) -> bool:
        return (
            files_processed == 1
            or files_processed % 5 == 0
            or files_processed >= total_files > 0
            or files_processed - self._last_progress_update >= 10
        )

    def _handle_ra_progress(self, progress) -> None:
        event_type = progress.ra_event_type
        if event_type == "ra_update":
            self._toolbar_manager.update_scan_details(
                operation=progress.ra_message,
                detail_message=progress.ra_message,
                message_type="info",
            )
        elif event_type == "ra_download":
            self._toolbar_manager.update_download_progress(
                progress.ra_download_bytes,
                progress.ra_download_total,
                progress.ra_download_speed,
            )
        elif event_type == "ra_complete":
            self._toolbar_manager.update_scan_details(
                detail_message=progress.ra_message,
                message_type="success",
            )
        elif event_type == "ra_match":
            self._toolbar_manager.increment_ra_matches()
            self._toolbar_manager.update_scan_details(
                detail_message=f"Matched: {progress.ra_message}",
                message_type="success",
            )

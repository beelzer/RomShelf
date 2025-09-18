"""Main window for the ROM Shelf application using extracted components."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.rom_scanner import ROMScannerThread
from ...models.rom_table_model import ROMTableModel
from ...platforms.core.platform_registry import platform_registry
from ...services import ServiceContainer
from ..settings import SettingsDialog
from ..themes import get_theme_manager
from .platform_tree import PlatformTreeWidget
from .rom_table_view import ROMTableView
from .search_handler import SearchHandler
from .toolbar_manager import ToolbarManager


class MainWindow(QMainWindow):
    """Main window for the ROM Shelf application."""

    def __init__(self, service_container: ServiceContainer) -> None:
        """Initialize the main window."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._service_container = service_container
        self._settings_service = service_container.settings_service

        # Initialize components
        self._platform_tree: PlatformTreeWidget | None = None
        self._rom_table: ROMTableView | None = None
        self._search_handler: SearchHandler | None = None
        self._toolbar_manager: ToolbarManager | None = None
        self._rom_model: ROMTableModel | None = None

        # Scanner thread
        self._scanner_thread: ROMScannerThread | None = None

        # Setup UI and connections
        self._setup_ui()
        self._setup_connections()
        self._apply_ui_settings()

        # Initialize ROM table model
        self._setup_rom_model()

        # Start initial scan if directories are configured
        if self._has_platform_directories():
            self._start_rom_scan()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("ROM Shelf")
        self.setMinimumSize(900, 600)
        self.resize(1300, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        # Main content layout - platform tree auto-sizes, table gets remaining space
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        layout.addLayout(content_layout)

        # Left sidebar - Platform tree (auto-sized to content)
        self._platform_tree = PlatformTreeWidget()
        self._platform_tree.setMinimumWidth(200)
        # Set size policy to auto-size to content width
        self._platform_tree.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self._platform_tree)

        # Right side - ROM table (takes remaining space)
        self._rom_table = ROMTableView()
        content_layout.addWidget(self._rom_table, 1)  # Stretch factor 1

        # Initialize component managers
        self._toolbar_manager = ToolbarManager(self)
        self._search_handler = SearchHandler(self)

        # Create UI components using managers
        self._toolbar_manager.create_main_toolbar(self._start_rom_scan, self._open_settings)
        search_toolbar = self._search_handler.create_search_toolbar(self)
        self.addToolBar(search_toolbar)

        self._toolbar_manager.create_menu_bar(self._start_rom_scan, self._open_settings)
        self._toolbar_manager.create_status_bar()

        # Hide menu bar by default - show on Alt press
        self.menuBar().setVisible(False)
        self._menu_visible = False

    def _setup_connections(self) -> None:
        """Set up signal connections between components."""
        if self._platform_tree:
            self._platform_tree.platform_selected.connect(self._on_platform_selected)

        if self._search_handler:
            self._search_handler.filter_changed.connect(self._update_platform_counts)

    def _setup_rom_model(self) -> None:
        """Initialize the ROM table model and connect it to components."""
        self._rom_model = ROMTableModel(self)

        if self._rom_table:
            self._rom_table.set_model(self._rom_model)

            # Set up initial columns based on selected platform
            if self._platform_tree:
                initial_platform = self._platform_tree.get_selected_platform()
                self._rom_table.update_columns(initial_platform)

        if self._search_handler:
            self._search_handler.set_rom_model(self._rom_model)

    def _apply_ui_settings(self) -> None:
        """Apply the current theme and UI settings."""
        settings = self._settings_service.settings

        # Apply modern theme
        theme_manager = get_theme_manager()

        # Use only modern themes - update settings if needed
        if settings.theme == "dark":
            theme_name = "modern dark"
        elif settings.theme == "light":
            theme_name = "modern light"
        else:
            theme_name = settings.theme

        if theme_manager.set_theme(theme_name):
            app = QApplication.instance()
            if app:
                theme_manager.apply_theme_to_application(app)

        # Apply font size to the entire application
        app = QApplication.instance()
        if app:
            app_font = app.font()
            app_font.setPointSize(settings.font_size)
            app.setFont(app_font)

            # Also apply to main window and key components explicitly
            self.setFont(app_font)

            if self._platform_tree:
                self._platform_tree.setFont(app_font)

            if self._search_handler:
                self._search_handler.apply_font_settings(app_font)

            if self._toolbar_manager:
                self._toolbar_manager.apply_font_settings(app_font)

            # Table needs special handling
            if self._rom_table:
                self._rom_table.setFont(app_font)
                # Also apply to table headers
                self._rom_table.horizontalHeader().setFont(app_font)
                self._rom_table.verticalHeader().setFont(app_font)
                # Force the table to update its appearance
                self._rom_table.reset()
                self._rom_table.repaint()

            # Force update on all child widgets
            self._update_fonts_recursively(self, app_font)

        # Apply table row height
        if self._rom_table:
            self._rom_table.apply_table_settings(settings.table_row_height)

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self._service_container.settings_service._settings_manager, self)
        # Connect to apply changes immediately when Apply is clicked
        dialog.settings_applied.connect(self._on_settings_applied)
        if dialog.exec():
            # Apply new settings when OK is clicked
            self._on_settings_applied()

    def _on_platform_selected(self, selected_platform: str) -> None:
        """Handle platform selection changes."""
        if not self._rom_model or not self._rom_table:
            return

        if selected_platform == "all":
            # Show all platforms
            all_platforms = [p.platform_id for p in platform_registry.get_all_platforms()]
            self._rom_model.set_platform_filter(all_platforms)
        else:
            # Show only selected platform
            self._rom_model.set_platform_filter([selected_platform])

        self._rom_table.update_columns(selected_platform)
        self._update_platform_counts()

    def _update_platform_counts(self) -> None:
        """Update ROM counts for each platform."""
        if not self._rom_model or not self._platform_tree:
            return

        # Count ROMs by platform using search-filtered entries (ignoring platform filter)
        counts: dict[str, int] = {}
        entries = self._rom_model.get_search_filtered_entries()

        for entry in entries:
            counts[entry.platform_id] = counts.get(entry.platform_id, 0) + 1

        self._platform_tree.update_rom_counts(counts)

    def add_rom_entries(self, entries) -> None:
        """Add ROM entries to the table."""
        if not entries or not self._rom_model:
            return

        self._rom_model.add_rom_entries(entries)
        self._update_platform_counts()

    def clear_rom_entries(self) -> None:
        """Clear all ROM entries."""
        if self._rom_model:
            self._rom_model.clear()
        self._update_platform_counts()

    def get_selected_platform(self) -> str:
        """Get the selected platform ID."""
        if self._platform_tree:
            return self._platform_tree.get_selected_platform()
        return "all"

    def _has_platform_directories(self) -> bool:
        """Check if any platform has directories configured."""
        return self._settings_service.has_any_platform_directories()

    def _update_fonts_recursively(self, widget, font):
        """Recursively apply font to widget and all its children."""
        try:
            widget.setFont(font)
            for child in widget.findChildren(QWidget):
                child.setFont(font)
        except Exception:
            pass  # Skip widgets that don't support fonts

    def _on_settings_applied(self) -> None:
        """Handle settings being applied."""
        self._apply_ui_settings()
        self._start_rom_scan()

    def _start_rom_scan(self) -> None:
        """Start scanning for ROMs based on platform-specific settings."""
        settings = self._settings_service.settings

        # Create platform-specific configurations
        platform_configs = []
        platforms = platform_registry.get_all_platforms()
        total_directories = 0

        for platform in platforms:
            # Get platform-specific settings
            platform_settings = settings.platform_settings.get(platform.platform_id, {})

            # Get platform directories
            platform_directories = platform_settings.get("rom_directories", [])

            if platform_directories:  # Only add platforms that have directories configured
                platform_configs.append(
                    {
                        "platform": platform,
                        "directories": platform_directories,
                        "scan_subdirectories": platform_settings.get("scan_subdirectories", True),
                        "handle_archives": platform_settings.get("handle_archives", True),
                        "supported_formats": platform_settings.get(
                            "supported_formats", platform.get_supported_handlers()
                        ),
                        "supported_archives": platform_settings.get(
                            "supported_archives", platform.get_archive_content_extensions()
                        ),
                    }
                )
                total_directories += len(platform_directories)

        # Don't scan if no directories are configured for any platform
        if not platform_configs:
            if self._toolbar_manager:
                self._toolbar_manager.update_status(
                    "No ROM directories configured for any platform. Check Settings."
                )
            return

        # Stop any existing scan
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.quit()
            self._scanner_thread.wait()

        # Clear existing ROMs
        self.clear_rom_entries()

        # Update status
        platform_count = len(platform_configs)
        if self._toolbar_manager:
            self._toolbar_manager.update_status(
                f"Scanning {total_directories} directories across {platform_count} platforms..."
            )

        # Start new scan with platform-specific configurations
        self._scanner_thread = ROMScannerThread(platform_configs)

        # Connect scanner signals
        self._scanner_thread.scanner.rom_found.connect(self._on_rom_found)
        self._scanner_thread.scanner.scan_completed.connect(self._on_scan_completed)
        self._scanner_thread.scanner.scan_error.connect(self._on_scan_error)
        self._scanner_thread.scanner.progress_updated.connect(self._on_scan_progress)

        # Clear existing ROMs before starting new scan
        if self._rom_model:
            self._rom_model.set_rom_entries([])

        # Reset progress tracking
        self._last_progress_update = 0
        self._current_progress_percentage = 0

        # Show progress bar
        if self._toolbar_manager:
            self._toolbar_manager.show_progress_bar()

        # Start scanning
        self._scanner_thread.start()
        self.logger.info(
            f"Started scanning {total_directories} directories across {platform_count} platforms..."
        )

    def _on_rom_found(self, rom_entry) -> None:
        """Handle a ROM being found during scan."""
        self.logger.debug(f"Found ROM: {rom_entry.display_name} ({rom_entry.platform_id})")
        self.add_rom_entries([rom_entry])

    def _on_scan_completed(self, all_entries) -> None:
        """Handle scan completion."""
        self.logger.info(f"Scan completed. Found {len(all_entries)} total ROMs.")

        if self._toolbar_manager:
            # Set to 100% to show completion before hiding
            self._toolbar_manager.update_progress(100)
            self._current_progress_percentage = 100
            self.logger.debug("Progress: Scan completed (100%)")

            # Brief delay to show 100% before hiding
            self._toolbar_manager.hide_progress_bar()
            self._toolbar_manager.update_status(f"Scan completed. Found {len(all_entries)} ROMs.")

        # Clean up scanner thread properly
        if self._scanner_thread:
            self._scanner_thread.quit()
            self._scanner_thread.wait()
            self._scanner_thread.deleteLater()
            self._scanner_thread = None

    def _on_scan_error(self, error_msg) -> None:
        """Handle scan errors."""
        self.logger.error(f"Scan error: {error_msg}")

        if self._toolbar_manager:
            self._toolbar_manager.hide_progress_bar()
            self._toolbar_manager.update_status(f"Scan error: {error_msg}")

        # Clean up scanner thread properly
        if self._scanner_thread:
            self._scanner_thread.quit()
            self._scanner_thread.wait()
            self._scanner_thread.deleteLater()
            self._scanner_thread = None

    def _on_scan_progress(self, progress) -> None:
        """Handle scan progress updates."""
        if not self._toolbar_manager:
            return

        # Check if this is a RetroAchievements update
        if hasattr(progress, "ra_event_type") and progress.ra_event_type:
            if progress.ra_event_type == "ra_update":
                # Downloading RA database
                self._toolbar_manager.update_scan_details(
                    operation=progress.ra_message,
                    detail_message=progress.ra_message,
                    message_type="info",
                )
            elif progress.ra_event_type == "ra_download":
                # Download progress with speed
                self._toolbar_manager.update_download_progress(
                    progress.ra_download_bytes,
                    progress.ra_download_total,
                    progress.ra_download_speed,
                )
            elif progress.ra_event_type == "ra_complete":
                # RA database download complete
                self._toolbar_manager.update_scan_details(
                    detail_message=progress.ra_message, message_type="success"
                )
            elif progress.ra_event_type == "ra_match":
                # Found an RA match
                self._toolbar_manager.increment_ra_matches()
                self._toolbar_manager.update_scan_details(
                    detail_message=f"Matched: {progress.ra_message}", message_type="success"
                )
            return

        # Throttle regular updates - only update UI every 5 files to prevent freezing
        should_update_ui = (
            progress.files_processed == 1  # First file
            or progress.files_processed % 5 == 0  # Every 5 files
            or progress.files_processed >= progress.total_files  # Last file
            or progress.files_processed - self._last_progress_update
            >= 10  # Force update every 10 files
        )

        if not should_update_ui:
            return

        self._last_progress_update = progress.files_processed

        # Update progress bar
        if progress.total_files > 0 and progress.files_processed <= progress.total_files:
            # Scale file processing to 95% max, reserve 5% for completion
            file_progress = (progress.files_processed / progress.total_files) * 95
            percentage = int(file_progress)

            # Only update if progress has actually increased
            if percentage > self._current_progress_percentage:
                # Ensure we're in determinate mode before updating (only once)
                if self._current_progress_percentage == 0:
                    self._toolbar_manager.set_progress_indeterminate(False)

                # Debug output first
                self.logger.debug(
                    f"Progress: {progress.files_processed}/{progress.total_files} ({percentage}%)"
                )

                # Update progress bar with new percentage
                self._toolbar_manager.update_progress(percentage)
                self._current_progress_percentage = percentage
        else:
            # If we don't have total yet or something is wrong, show indeterminate progress
            if progress.total_files == 0:
                self.logger.debug(f"Files processed: {progress.files_processed} (total unknown)")
            if self._current_progress_percentage == 0:  # Only set indeterminate once
                self._toolbar_manager.set_progress_indeterminate(True)

        # Update detailed scan information
        if progress.current_file:
            file_name = progress.current_file.split("/")[-1].split("\\")[-1]
        else:
            file_name = None

        # Create operation string with platform if available
        operation = "Scanning ROM files"
        if hasattr(progress, "current_platform") and progress.current_platform:
            operation = f"Scanning {progress.current_platform}"

        self._toolbar_manager.update_scan_details(
            operation=operation,
            current_file=progress.current_file,
            files_processed=progress.files_processed,
            total_files=progress.total_files,
            roms_found=progress.rom_entries_found,
        )

        # Update status message (compact view)
        if file_name and progress.total_files > 0:
            self._toolbar_manager.update_status(
                f"Scanning: {file_name} ({progress.files_processed}/{progress.total_files})"
            )
        else:
            self._toolbar_manager.update_status(f"Files processed: {progress.files_processed}")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for menu bar visibility."""
        if event.key() == Qt.Key.Key_Alt:
            if not self._menu_visible:
                self.menuBar().setVisible(True)
                self._menu_visible = True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release events for menu bar visibility."""
        if event.key() == Qt.Key.Key_Alt:
            if self._menu_visible:
                self.menuBar().setVisible(False)
                self._menu_visible = False
        super().keyReleaseEvent(event)

    def closeEvent(self, event) -> None:
        """Handle application close event."""
        # Stop scanner thread if running
        if self._scanner_thread:
            if self._scanner_thread.isRunning():
                self.logger.info("Stopping ROM scanner thread...")
                self._scanner_thread.scanner.stop_scan()
                self._scanner_thread.quit()
                self._scanner_thread.wait(5000)  # Wait up to 5 seconds
                if self._scanner_thread.isRunning():
                    self.logger.warning("Thread didn't stop gracefully, terminating...")
                    self._scanner_thread.terminate()
                    self._scanner_thread.wait(1000)  # Wait 1 more second after terminate

            # Clean up thread object
            self._scanner_thread.deleteLater()
            self._scanner_thread = None

        event.accept()

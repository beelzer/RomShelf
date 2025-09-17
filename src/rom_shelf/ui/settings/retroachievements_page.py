"""RetroAchievements settings page with cache management."""

import logging
import time

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...services.retroachievements_service import RetroAchievementsService
from ..widgets.compact_button import TableCellButton


class CacheUpdateDialog(QDialog):
    """Custom dialog for cache update operations with multiple states."""

    def __init__(self, parent=None, title="Update Cache", is_update_all=False, total_count=0):
        super().__init__(parent)
        self.is_update_all = is_update_all
        self.total_count = total_count
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        # Main layout
        layout = QVBoxLayout(self)

        # Stacked widget for different states
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background-color: transparent; }")
        layout.addWidget(self.stack)

        # Confirmation page
        self.confirm_widget = QWidget()
        self.confirm_widget.setStyleSheet("background-color: transparent;")
        confirm_layout = QVBoxLayout(self.confirm_widget)

        if is_update_all:
            self.confirm_label = QLabel(
                f"This will update {total_count} platform cache{'s' if total_count != 1 else ''}.\n"
                "This may take several minutes depending on your connection.\n\n"
                "Continue?"
            )
        else:
            self.confirm_label = QLabel("Update cache for this platform?")

        # Ensure label has transparent background
        self.confirm_label.setStyleSheet("background-color: transparent;")
        confirm_layout.addWidget(self.confirm_label)
        confirm_layout.addStretch()

        # Confirmation buttons
        confirm_buttons = QDialogButtonBox()
        self.update_btn = confirm_buttons.addButton(
            "Update", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.cancel_btn = confirm_buttons.addButton(
            "Cancel", QDialogButtonBox.ButtonRole.RejectRole
        )
        confirm_layout.addWidget(confirm_buttons)

        self.stack.addWidget(self.confirm_widget)

        # Progress page
        self.progress_widget = QWidget()
        self.progress_widget.setStyleSheet("background-color: transparent;")
        progress_layout = QVBoxLayout(self.progress_widget)

        self.progress_label = QLabel("Preparing update...")
        self.progress_label.setStyleSheet("background-color: transparent;")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        # Download speed label
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("background-color: transparent; color: #4CAF50;")
        progress_layout.addWidget(self.speed_label)

        progress_layout.addStretch()

        self.stack.addWidget(self.progress_widget)

        # Result page
        self.result_widget = QWidget()
        self.result_widget.setStyleSheet("background-color: transparent;")
        result_layout = QVBoxLayout(self.result_widget)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("background-color: transparent;")
        result_layout.addWidget(self.result_label)
        result_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        result_layout.addWidget(self.close_btn)

        self.stack.addWidget(self.result_widget)

        # Connect buttons
        self.update_btn.clicked.connect(self.start_update)
        self.cancel_btn.clicked.connect(self.reject)

        # Start with confirmation page
        self.stack.setCurrentWidget(self.confirm_widget)

    def start_update(self):
        """Switch to progress view and emit signal to start update."""
        self.stack.setCurrentWidget(self.progress_widget)
        if self.is_update_all:
            self.progress_bar.setMaximum(self.total_count)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate

    def update_progress(self, current: int, message: str):
        """Update progress display."""
        self.progress_label.setText(message)
        if self.is_update_all:
            self.progress_bar.setValue(current)

    def update_download_speed(
        self, speed_bps: float, bytes_downloaded: int = 0, total_bytes: int = 0
    ):
        """Update download speed display."""
        if speed_bps == 0 and bytes_downloaded == 0:
            self.speed_label.setText("Starting download...")
        elif speed_bps > 0:
            # Format speed
            if speed_bps > 1024 * 1024:
                speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s"
            elif speed_bps > 1024:
                speed_str = f"{speed_bps / 1024:.1f} KB/s"
            else:
                speed_str = f"{speed_bps:.0f} B/s"

            # Add progress if available
            if total_bytes > 0:
                progress_pct = (bytes_downloaded / total_bytes) * 100
                self.speed_label.setText(f"Downloading: {progress_pct:.0f}% @ {speed_str}")
            elif bytes_downloaded > 0:
                mb_downloaded = bytes_downloaded / (1024 * 1024)
                self.speed_label.setText(f"Downloaded: {mb_downloaded:.1f} MB @ {speed_str}")
            else:
                self.speed_label.setText(f"Download speed: {speed_str}")
        else:
            self.speed_label.setText("")

    def show_result(self, success: bool, message: str):
        """Show the result page."""
        self.result_label.setText(message)
        self.speed_label.setText("")  # Clear speed display
        self.stack.setCurrentWidget(self.result_widget)

        # Auto-close after delay for success
        if success:
            QTimer.singleShot(2000, self.accept)


class UpdateThread(QThread):
    """Thread for updating platform cache."""

    finished_signal = Signal(bool, str)
    progress_signal = Signal(dict)  # For download progress

    def __init__(self, ra_service: RetroAchievementsService, console_id: int):
        super().__init__()
        self.ra_service = ra_service
        self.console_id = console_id

    def run(self):
        """Run the update."""
        try:
            # Set progress callback
            self.ra_service.set_progress_callback(self._handle_progress)

            success = self.ra_service.force_update_console(self.console_id)
            if success:
                self.finished_signal.emit(True, "Cache updated successfully")
            else:
                self.finished_signal.emit(False, "Failed to update cache")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            # Clear callback
            self.ra_service.set_progress_callback(None)

    def _handle_progress(self, event_type: str, data: dict):
        """Handle progress callbacks from RA service."""
        if event_type == "ra_download":
            self.progress_signal.emit(data)


class UpdateAllThread(QThread):
    """Thread for updating all platform caches."""

    progress_signal = Signal(int, str)  # current index, status message
    download_signal = Signal(dict)  # download progress data
    finished_signal = Signal(int, int)  # successful count, total count

    def __init__(self, ra_service: RetroAchievementsService, console_ids: list):
        super().__init__()
        self.ra_service = ra_service
        self.console_ids = console_ids

    def run(self):
        """Run the updates."""
        successful = 0
        for i, console_id in enumerate(self.console_ids):
            console_name = self.ra_service._get_console_name(console_id)
            self.progress_signal.emit(
                i, f"Updating {console_name}... ({i+1}/{len(self.console_ids)})"
            )

            try:
                # Set progress callback
                self.ra_service.set_progress_callback(self._handle_progress)

                success = self.ra_service.force_update_console(console_id)
                if success:
                    successful += 1
            except Exception as e:
                pass  # Continue with next console
            finally:
                # Clear callback
                self.ra_service.set_progress_callback(None)

        self.finished_signal.emit(successful, len(self.console_ids))

    def _handle_progress(self, event_type: str, data: dict):
        """Handle progress callbacks from RA service."""
        if event_type == "ra_download":
            self.download_signal.emit(data)


class RetroAchievementsPage(QWidget):
    """Settings page for RetroAchievements configuration and cache management."""

    # Signal emitted when settings are changed
    settings_changed = Signal()

    def __init__(self, settings_manager):
        """Initialize the RetroAchievements page."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._settings_manager = settings_manager
        self._ra_service = None
        self._update_thread = None
        self._update_all_thread = None
        self._setup_ui()
        self._refresh_cache_table()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # API Configuration
        api_group = QGroupBox("API Configuration")
        api_layout = QVBoxLayout(api_group)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("Your RetroAchievements username")
        self._username_edit.textChanged.connect(lambda: self.settings_changed.emit())
        username_layout.addWidget(self._username_edit)
        api_layout.addLayout(username_layout)

        # API Key
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("API Key:"))
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("Your RetroAchievements API key")
        self._api_key_edit.textChanged.connect(lambda: self.settings_changed.emit())
        api_key_layout.addWidget(self._api_key_edit)

        # Toggle visibility button
        self._toggle_key_btn = QPushButton("Show")
        self._toggle_key_btn.setMaximumWidth(60)
        self._toggle_key_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_layout.addWidget(self._toggle_key_btn)

        api_layout.addLayout(api_key_layout)

        # Test connection button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self._test_btn = QPushButton("Test Connection")
        self._test_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self._test_btn)
        api_layout.addLayout(test_layout)

        # Info label
        info_label = QLabel(
            "Get your API key from: "
            '<a href="https://retroachievements.org/controlpanel.php">RetroAchievements Control Panel</a>'
        )
        info_label.setOpenExternalLinks(True)
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        api_layout.addWidget(info_label)

        layout.addWidget(api_group)

        # Cache Management
        cache_group = QGroupBox("Cache Management")
        cache_layout = QVBoxLayout(cache_group)

        # Cache info
        self._cache_info_label = QLabel("Cache Size: Calculating...")
        cache_layout.addWidget(self._cache_info_label)

        # Platform cache table
        self._cache_table = QTableWidget()
        self._cache_table.setColumnCount(6)
        self._cache_table.setHorizontalHeaderLabels(
            ["Platform", "Games", "Last Updated", "Progress Sync", "Update", "Sync Progress"]
        )
        self._cache_table.horizontalHeader().setStretchLastSection(False)
        self._cache_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._cache_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._cache_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._cache_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._cache_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._cache_table.setColumnWidth(4, 70)  # Update button column
        self._cache_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._cache_table.setColumnWidth(5, 90)  # Sync Progress button column
        self._cache_table.setAlternatingRowColors(True)
        self._cache_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._cache_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._cache_table.verticalHeader().setDefaultSectionSize(26)  # Slightly larger for button
        self._cache_table.verticalHeader().setVisible(False)  # Hide row numbers to save space

        # Remove cell padding/margins with custom stylesheet
        self._cache_table.setStyleSheet("""
            QTableWidget::item {
                padding: 1px;
                margin: 0px;
            }
            QTableWidget {
                gridline-color: rgba(255, 255, 255, 0.1);
            }
        """)
        cache_layout.addWidget(self._cache_table)

        # Cache actions
        cache_actions_layout = QHBoxLayout()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_cache_table)
        cache_actions_layout.addWidget(self._refresh_btn)

        self._update_all_btn = QPushButton("Update All")
        self._update_all_btn.clicked.connect(self._update_all_caches)
        cache_actions_layout.addWidget(self._update_all_btn)

        self._sync_progress_btn = QPushButton("Sync Progress")
        self._sync_progress_btn.clicked.connect(self._sync_user_progress)
        cache_actions_layout.addWidget(self._sync_progress_btn)

        cache_actions_layout.addStretch()

        self._clear_cache_btn = QPushButton("Clear All Caches")
        self._clear_cache_btn.setStyleSheet("QPushButton { color: #ff6b6b; }")
        self._clear_cache_btn.clicked.connect(self._clear_all_caches)
        cache_actions_layout.addWidget(self._clear_cache_btn)

        cache_layout.addLayout(cache_actions_layout)

        layout.addWidget(cache_group)

        # Add stretch at bottom
        layout.addStretch()

    def _test_connection(self):
        """Test the RetroAchievements API connection."""
        username = self._username_edit.text().strip()
        api_key = self._api_key_edit.text().strip()

        if not username or not api_key:
            QMessageBox.warning(
                self, "Missing Credentials", "Please enter both username and API key."
            )
            return

        # Create a temporary RA service with the current credentials
        from ...core.settings import Settings

        temp_settings = Settings()
        temp_settings.retroachievements_username = username
        temp_settings.retroachievements_api_key = api_key

        try:
            test_service = RetroAchievementsService(temp_settings)

            # Try a simple API call to test the connection
            # We'll use get_game_info with a known game ID
            test_result = test_service.get_game_info(1)  # Super Mario Bros. (NES)

            if test_result:
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to RetroAchievements as {username}!\n\n"
                    "Your API key is valid and working.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    "Could not connect to RetroAchievements.\n\n"
                    "Please check your API key is correct.",
                )
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error testing connection:\n{str(e)}")

    def _toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        if self._api_key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_key_btn.setText("Hide")
        else:
            self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_key_btn.setText("Show")

    def _get_progress_sync_info(self) -> dict:
        """Get progress sync information for platforms."""
        try:
            from pathlib import Path

            from ...core.rom_database import get_rom_database
            from ...services.ra_database import RetroAchievementsDatabase

            ra_db_path = Path("data/retroachievements.db")
            if not ra_db_path.exists():
                return {}

            ra_db = RetroAchievementsDatabase(ra_db_path)
            rom_db = get_rom_database()

            # Get latest progress sync timestamp for each platform
            progress_info = {}

            # Check if we have a configured username
            settings = self._settings_manager.settings
            if not settings.ra_username:
                return {}

            # Get all games with RA data grouped by platform
            with rom_db.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT platform, ra_game_id
                    FROM rom_fingerprints
                    WHERE ra_game_id IS NOT NULL
                """)
                results = cursor.fetchall()

                platform_games = {}
                for row in results:
                    platform = row[0].lower()  # Normalize platform name to lowercase
                    game_id = row[1]
                    if platform not in platform_games:
                        platform_games[platform] = set()
                    platform_games[platform].add(game_id)

                self.logger.debug(f"Found RA games for platforms: {list(platform_games.keys())}")

            # Get progress sync status for each platform
            for platform, game_ids in platform_games.items():
                synced_games = 0
                latest_sync = 0

                for game_id in game_ids:
                    progress = ra_db.get_user_game_progress(settings.ra_username, game_id)
                    if progress:
                        synced_games += 1
                        last_updated = progress.get("last_updated", 0)
                        latest_sync = max(latest_sync, last_updated)

                progress_info[platform] = {
                    "total_games": len(game_ids),
                    "synced_games": synced_games,
                    "latest_sync": latest_sync,
                    "sync_percentage": (synced_games / len(game_ids) * 100) if game_ids else 0,
                }

                self.logger.debug(
                    f"Platform {platform}: {synced_games}/{len(game_ids)} games synced"
                )

            self.logger.debug(f"Progress info: {progress_info}")
            self.logger.info(
                f"Generated progress sync info for {len(progress_info)} platforms: {list(progress_info.keys())}"
            )
            return progress_info

        except Exception as e:
            self.logger.error(f"Failed to get progress sync info: {e}")
            return {}

    def _refresh_cache_table(self):
        """Refresh the cache statistics table."""
        try:
            # Initialize RA service if needed
            if not self._ra_service:
                self._ra_service = RetroAchievementsService(self._settings_manager.settings)

            # Get cache statistics
            stats = self._ra_service.get_cache_statistics()
            total_size, size_str = self._ra_service.get_total_cache_size()

            # Update cache size label
            self._cache_info_label.setText(f"Cache Size: {size_str}")

            # Get list of all supported platforms
            all_platforms = self._ra_service.get_all_supported_platforms()

            # Get progress sync information
            progress_sync_info = self._get_progress_sync_info()

            # Combine cached and uncached platforms
            all_platform_stats = {}

            # Add cached platforms
            for console_id, info in stats.items():
                all_platform_stats[console_id] = info

            # Add uncached platforms
            for console_id, name in all_platforms.items():
                if console_id not in all_platform_stats:
                    all_platform_stats[console_id] = {
                        "name": name,
                        "game_count": 0,
                        "last_updated": 0,
                        "age_string": "Never",
                        "age_days": float("inf"),
                    }

            # Update table
            self._cache_table.setRowCount(len(all_platform_stats))
            row = 0

            # Sort by console name
            sorted_platforms = sorted(all_platform_stats.items(), key=lambda x: x[1]["name"])

            for console_id, info in sorted_platforms:
                # Platform name
                name_item = QTableWidgetItem(info["name"])
                self._cache_table.setItem(row, 0, name_item)

                # Game count
                count_item = QTableWidgetItem(str(info["game_count"]))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._cache_table.setItem(row, 1, count_item)

                # Last updated
                age_item = QTableWidgetItem(info["age_string"])
                age_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color code by age
                if info["age_string"] == "Never":
                    age_item.setForeground(Qt.GlobalColor.gray)
                elif info["age_days"] < 7:
                    age_item.setForeground(Qt.GlobalColor.green)
                elif info["age_days"] < 30:
                    age_item.setForeground(Qt.GlobalColor.yellow)
                else:
                    age_item.setForeground(Qt.GlobalColor.red)

                self._cache_table.setItem(row, 2, age_item)

                # Progress sync status (column 3)
                # Map console names to database platform names
                platform_mapping = {
                    "game boy": "gameboy",
                    "game boy advance": "gba",
                    "game boy color": "gbc",
                    "genesis/mega drive": "genesis",
                    "nintendo 64": "n64",
                    "snes": "snes",
                    "nes": "nes",
                    "master system": "mastersystem",
                    "playstation": "psx",
                    "neo geo": "neogeo",
                    "game gear": "gamegear",
                    "nintendo ds": "nds",
                    "playstation 2": "ps2",
                    "arcade": "arcade",
                    "playstation portable": "psp",
                }

                platform_key = platform_mapping.get(info["name"].lower(), info["name"].lower())
                progress_info = progress_sync_info.get(platform_key, {})

                if progress_info:
                    synced = progress_info.get("synced_games", 0)
                    total = progress_info.get("total_games", 0)
                    percentage = progress_info.get("sync_percentage", 0)

                    if total > 0:
                        progress_text = f"{synced}/{total} ({percentage:.0f}%)"
                        progress_item = QTableWidgetItem(progress_text)

                        # Color code by sync percentage
                        if percentage >= 100:
                            progress_item.setForeground(Qt.GlobalColor.green)
                        elif percentage >= 50:
                            progress_item.setForeground(Qt.GlobalColor.yellow)
                        elif percentage > 0:
                            progress_item.setForeground(Qt.GlobalColor.red)
                        else:
                            progress_item.setForeground(Qt.GlobalColor.gray)
                    else:
                        progress_item = QTableWidgetItem("No RA games")
                        progress_item.setForeground(Qt.GlobalColor.gray)
                else:
                    progress_item = QTableWidgetItem("No RA games")
                    progress_item.setForeground(Qt.GlobalColor.gray)

                progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._cache_table.setItem(row, 3, progress_item)

                # Update button (column 4)
                update_cell_widget = QWidget()
                update_cell_layout = QHBoxLayout(update_cell_widget)
                update_cell_layout.setContentsMargins(0, 0, 0, 0)
                update_cell_layout.setSpacing(0)

                update_btn = TableCellButton("Update")
                update_btn.clicked.connect(
                    lambda checked, cid=console_id: self._update_platform_cache(cid)
                )
                update_cell_layout.addWidget(update_btn)
                self._cache_table.setCellWidget(row, 4, update_cell_widget)

                # Sync Progress button (column 5)
                sync_cell_widget = QWidget()
                sync_cell_layout = QHBoxLayout(sync_cell_widget)
                sync_cell_layout.setContentsMargins(0, 0, 0, 0)
                sync_cell_layout.setSpacing(0)

                sync_btn = TableCellButton("Sync")
                sync_btn.clicked.connect(
                    lambda checked, platform=platform_key: self._sync_platform_progress(platform)
                )
                # Disable if no RA games for this platform
                if not progress_info or progress_info.get("total_games", 0) == 0:
                    sync_btn.setEnabled(False)

                sync_cell_layout.addWidget(sync_btn)
                self._cache_table.setCellWidget(row, 5, sync_cell_widget)

                row += 1

            # Show message if no platforms available
            if len(all_platform_stats) == 0:
                self._cache_table.setRowCount(1)
                empty_item = QTableWidgetItem("No platforms configured")
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._cache_table.setItem(0, 0, empty_item)
                self._cache_table.setSpan(0, 0, 1, 6)  # Updated for 6 columns

        except Exception as e:
            self.logger.error(f"Failed to refresh cache table: {e}")

    def _update_platform_cache(self, console_id: int):
        """Update cache for a specific platform."""
        if self._update_thread and self._update_thread.isRunning():
            QMessageBox.warning(
                self, "Update in Progress", "Another update is already in progress."
            )
            return

        # Get console name for display
        if not self._ra_service:
            self._ra_service = RetroAchievementsService(self._settings_manager.settings)

        console_name = self._ra_service._get_console_name(console_id)

        # Create custom dialog
        self._update_dialog = CacheUpdateDialog(self, f"Update {console_name} Cache")
        self._update_dialog.confirm_label.setText(
            f"Update cache for {console_name}?\n\nThis may take a few moments."
        )

        # Connect the update button to start the thread
        self._update_dialog.update_btn.clicked.disconnect()  # Remove default connection
        self._update_dialog.update_btn.clicked.connect(
            lambda: self._start_single_update(console_id)
        )

        # Show dialog
        result = self._update_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self._refresh_cache_table()

    def _start_single_update(self, console_id: int):
        """Start the single platform update."""
        self._update_dialog.start_update()
        console_name = self._ra_service._get_console_name(console_id)
        self._update_dialog.update_progress(0, f"Updating {console_name} cache...")

        # Start update thread
        self._update_thread = UpdateThread(self._ra_service, console_id)
        self._update_thread.finished_signal.connect(self._on_single_update_finished)
        self._update_thread.progress_signal.connect(self._on_single_download_progress)
        self._update_thread.start()

    def _on_single_download_progress(self, data: dict):
        """Handle download progress for single update."""
        if hasattr(self, "_update_dialog") and self._update_dialog:
            speed = data.get("speed", 0)
            bytes_downloaded = data.get("bytes", 0)
            total_bytes = data.get("total", 0)
            self._update_dialog.update_download_speed(speed, bytes_downloaded, total_bytes)

    def _on_single_update_finished(self, success: bool, message: str):
        """Handle single update completion."""
        if success:
            self._update_dialog.show_result(True, "Cache updated successfully!")
        else:
            self._update_dialog.show_result(False, f"Update failed: {message}")
        self._update_thread = None

    def _update_all_caches(self):
        """Update all platform caches."""
        if (self._update_thread and self._update_thread.isRunning()) or (
            self._update_all_thread and self._update_all_thread.isRunning()
        ):
            QMessageBox.warning(
                self, "Update in Progress", "Another update is already in progress."
            )
            return

        if not self._ra_service:
            self._ra_service = RetroAchievementsService(self._settings_manager.settings)

        # Get all supported platforms
        all_platforms = self._ra_service.get_all_supported_platforms()
        if not all_platforms:
            QMessageBox.information(self, "No Platforms", "No platforms available to update.")
            return

        self._console_ids = list(all_platforms.keys())
        total = len(self._console_ids)

        # Create custom dialog for update all
        self._update_all_dialog = CacheUpdateDialog(
            self, "Update All Caches", is_update_all=True, total_count=total
        )

        # Connect the update button to start the thread
        self._update_all_dialog.update_btn.clicked.disconnect()  # Remove default connection
        self._update_all_dialog.update_btn.clicked.connect(self._start_update_all)

        # Show dialog
        result = self._update_all_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self._refresh_cache_table()

    def _start_update_all(self):
        """Start the update all process."""
        self._update_all_dialog.start_update()

        # Start update thread
        self._update_all_thread = UpdateAllThread(self._ra_service, self._console_ids)
        self._update_all_thread.progress_signal.connect(self._on_update_all_progress)
        self._update_all_thread.download_signal.connect(self._on_update_all_download_progress)
        self._update_all_thread.finished_signal.connect(self._on_update_all_finished)
        self._update_all_thread.start()

    def _on_update_all_progress(self, current: int, message: str):
        """Handle progress updates from update all thread."""
        if hasattr(self, "_update_all_dialog") and self._update_all_dialog:
            self._update_all_dialog.update_progress(current, message)

    def _on_update_all_download_progress(self, data: dict):
        """Handle download progress for update all."""
        if hasattr(self, "_update_all_dialog") and self._update_all_dialog:
            speed = data.get("speed", 0)
            bytes_downloaded = data.get("bytes", 0)
            total_bytes = data.get("total", 0)
            self._update_all_dialog.update_download_speed(speed, bytes_downloaded, total_bytes)

    def _on_update_all_finished(self, successful: int, total: int):
        """Handle update all completion."""
        if hasattr(self, "_update_all_dialog") and self._update_all_dialog:
            if successful == total:
                message = (
                    f"Successfully updated all {total} platform cache{'s' if total != 1 else ''}!"
                )
                self._update_all_dialog.show_result(True, message)
            else:
                message = (
                    f"Updated {successful} of {total} platform caches.\n\n"
                    f"{total - successful} cache{'s' if (total - successful) != 1 else ''} failed to update."
                )
                self._update_all_dialog.show_result(False, message)

        self._update_all_thread = None

    def _clear_all_caches(self):
        """Clear all RetroAchievements caches."""
        reply = QMessageBox.question(
            self,
            "Clear Caches",
            "This will remove all downloaded RetroAchievements data.\n"
            "The data will be re-downloaded as needed during ROM scanning.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if not self._ra_service:
                self._ra_service = RetroAchievementsService(self._settings_manager.settings)

            self._ra_service.clear_cache()
            QMessageBox.information(
                self, "Caches Cleared", "All RetroAchievements caches have been cleared."
            )
            self._refresh_cache_table()

    def _sync_user_progress(self):
        """Sync user achievement progress for all games with RA data."""
        # Check if username and API key are configured
        settings = self._settings_manager.settings
        if not settings.ra_username:
            QMessageBox.warning(
                self, "Username Required", "Please configure your RetroAchievements username first."
            )
            return

        if not settings.ra_api_key:
            QMessageBox.warning(
                self, "API Key Required", "Please configure your RetroAchievements API key first."
            )
            return

        # Check if any operations are running
        if (self._update_thread and self._update_thread.isRunning()) or (
            self._update_all_thread and self._update_all_thread.isRunning()
        ):
            QMessageBox.warning(
                self, "Operation in Progress", "Please wait for current operations to complete."
            )
            return

        # Get all games with RA data
        try:
            from ...core.rom_database import get_rom_database

            rom_db = get_rom_database()

            # Get all fingerprints with RA game IDs
            with rom_db.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT ra_game_id FROM rom_fingerprints WHERE ra_game_id IS NOT NULL"
                )
                results = cursor.fetchall()
                game_ids = [row[0] for row in results]

            if not game_ids:
                QMessageBox.information(
                    self,
                    "No Games Found",
                    "No games with RetroAchievements data found.\n"
                    "Please scan your ROMs first and ensure platform caches are updated.",
                )
                return

            # Confirm sync
            reply = QMessageBox.question(
                self,
                "Sync Progress",
                f"This will fetch achievement progress for {len(game_ids)} game{'s' if len(game_ids) != 1 else ''}.\n"
                f"This may take a few minutes depending on your connection.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Create progress dialog
                self._progress_dialog = CacheUpdateDialog(
                    self, "Sync User Progress", is_update_all=True, total_count=len(game_ids)
                )

                # Update the text for progress sync
                self._progress_dialog.confirm_label.setText(
                    f"This will sync achievement progress for {len(game_ids)} game{'s' if len(game_ids) != 1 else ''}.\n"
                    "This may take a few minutes depending on your connection.\n\n"
                    "Continue?"
                )
                self._progress_dialog.update_btn.setText("Sync")

                # Disconnect default connections and set up sync-specific ones
                self._progress_dialog.update_btn.clicked.disconnect()
                self._progress_dialog.cancel_btn.clicked.disconnect()

                self._progress_dialog.update_btn.clicked.connect(
                    lambda: self._start_progress_sync(game_ids)
                )
                self._progress_dialog.cancel_btn.clicked.connect(self._progress_dialog.reject)

                self._progress_dialog.show()

        except Exception as e:
            self.logger.error(f"Error preparing progress sync: {e}")
            QMessageBox.critical(self, "Error", f"Failed to prepare progress sync: {str(e)}")

    def _start_progress_sync(self, game_ids):
        """Start the progress sync in a separate thread."""
        self._progress_dialog.start_update()

        # Create and start sync thread
        self._sync_thread = ProgressSyncThread(self._settings_manager.settings, game_ids)
        self._sync_thread.progress_updated.connect(self._on_sync_progress_update)
        self._sync_thread.finished.connect(self._on_progress_sync_finished)
        self._sync_thread.start()

    def _on_sync_progress_update(self, message, current, total, speed, bytes_val):
        """Adapter method to convert ProgressSyncThread signals to dialog format."""
        self._progress_dialog.update_progress(current, message)

        # Update download speed display with games per second
        if speed > 0:
            speed_text = f"Syncing: {speed:.1f} games/sec"
            self._progress_dialog.update_download_speed(0, 0, 0)  # Clear download info
            self._progress_dialog.speed_label.setText(speed_text)

    def _on_progress_sync_finished(self, success, message, synced_count, total_count):
        """Handle progress sync completion."""
        if success:
            self._progress_dialog.show_result(
                True, f"Successfully synced progress for {synced_count} out of {total_count} games."
            )
        else:
            self._progress_dialog.show_result(False, message)

        self._sync_thread = None

    def _sync_platform_progress(self, platform_name: str):
        """Sync progress for games from a specific platform."""
        # Check if username and API key are configured
        settings = self._settings_manager.settings
        if not settings.ra_username:
            QMessageBox.warning(
                self, "Username Required", "Please configure your RetroAchievements username first."
            )
            return

        if not settings.ra_api_key:
            QMessageBox.warning(
                self, "API Key Required", "Please configure your RetroAchievements API key first."
            )
            return

        # Check if any operations are running
        if (self._update_thread and self._update_thread.isRunning()) or (
            self._update_all_thread and self._update_all_thread.isRunning()
        ):
            QMessageBox.warning(
                self, "Operation in Progress", "Please wait for current operations to complete."
            )
            return

        # Get games for this platform with RA data
        try:
            from ...core.rom_database import get_rom_database

            rom_db = get_rom_database()

            # Get all fingerprints with RA game IDs for this platform
            with rom_db.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT ra_game_id FROM rom_fingerprints WHERE platform = ? AND ra_game_id IS NOT NULL",
                    (platform_name,),
                )
                results = cursor.fetchall()
                game_ids = [row[0] for row in results]

            if not game_ids:
                QMessageBox.information(
                    self,
                    "No Games Found",
                    f"No games with RetroAchievements data found for {platform_name.title()}.",
                )
                return

            # Confirm sync
            reply = QMessageBox.question(
                self,
                "Sync Platform Progress",
                f"This will sync achievement progress for {len(game_ids)} {platform_name.title()} game{'s' if len(game_ids) != 1 else ''}.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Create progress dialog
                self._progress_dialog = CacheUpdateDialog(
                    self,
                    f"Sync {platform_name.title()} Progress",
                    is_update_all=True,
                    total_count=len(game_ids),
                )

                # Update the text for progress sync
                self._progress_dialog.confirm_label.setText(
                    f"This will sync achievement progress for {len(game_ids)} {platform_name.title()} game{'s' if len(game_ids) != 1 else ''}.\n\n"
                    "Continue?"
                )
                self._progress_dialog.update_btn.setText("Sync")

                # Disconnect default connections and set up sync-specific ones
                self._progress_dialog.update_btn.clicked.disconnect()
                self._progress_dialog.cancel_btn.clicked.disconnect()

                self._progress_dialog.update_btn.clicked.connect(
                    lambda: self._start_platform_progress_sync(game_ids, platform_name)
                )
                self._progress_dialog.cancel_btn.clicked.connect(self._progress_dialog.reject)

                self._progress_dialog.show()

        except Exception as e:
            self.logger.error(f"Error preparing platform progress sync: {e}")
            QMessageBox.critical(self, "Error", f"Failed to prepare progress sync: {str(e)}")

    def _start_platform_progress_sync(self, game_ids, platform_name):
        """Start the platform progress sync in a separate thread."""
        self._progress_dialog.start_update()

        # Create and start sync thread
        self._sync_thread = ProgressSyncThread(self._settings_manager.settings, game_ids)
        self._sync_thread.progress_updated.connect(self._on_sync_progress_update)
        self._sync_thread.finished.connect(
            lambda success,
            message,
            synced_count,
            total_count: self._on_platform_progress_sync_finished(
                success, message, synced_count, total_count, platform_name
            )
        )
        self._sync_thread.start()

    def _on_platform_progress_sync_finished(
        self, success, message, synced_count, total_count, platform_name
    ):
        """Handle platform progress sync completion."""
        if success:
            self._progress_dialog.show_result(
                True,
                f"Successfully synced progress for {synced_count} out of {total_count} {platform_name.title()} games.",
            )
        else:
            self._progress_dialog.show_result(False, message)

        self._sync_thread = None
        # Refresh the cache table to show updated progress
        self._refresh_cache_table()

    def load_settings(self, settings):
        """Load settings from the settings object.

        Args:
            settings: Settings object to load from
        """
        self._username_edit.setText(settings.retroachievements_username or "")
        self._api_key_edit.setText(settings.retroachievements_api_key or "")

    def save_settings(self, settings):
        """Save settings to the settings object.

        Args:
            settings: Settings object to save to
        """
        settings.retroachievements_username = self._username_edit.text().strip() or None
        settings.retroachievements_api_key = self._api_key_edit.text().strip() or None

        # Reinitialize RA service with new settings
        self._ra_service = None
        self._refresh_cache_table()

    def apply_settings(self):
        """Apply the settings to the configuration."""
        settings = self._settings_manager.settings
        self.save_settings(settings)
        self._settings_manager.save_settings()


class ProgressSyncThread(QThread):
    """Thread for syncing user achievement progress."""

    progress_updated = Signal(str, int, int, float, float)  # message, current, total, speed, bytes
    finished = Signal(bool, str, int, int)  # success, message, synced_count, total_count

    def __init__(self, settings, game_ids):
        super().__init__()
        self.settings = settings
        self.game_ids = game_ids
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Run the progress sync operation."""
        try:
            ra_service = RetroAchievementsService(self.settings)
            synced_count = 0
            total_count = len(self.game_ids)
            start_time = time.time()

            # Get RA database to lookup game names
            from pathlib import Path

            from ...services.ra_database import RetroAchievementsDatabase

            ra_db_path = Path("data/retroachievements.db")
            ra_db = None
            if ra_db_path.exists():
                ra_db = RetroAchievementsDatabase(ra_db_path)

            # Use optimized batch sync method
            def progress_callback(current, total, message):
                # Calculate speed (games per second)
                elapsed = time.time() - start_time
                games_per_second = current / max(elapsed, 0.1) if current > 0 else 0

                # Update progress with speed info
                self.progress_updated.emit(
                    message,
                    current,
                    total,
                    games_per_second,  # Speed as games per second
                    float(current),  # Current count as bytes equivalent
                )

            # Use the optimized sync method (single API call + fast local processing)
            sync_results = ra_service.sync_all_user_progress_optimized(
                self.settings.ra_username, self.game_ids, progress_callback=progress_callback
            )

            synced_count = sync_results.get("synced", 0)

            # Emit completion
            self.finished.emit(True, "Progress sync completed", synced_count, total_count)

        except Exception as e:
            self.logger.error(f"Progress sync failed: {e}")
            self.finished.emit(False, f"Progress sync failed: {str(e)}", 0, len(self.game_ids))

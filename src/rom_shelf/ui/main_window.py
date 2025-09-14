"""Main window for the ROM Shelf application."""


from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTableView,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.rom_scanner import ROMScannerThread
from ..core.settings import SettingsManager
from ..models.rom_table_model import ROMTableModel
from ..platforms.platform_registry import platform_registry
from .settings_dialog import SettingsDialog
from .styles import DARK_STYLE, LIGHT_STYLE


class PlatformTreeWidget(QTreeWidget):
    """Custom tree widget for platform selection."""

    platform_selected = Signal(str)  # Selected platform ID

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the platform tree widget."""
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._setup_platforms()

        # Connect item selection changed
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def _setup_platforms(self) -> None:
        """Set up platform items."""
        self._platform_items = {}

        # Add "All Platforms" item first
        all_item = QTreeWidgetItem(self)
        all_item.setData(0, 32, "all")  # Store special "all" ID
        all_item.setText(0, "All Platforms (0)")
        self._platform_items["all"] = all_item

        # Add individual platform items
        for platform in platform_registry.get_all_platforms():
            item = QTreeWidgetItem(self)
            item.setData(0, 32, platform.platform_id)  # Store platform ID
            item.setText(0, f"{platform.name} (0)")
            self._platform_items[platform.platform_id] = item

        # Select "All Platforms" by default
        all_item.setSelected(True)

    def _on_selection_changed(self) -> None:
        """Handle item selection changes."""
        selected_items = self.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            platform_id = selected_item.data(0, 32)
            self.platform_selected.emit(platform_id)

    def update_rom_counts(self, rom_counts: dict) -> None:
        """Update the ROM count display for each platform."""
        total_count = sum(rom_counts.values())

        for platform_id, item in self._platform_items.items():
            if platform_id == "all":
                item.setText(0, f"All Platforms ({total_count})")
            else:
                count = rom_counts.get(platform_id, 0)
                platform = platform_registry.get_platform(platform_id)
                platform_name = platform.name if platform else platform_id
                item.setText(0, f"{platform_name} ({count})")

    def get_selected_platform(self) -> str:
        """Get the selected platform ID."""
        selected_items = self.selectedItems()
        if selected_items:
            return selected_items[0].data(0, 32)
        return "all"


class MainWindow(QMainWindow):
    """Main window for the ROM Shelf application."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        """Initialize the main window."""
        super().__init__()
        self._settings_manager = settings_manager
        self._setup_ui()
        self._setup_connections()
        self._apply_ui_settings()

        # Initialize ROM table model
        self._rom_model = ROMTableModel(self)
        self._rom_table.setModel(self._rom_model)

        # Set up initial columns based on selected platform
        initial_platform = self._platform_tree.get_selected_platform()
        self._update_table_columns(initial_platform)

        # Ensure sorting is enabled after model is set
        self._rom_table.setSortingEnabled(True)

        # Initialize scanner variables
        self._scanner_thread: ROMScannerThread | None = None

        # Start initial scan if any platform has directories configured
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


        # Main content splitter with improved proportions
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)

        # Left sidebar - Platform tree with better sizing
        self._platform_tree = PlatformTreeWidget()
        self._platform_tree.setMinimumWidth(220)
        self._platform_tree.setMaximumWidth(300)
        splitter.addWidget(self._platform_tree)

        # Right side - ROM table with improved settings
        self._rom_table = QTableView()
        self._rom_table.setAlternatingRowColors(True)
        self._rom_table.setSortingEnabled(True)
        self._rom_table.verticalHeader().setVisible(False)
        self._rom_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._rom_table.setShowGrid(False)

        # Set better row height
        self._rom_table.verticalHeader().setDefaultSectionSize(28)
        self._rom_table.verticalHeader().setMinimumSectionSize(24)

        # Configure horizontal header
        header = self._rom_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSortIndicatorShown(True)
        header.setHighlightSections(False)

        splitter.addWidget(self._rom_table)

        # Set better splitter proportions
        splitter.setSizes([250, 1050])
        splitter.setStretchFactor(0, 0)  # Don't stretch sidebar
        splitter.setStretchFactor(1, 1)  # Stretch table

        # Create UI components
        self._create_toolbar()
        self._create_search_toolbar()
        self._create_menu_bar()
        self._create_status_bar()

    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh ROM library")
        refresh_action.triggered.connect(self._start_rom_scan)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

    def _create_search_toolbar(self) -> None:
        """Create the search toolbar."""
        search_toolbar = QToolBar("Search", self)
        search_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(search_toolbar)

        # Add search label and field
        search_label = QLabel("Search:")
        search_toolbar.addWidget(search_label)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Filter ROMs by name, platform, region, language, or version...")
        self._search_edit.setMinimumWidth(300)
        self._search_edit.setMaximumWidth(500)
        search_toolbar.addWidget(self._search_edit)

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        refresh_action = QAction("Refresh Library", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._start_rom_scan)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        # Default status message
        self._status_bar.showMessage("Ready")

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Platform selection
        self._platform_tree.platform_selected.connect(self._on_platform_selected)

        # Search filter with delay
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_search_filter)
        self._search_edit.textChanged.connect(self._on_search_text_changed)

    def _setup_default_columns(self) -> None:
        """Set up default table columns."""
        from ..platforms.base_platform import TableColumn

        # Default columns that work across all platforms
        default_columns = [
            TableColumn("name", "Name", 300),
            TableColumn("platform", "Platform", 100),
            TableColumn("region", "Region", 80),
            TableColumn("language", "Language", 80),
            TableColumn("version", "Version", 80),
            TableColumn("size", "Size", 100),
            TableColumn("hash", "Hash", 200),
        ]

        self._rom_model.set_columns(default_columns)

        # Set column widths
        for i, column in enumerate(default_columns):
            self._rom_table.setColumnWidth(i, column.width)

    def _apply_ui_settings(self) -> None:
        """Apply the current theme and UI settings."""
        settings = self._settings_manager.settings

        # Apply color theme
        if settings.theme == "light":
            self.setStyleSheet(LIGHT_STYLE)
        else:
            self.setStyleSheet(DARK_STYLE)

        # Apply font size to the entire application
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app_font = app.font()
            app_font.setPointSize(settings.font_size)
            app.setFont(app_font)

            # Also apply to main window and key components explicitly
            self.setFont(app_font)
            self._platform_tree.setFont(app_font)
            if hasattr(self, '_search_edit'):
                self._search_edit.setFont(app_font)

            # Table needs special handling
            self._rom_table.setFont(app_font)
            # Also apply to table headers
            self._rom_table.horizontalHeader().setFont(app_font)
            self._rom_table.verticalHeader().setFont(app_font)
            # Force the table to update its appearance
            self._rom_table.reset()
            self._rom_table.repaint()

            # Apply to menu bar and status bar
            if hasattr(self, 'menuBar'):
                self.menuBar().setFont(app_font)
            if hasattr(self, '_status_bar'):
                self._status_bar.setFont(app_font)

            # Force update on all child widgets
            self._update_fonts_recursively(self, app_font)

        # Apply table row height
        self._rom_table.verticalHeader().setDefaultSectionSize(settings.table_row_height)
        self._rom_table.verticalHeader().setMinimumSectionSize(max(20, settings.table_row_height - 4))

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self._settings_manager, self)
        # Connect to apply changes immediately when Apply is clicked
        dialog.settings_applied.connect(self._on_settings_applied)
        if dialog.exec():
            # Apply new settings when OK is clicked
            self._on_settings_applied()

    def _on_platform_selected(self, selected_platform: str) -> None:
        """Handle platform selection changes."""
        if selected_platform == "all":
            # Show all platforms
            all_platforms = [p.platform_id for p in platform_registry.get_all_platforms()]
            self._rom_model.set_platform_filter(all_platforms)
            self._update_table_columns("all")
        else:
            # Show only selected platform
            self._rom_model.set_platform_filter([selected_platform])
            self._update_table_columns(selected_platform)
        self._update_platform_counts()

    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes with a delay."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms delay

    def _apply_search_filter(self) -> None:
        """Apply search filter to the ROM table."""
        search_text = self._search_edit.text().strip()
        self._rom_model.set_search_filter(search_text)
        self._update_platform_counts()

    def _update_platform_counts(self) -> None:
        """Update ROM counts for each platform."""
        # Count ROMs by platform using search-filtered entries (ignoring platform filter)
        # This shows total count or search results count, not what's currently visible
        counts: dict[str, int] = {}
        entries = self._rom_model.get_search_filtered_entries()

        for entry in entries:
            counts[entry.platform_id] = counts.get(entry.platform_id, 0) + 1

        self._platform_tree.update_rom_counts(counts)

    def _update_table_columns(self, selected_platform: str) -> None:
        """Update table columns based on selected platform."""
        from ..platforms.base_platform import TableColumn

        columns = []

        if selected_platform == "all":
            # Show default columns for all platforms view
            columns.extend([
                TableColumn("name", "Name", 300),
                TableColumn("platform", "Platform", 100),
                TableColumn("region", "Region", 80),
                TableColumn("language", "Language", 80),
                TableColumn("version", "Version", 80),
                TableColumn("size", "Size", 100),
            ])
        else:
            # Show platform-specific columns
            platform = platform_registry.get_platform(selected_platform)
            if platform:
                columns.extend(platform.table_columns.copy())
            else:
                # Fallback to default columns
                columns.extend([
                    TableColumn("name", "Name", 300),
                    TableColumn("platform", "Platform", 100),
                    TableColumn("region", "Region", 80),
                    TableColumn("language", "Language", 80),
                    TableColumn("version", "Version", 80),
                    TableColumn("size", "Size", 100),
                ])

        # Update the model with new columns
        self._rom_model.set_columns(columns)

        # Apply column widths
        for i, column in enumerate(columns):
            self._rom_table.setColumnWidth(i, column.width)


    def add_rom_entries(self, entries) -> None:
        """Add ROM entries to the table."""
        if not entries:
            return

        self._rom_model.add_rom_entries(entries)
        self._update_platform_counts()



    def clear_rom_entries(self) -> None:
        """Clear all ROM entries."""
        self._rom_model.clear()
        self._update_platform_counts()

    def get_selected_platform(self) -> str:
        """Get the selected platform ID."""
        return self._platform_tree.get_selected_platform()

    def _has_platform_directories(self) -> bool:
        """Check if any platform has directories configured."""
        settings = self._settings_manager.settings
        for platform_settings in settings.platform_settings.values():
            rom_directories = platform_settings.get('rom_directories', [])
            if rom_directories:
                return True
        return False

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
        settings = self._settings_manager.settings

        # Create platform-specific configurations
        platform_configs = []
        platforms = platform_registry.get_all_platforms()
        total_directories = 0

        for platform in platforms:
            # Get platform-specific settings
            platform_settings = settings.platform_settings.get(platform.platform_id, {})

            # Get platform directories
            platform_directories = platform_settings.get('rom_directories', [])

            if platform_directories:  # Only add platforms that have directories configured
                platform_configs.append({
                    'platform': platform,
                    'directories': platform_directories,
                    'scan_subdirectories': platform_settings.get('scan_subdirectories', True),
                    'handle_archives': platform_settings.get('handle_archives', True),
                    'supported_formats': platform_settings.get('supported_formats', platform.get_supported_handlers()),
                    'supported_archives': platform_settings.get('supported_archives', platform.get_archive_content_extensions())
                })
                total_directories += len(platform_directories)

        # Don't scan if no directories are configured for any platform
        if not platform_configs:
            self._status_bar.showMessage("No ROM directories configured for any platform. Check Settings.")
            return

        # Stop any existing scan
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.quit()
            self._scanner_thread.wait()

        # Clear existing ROMs
        self.clear_rom_entries()

        # Update status
        platform_count = len(platform_configs)
        self._status_bar.showMessage(f"Scanning {total_directories} directories across {platform_count} platforms...")

        # Start new scan with platform-specific configurations
        self._scanner_thread = ROMScannerThread(platform_configs)

        # Connect scanner signals
        self._scanner_thread.scanner.rom_found.connect(self._on_rom_found)
        self._scanner_thread.scanner.scan_completed.connect(self._on_scan_completed)
        self._scanner_thread.scanner.scan_error.connect(self._on_scan_error)

        # Start scanning
        self._scanner_thread.start()
        print(f"Started scanning {total_directories} directories across {platform_count} platforms...")

    def _on_rom_found(self, rom_entry) -> None:
        """Handle a ROM being found during scan."""
        print(f"Found ROM: {rom_entry.display_name} ({rom_entry.platform_id})")
        self.add_rom_entries([rom_entry])

    def _on_scan_completed(self, all_entries) -> None:
        """Handle scan completion."""
        print(f"Scan completed. Found {len(all_entries)} total ROMs.")
        self._status_bar.showMessage(f"Scan completed. Found {len(all_entries)} ROMs.")

        # Clean up scanner thread properly
        if self._scanner_thread:
            self._scanner_thread.quit()
            self._scanner_thread.wait()
            self._scanner_thread.deleteLater()
            self._scanner_thread = None


    def _on_scan_error(self, error_msg) -> None:
        """Handle scan errors."""
        print(f"Scan error: {error_msg}")
        self._status_bar.showMessage(f"Scan error: {error_msg}")

        # Clean up scanner thread properly
        if self._scanner_thread:
            self._scanner_thread.quit()
            self._scanner_thread.wait()
            self._scanner_thread.deleteLater()
            self._scanner_thread = None

    def closeEvent(self, event) -> None:
        """Handle application close event."""
        # Stop scanner thread if running
        if self._scanner_thread:
            if self._scanner_thread.isRunning():
                print("Stopping ROM scanner thread...")
                self._scanner_thread.scanner.stop_scan()
                self._scanner_thread.quit()
                self._scanner_thread.wait(5000)  # Wait up to 5 seconds
                if self._scanner_thread.isRunning():
                    print("Thread didn't stop gracefully, terminating...")
                    self._scanner_thread.terminate()
                    self._scanner_thread.wait(1000)  # Wait 1 more second after terminate

            # Clean up thread object
            self._scanner_thread.deleteLater()
            self._scanner_thread = None

        event.accept()







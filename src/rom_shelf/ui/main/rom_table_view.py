"""ROM table view component with configurable columns."""

import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHeaderView, QMenu, QMessageBox, QTableView, QWidget

from ...models.rom_table_model import ROMTableModel
from ...platforms.core.base_platform import TableColumn
from ...platforms.core.platform_registry import platform_registry
from ..delegates.achievement_delegate import AchievementDelegate
from ..delegates.hash_delegate import HashDelegate
from ..delegates.language_delegate import LanguageDelegate
from ..delegates.region_delegate import RegionDelegate


class ROMTableView(QTableView):
    """Enhanced table view for displaying ROM entries."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the ROM table view."""
        super().__init__(parent)
        self._rom_model: ROMTableModel | None = None
        self._achievement_delegate = AchievementDelegate(self)
        self._hash_delegate = HashDelegate(self)
        self._region_delegate = RegionDelegate(self)
        self._language_delegate = LanguageDelegate(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the table view appearance and behavior."""
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setShowGrid(False)

        # Enable mouse tracking for tooltips
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        # Enable hover events for delegates
        self.viewport().setAttribute(Qt.WA_Hover, True)

        # Disable text wrapping to use ellipsis instead
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)

        # Set better row height
        self.verticalHeader().setDefaultSectionSize(28)
        self.verticalHeader().setMinimumSectionSize(24)

        # Configure horizontal header
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSortIndicatorShown(True)
        header.setHighlightSections(False)

        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_model(self, model: ROMTableModel) -> None:
        """Set the ROM table model."""
        self._rom_model = model
        super().setModel(model)

    def update_columns(self, selected_platform: str) -> None:
        """Update table columns based on selected platform."""
        if not self._rom_model:
            return

        columns = []

        if selected_platform == "all":
            # Show default columns for all platforms view
            columns.extend(
                [
                    TableColumn("name", "Name", 300),  # Will stretch, width is minimum
                    TableColumn("platform", "Platform", 120),
                    TableColumn("region", "Region", 100),
                    TableColumn("language", "Language", 100),
                    TableColumn("version", "Version", 90),
                    TableColumn("size", "Size", 100),
                    TableColumn("achievements", "RA", 100),  # RetroAchievements column
                ]
            )
        else:
            # Show platform-specific columns
            platform = platform_registry.get_platform(selected_platform)
            if platform:
                columns.extend(platform.table_columns.copy())
            else:
                # Fallback to default columns
                columns.extend(
                    [
                        TableColumn("name", "Name", 300),  # Will stretch, width is minimum
                        TableColumn("platform", "Platform", 120),
                        TableColumn("region", "Region", 100),
                        TableColumn("language", "Language", 100),
                        TableColumn("version", "Version", 90),
                        TableColumn("size", "Size", 100),
                        TableColumn("achievements", "RA", 100),  # RetroAchievements column
                    ]
                )

        # Update the model with new columns
        self._rom_model.set_columns(columns)

        # Clear all column delegates first to avoid misalignment
        for i in range(self._rom_model.columnCount()):
            self.setItemDelegateForColumn(i, None)

        # Configure column resize modes and widths
        header = self.horizontalHeader()
        for i, column in enumerate(columns):
            # Apply custom delegates where needed
            if column.key == "hash":
                print(f"[DEBUG] Setting hash delegate for column {i}")
                self.setItemDelegateForColumn(i, self._hash_delegate)
            elif column.key == "region":
                print(f"[DEBUG] Setting region delegate for column {i}")
                self.setItemDelegateForColumn(i, self._region_delegate)
            elif column.key == "language":
                print(f"[DEBUG] Setting language delegate for column {i}")
                self.setItemDelegateForColumn(i, self._language_delegate)
            elif column.key == "achievements":
                print(f"[DEBUG] Setting achievement delegate for column {i}")
                self.setItemDelegateForColumn(i, self._achievement_delegate)

            # Configure column sizing
            if column.key == "name":
                # Make Name column stretch to fill available space
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                # Set other columns to fixed size
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(i, column.width)

    def apply_table_settings(self, row_height: int) -> None:
        """Apply table-specific settings."""
        self.verticalHeader().setDefaultSectionSize(row_height)
        self.verticalHeader().setMinimumSectionSize(max(20, row_height - 4))

    def _show_context_menu(self, position: QPoint) -> None:
        """Show context menu for ROM entries."""
        index = self.indexAt(position)
        if not index.isValid() or not self._rom_model:
            return

        # Get the ROM entry
        rom_entry = self._rom_model.get_rom_entry(index)
        if not rom_entry:
            return

        # Create context menu
        menu = QMenu(self)

        # Show in file manager
        if os.name == "nt":
            file_manager_text = "Show in Explorer"
        elif platform.system() == "Darwin":
            file_manager_text = "Show in Finder"
        else:
            file_manager_text = "Show in File Manager"

        show_in_explorer = QAction(file_manager_text, self)
        show_in_explorer.triggered.connect(lambda: self._show_in_file_manager(rom_entry.file_path))
        menu.addAction(show_in_explorer)

        # Copy file path
        copy_path = QAction("Copy File Path", self)
        copy_path.triggered.connect(lambda: self._copy_to_clipboard(str(rom_entry.file_path)))
        menu.addAction(copy_path)

        # Copy file name
        copy_name = QAction("Copy File Name", self)
        copy_name.triggered.connect(lambda: self._copy_to_clipboard(rom_entry.file_path.name))
        menu.addAction(copy_name)

        menu.addSeparator()

        # Copy ROM info
        copy_info = QAction("Copy ROM Info", self)
        copy_info.triggered.connect(lambda: self._copy_rom_info(rom_entry))
        menu.addAction(copy_info)

        # If it's an archive with internal path
        if rom_entry.internal_path:
            menu.addSeparator()
            copy_internal = QAction("Copy Internal Path", self)
            copy_internal.triggered.connect(
                lambda: self._copy_to_clipboard(rom_entry.internal_path)
            )
            menu.addAction(copy_internal)

        # Show the menu at cursor position
        menu.exec(self.mapToGlobal(position))

    def _show_in_file_manager(self, file_path: Path) -> None:
        """Open the file location in the system's file manager."""
        if not file_path.exists():
            QMessageBox.warning(self, "File Not Found", f"The file no longer exists:\n{file_path}")
            return

        system = platform.system()
        try:
            if system == "Windows":
                # Windows: Use SHOpenFolderAndSelectItems via ctypes to respect default file manager
                import ctypes

                try:
                    # Use Windows Shell API to open folder and select item
                    # This respects the system's default file manager
                    shell32 = ctypes.windll.shell32

                    # Convert path to Windows format
                    file_path_str = str(file_path).replace("/", "\\")

                    # SHOpenFolderAndSelectItems would be ideal but it's complex to call
                    # Instead, use ShellExecute to open the parent folder
                    # This will use the default file manager
                    result = shell32.ShellExecuteW(
                        None,
                        "open",
                        str(file_path.parent),
                        None,
                        None,
                        1,  # SW_SHOWNORMAL
                    )

                    if result <= 32:  # Error occurred
                        # Fallback to explorer if shell execute fails
                        subprocess.run(["explorer", "/select,", str(file_path)])
                except Exception:
                    # Final fallback to explorer
                    subprocess.run(["explorer", "/select,", str(file_path)])
            elif system == "Darwin":
                # macOS: Use open with the parent directory
                # This respects the user's default file manager (Finder, Path Finder, etc.)
                subprocess.run(["open", str(file_path.parent)])
            else:
                # Linux: Use xdg-open which respects the user's default file manager
                # xdg-open will use whatever is configured in the desktop environment
                parent_dir = file_path.parent

                # First try xdg-open which respects user preferences
                if subprocess.run(["which", "xdg-open"], capture_output=True).returncode == 0:
                    # Open the parent directory with the default file manager
                    subprocess.run(["xdg-open", str(parent_dir)])
                else:
                    # Very rare case where xdg-open isn't available
                    # Try some common file managers
                    if subprocess.run(["which", "nautilus"], capture_output=True).returncode == 0:
                        subprocess.run(["nautilus", str(parent_dir)])
                    elif subprocess.run(["which", "dolphin"], capture_output=True).returncode == 0:
                        subprocess.run(["dolphin", str(parent_dir)])
                    elif subprocess.run(["which", "thunar"], capture_output=True).returncode == 0:
                        subprocess.run(["thunar", str(parent_dir)])
                    else:
                        # Last resort: try to open with Python's webbrowser module
                        import webbrowser

                        webbrowser.open(str(parent_dir))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file location:\n{e}")

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def _copy_rom_info(self, rom_entry) -> None:
        """Copy ROM information to clipboard."""
        info_lines = [
            f"Name: {rom_entry.display_name}",
            f"File: {rom_entry.file_path.name}",
            f"Path: {rom_entry.file_path}",
            f"Platform: {rom_entry.platform_id}",
        ]

        # Add metadata if available
        if rom_entry.metadata:
            for key, value in rom_entry.metadata.items():
                if value:  # Only add non-empty values
                    # Capitalize the key for display
                    display_key = key.replace("_", " ").title()
                    info_lines.append(f"{display_key}: {value}")

        self._copy_to_clipboard("\n".join(info_lines))

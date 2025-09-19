"""Builder utilities for constructing the main window layout."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..widgets.scan_progress_dock import ScanProgressDock
from .platform_tree import PlatformTreeWidget
from .rom_table_view import ROMTableView
from .search_handler import SearchHandler
from .toolbar_manager import ToolbarManager


@dataclass(slots=True)
class MainUiComponents:
    """Container for the primary widgets hosted by the main window."""

    central_widget: QWidget
    platform_tree: PlatformTreeWidget
    rom_table: ROMTableView
    toolbar_manager: ToolbarManager
    search_handler: SearchHandler
    scan_dock: ScanProgressDock


class MainUiBuilder:
    """Builds the reusable layout and chrome for the ROM Shelf main window."""

    def __init__(self, main_window) -> None:
        self._main_window = main_window

    def build(self) -> MainUiComponents:
        """Create the main layout and associated helper objects."""
        central_widget = QWidget()
        self._main_window.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 8, 12, 12)
        root_layout.setSpacing(8)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        root_layout.addLayout(content_layout)

        platform_tree = PlatformTreeWidget()
        platform_tree.setMinimumWidth(200)
        platform_tree.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(platform_tree)

        rom_table = ROMTableView()
        content_layout.addWidget(rom_table, 1)

        toolbar_manager = ToolbarManager(self._main_window)
        search_handler = SearchHandler(self._main_window)

        scan_dock = ScanProgressDock(self._main_window)
        self._main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, scan_dock)

        return MainUiComponents(
            central_widget=central_widget,
            platform_tree=platform_tree,
            rom_table=rom_table,
            toolbar_manager=toolbar_manager,
            search_handler=search_handler,
            scan_dock=scan_dock,
        )

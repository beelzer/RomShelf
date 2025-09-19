"""Main window for the ROM Shelf application using modular components."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from ...models.rom_table_model import ROMTableModel
from ...platforms.core.platform_registry import platform_registry
from ...services import ServiceContainer
from ..settings import SettingsDialog
from ..themes import get_theme_manager
from .scan_controller import (
    RomFoundEvent,
    ROMScanController,
    ScanCompletionContext,
    ScanStartContext,
)
from .scan_presenter import ScanUiPresenter
from .ui_builder import MainUiBuilder


class MainWindow(QMainWindow):
    """Main window for the ROM Shelf application."""

    def __init__(self, service_container: ServiceContainer) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._service_container = service_container
        self._settings_service = service_container.settings_service

        self.setWindowTitle("ROM Shelf")
        self.setMinimumSize(900, 600)
        self.resize(1300, 800)

        # Build reusable UI shell
        ui_components = MainUiBuilder(self).build()
        self._platform_tree = ui_components.platform_tree
        self._rom_table = ui_components.rom_table
        self._toolbar_manager = ui_components.toolbar_manager
        self._search_handler = ui_components.search_handler
        self._scan_dock = ui_components.scan_dock

        # Wire chrome elements
        self._toolbar_manager.attach_scan_dock(self._scan_dock)
        self._toolbar_manager.create_status_bar()
        self._toolbar_manager.create_main_toolbar(self._start_rom_scan, self._open_settings)
        search_toolbar = self._search_handler.create_search_toolbar(self)
        self.addToolBar(search_toolbar)
        self._toolbar_manager.create_menu_bar(self._start_rom_scan, self._open_settings)

        self.menuBar().setVisible(False)
        self._menu_visible = False

        # Models and coordinators
        self._rom_model: ROMTableModel | None = None
        self._scan_controller = ROMScanController(
            settings_service=self._settings_service,
            platform_registry=platform_registry,
            parent=self,
            logger=self.logger.getChild("ROMScanController"),
        )
        self._scan_presenter = ScanUiPresenter(
            toolbar_manager=self._toolbar_manager,
            scan_dock=self._scan_dock,
            logger=self.logger.getChild("ScanUiPresenter"),
        )

        self._connect_scan_pipeline()
        self._setup_connections()
        self._apply_ui_settings()
        self._setup_rom_model()

        if self._scan_controller.has_configured_platforms():
            self._start_rom_scan()

    # ----------------------------------------------------------------------------------
    # Wiring helpers

    def _connect_scan_pipeline(self) -> None:
        self._scan_controller.scan_started.connect(self._scan_presenter.on_scan_started)
        self._scan_controller.scan_started.connect(self._on_scan_started)
        self._scan_controller.rom_found.connect(self._scan_presenter.on_rom_found)
        self._scan_controller.rom_found.connect(self._append_rom_entry)
        self._scan_controller.scan_progress.connect(self._scan_presenter.on_scan_progress)
        self._scan_controller.scan_completed.connect(self._scan_presenter.on_scan_completed)
        self._scan_controller.scan_completed.connect(self._on_scan_completed)
        self._scan_controller.scan_failed.connect(self._scan_presenter.on_scan_failed)

    def _setup_connections(self) -> None:
        if self._platform_tree:
            self._platform_tree.platform_selected.connect(self._on_platform_selected)

        if self._search_handler:
            self._search_handler.filter_changed.connect(self._update_platform_counts)

    def _setup_rom_model(self) -> None:
        self._rom_model = ROMTableModel(self)

        if self._rom_table:
            self._rom_table.set_model(self._rom_model)
            if self._platform_tree:
                initial_platform = self._platform_tree.get_selected_platform()
                self._rom_table.update_columns(initial_platform)

        if self._search_handler:
            self._search_handler.set_rom_model(self._rom_model)

    # ----------------------------------------------------------------------------------
    # UI behaviour

    def _apply_ui_settings(self) -> None:
        settings = self._settings_service.settings

        theme_manager = get_theme_manager()
        theme_name = settings.theme
        if settings.theme == "dark":
            theme_name = "modern dark"
        elif settings.theme == "light":
            theme_name = "modern light"

        if theme_manager.set_theme(theme_name):
            app = QApplication.instance()
            if app:
                theme_manager.apply_theme_to_application(app)

        app = QApplication.instance()
        if app:
            app_font = app.font()
            app_font.setPointSize(settings.font_size)
            app.setFont(app_font)

            self.setFont(app_font)

            if self._platform_tree:
                self._platform_tree.setFont(app_font)

            if self._search_handler:
                self._search_handler.apply_font_settings(app_font)

            if self._toolbar_manager:
                self._toolbar_manager.apply_font_settings(app_font)

            if self._scan_dock:
                self._scan_dock.setFont(app_font)
                self._scan_dock.apply_theme()

            if self._rom_table:
                self._rom_table.setFont(app_font)
                self._rom_table.horizontalHeader().setFont(app_font)
                self._rom_table.verticalHeader().setFont(app_font)
                self._rom_table.reset()
                self._rom_table.repaint()

            self._update_fonts_recursively(self, app_font)

        if self._rom_table:
            self._rom_table.apply_table_settings(settings.table_row_height)

    # ----------------------------------------------------------------------------------
    # Scan orchestration

    def _on_scan_started(self, _: ScanStartContext) -> None:
        self.clear_rom_entries()

    def _append_rom_entry(self, event: RomFoundEvent) -> None:
        self.add_rom_entries([event.entry])

    def _on_scan_completed(self, _: ScanCompletionContext) -> None:
        self._update_platform_counts()

    def _start_rom_scan(self) -> None:
        self._scan_controller.start_scan()

    # ----------------------------------------------------------------------------------
    # Model helpers

    def _on_platform_selected(self, selected_platform: str) -> None:
        if not self._rom_model or not self._rom_table:
            return

        if selected_platform == "all":
            platform_ids = [p.platform_id for p in platform_registry.get_all_platforms()]
            self._rom_model.set_platform_filter(platform_ids)
        else:
            self._rom_model.set_platform_filter([selected_platform])

        self._rom_table.update_columns(selected_platform)
        self._update_platform_counts()

    def _update_platform_counts(self) -> None:
        if not self._rom_model or not self._platform_tree:
            return

        counts: dict[str, int] = {}
        for entry in self._rom_model.get_search_filtered_entries():
            counts[entry.platform_id] = counts.get(entry.platform_id, 0) + 1

        self._platform_tree.update_rom_counts(counts)

    def add_rom_entries(self, entries) -> None:
        if not entries or not self._rom_model:
            return
        self._rom_model.add_rom_entries(entries)
        self._update_platform_counts()

    def clear_rom_entries(self) -> None:
        if self._rom_model:
            self._rom_model.clear()
        self._update_platform_counts()

    def get_selected_platform(self) -> str:
        if self._platform_tree:
            return self._platform_tree.get_selected_platform()
        return "all"

    # ----------------------------------------------------------------------------------
    # Settings

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._service_container.settings_service._settings_manager, self)
        dialog.settings_applied.connect(self._on_settings_applied)
        if dialog.exec():
            self._on_settings_applied()

    def _on_settings_applied(self) -> None:
        self._apply_ui_settings()
        self._start_rom_scan()

    # ----------------------------------------------------------------------------------
    # Utilities

    def _update_fonts_recursively(self, widget, font) -> None:
        try:
            widget.setFont(font)
            for child in widget.findChildren(QWidget):
                child.setFont(font)
        except Exception:
            pass

    # ----------------------------------------------------------------------------------
    # Qt Events

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Alt and not self._menu_visible:
            self.menuBar().setVisible(True)
            self._menu_visible = True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Alt and self._menu_visible:
            self.menuBar().setVisible(False)
            self._menu_visible = False
        super().keyReleaseEvent(event)

    def closeEvent(self, event) -> None:
        self._scan_controller.stop_scan()
        event.accept()

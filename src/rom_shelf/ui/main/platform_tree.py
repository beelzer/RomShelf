"""Platform tree widget for filtering ROMs by platform."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from ...platforms.core.platform_registry import platform_registry


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

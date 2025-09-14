"""ROM table view component with configurable columns."""

from PySide6.QtWidgets import QHeaderView, QTableView, QWidget

from ...models.rom_table_model import ROMTableModel
from ...platforms.base_platform import TableColumn
from ...platforms.platform_registry import platform_registry


class ROMTableView(QTableView):
    """Enhanced table view for displaying ROM entries."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the ROM table view."""
        super().__init__(parent)
        self._rom_model: ROMTableModel | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the table view appearance and behavior."""
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setShowGrid(False)

        # Set better row height
        self.verticalHeader().setDefaultSectionSize(28)
        self.verticalHeader().setMinimumSectionSize(24)

        # Configure horizontal header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSortIndicatorShown(True)
        header.setHighlightSections(False)

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
            self.setColumnWidth(i, column.width)

    def apply_table_settings(self, row_height: int) -> None:
        """Apply table-specific settings."""
        self.verticalHeader().setDefaultSectionSize(row_height)
        self.verticalHeader().setMinimumSectionSize(max(20, row_height - 4))
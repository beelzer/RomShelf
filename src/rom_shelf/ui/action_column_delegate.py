"""Action column delegate for ROM table."""


from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QWidget


class ActionColumnDelegate(QStyledItemDelegate):
    """Custom delegate for action column."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the delegate."""
        super().__init__(parent)
        self._icon_size = 20

    def paint(self, painter: QPainter, option, index) -> None:
        """Paint the action column."""
        # Currently no actions to display - placeholder for future functionality
        pass

    def editorEvent(self, event, model, option, index):
        """Handle editor events like clicks."""
        # Currently no click handling - placeholder for future functionality
        return False

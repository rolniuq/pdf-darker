"""Base class for tool panels."""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from ...utils.logging import get_logger

logger = get_logger("gui.tool_panel_base")


class BaseToolPanel(QWidget):
    """Base class for all tool panels."""
    
    # Signal emitted when an operation is requested
    operation_requested = Signal(dict)
    
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        self.main_layout = layout
        
        # Override in subclasses
        self.setup_panel()
    
    def setup_panel(self):
        """Setup the specific panel content. Override in subclasses."""
        pass
    
    def emit_operation(self, operation_data: dict):
        """Emit an operation request."""
        self.operation_requested.emit(operation_data)
        logger.info(f"Operation requested from {self.title}: {operation_data.get('name')}")
"""Form editor tool panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QSpinBox, QGroupBox, QCheckBox,
    QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt

from . import BaseToolPanel
from ...utils.logging import get_logger

logger = get_logger("gui.form_editor")


class FormEditorPanel(BaseToolPanel):
    """Panel for creating and editing form fields."""
    
    def __init__(self):
        super().__init__("Form Editor")
    
    def setup_panel(self):
        """Setup the form editor panel."""
        # Field creation group
        create_group = QGroupBox("Create Form Field")
        create_layout = QFormLayout()
        
        # Field type
        self.field_type_combo = QComboBox()
        self.field_type_combo.addItems([
            "Text Field",
            "Checkbox", 
            "Radio Button",
            "List/Dropdown",
            "Signature"
        ])
        create_layout.addRow("Field Type:", self.field_type_combo)
        
        # Field name
        self.field_name_edit = QLineEdit()
        self.field_name_edit.setPlaceholderText("Enter field name")
        create_layout.addRow("Field Name:", self.field_name_edit)
        
        # Default value
        self.default_value_edit = QLineEdit()
        self.default_value_edit.setPlaceholderText("Default value (optional)")
        create_layout.addRow("Default Value:", self.default_value_edit)
        
        # Position and size
        position_group = QGroupBox("Position & Size")
        position_layout = QFormLayout()
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setValue(1)
        position_layout.addRow("Page:", self.page_spinbox)
        
        self.x_pos_spinbox = QSpinBox()
        self.x_pos_spinbox.setRange(0, 1000)
        self.x_pos_spinbox.setValue(100)
        position_layout.addRow("X Position:", self.x_pos_spinbox)
        
        self.y_pos_spinbox = QSpinBox()
        self.y_pos_spinbox.setRange(0, 1000)
        self.y_pos_spinbox.setValue(100)
        position_layout.addRow("Y Position:", self.y_pos_spinbox)
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(10, 500)
        self.width_spinbox.setValue(100)
        position_layout.addRow("Width:", self.width_spinbox)
        
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(10, 200)
        self.height_spinbox.setValue(20)
        position_layout.addRow("Height:", self.height_spinbox)
        
        position_group.setLayout(position_layout)
        create_layout.addRow(position_group)
        
        # Options for list/dropdown fields
        self.options_edit = QLineEdit()
        self.options_edit.setPlaceholderText("Option1,Option2,Option3")
        self.options_edit.setEnabled(False)
        create_layout.addRow("Options (List/Dropdown):", self.options_edit)
        
        # Create button
        self.create_button = QPushButton("Create Field")
        self.create_button.clicked.connect(self.create_field)
        create_layout.addRow(self.create_button)
        
        create_group.setLayout(create_layout)
        self.main_layout.addWidget(create_group)
        
        # Field operations group
        operations_group = QGroupBox("Field Operations")
        operations_layout = QVBoxLayout()
        
        self.fill_button = QPushButton("Fill Form Fields")
        self.fill_button.clicked.connect(self.fill_form)
        operations_layout.addWidget(self.fill_button)
        
        self.validate_button = QPushButton("Validate Form")
        self.validate_button.clicked.connect(self.validate_form)
        operations_layout.addWidget(self.validate_button)
        
        self.export_button = QPushButton("Export Form Data")
        self.export_button.clicked.connect(self.export_form_data)
        operations_layout.addWidget(self.export_button)
        
        operations_group.setLayout(operations_layout)
        self.main_layout.addWidget(operations_group)
        
        # Connect signals
        self.field_type_combo.currentTextChanged.connect(self.on_field_type_changed)
        
        self.main_layout.addStretch()
    
    def on_field_type_changed(self, field_type: str):
        """Handle field type change."""
        # Enable options edit for list/dropdown fields
        is_list_field = field_type in ["List/Dropdown"]
        self.options_edit.setEnabled(is_list_field)
        
        # Adjust default height based on field type
        if field_type == "Text Field":
            self.height_spinbox.setValue(20)
        elif field_type == "Checkbox":
            self.height_spinbox.setValue(15)
            self.width_spinbox.setValue(15)
        elif field_type == "Signature":
            self.height_spinbox.setValue(50)
            self.width_spinbox.setValue(200)
        elif field_type == "List/Dropdown":
            self.height_spinbox.setValue(30)
    
    def create_field(self):
        """Create a new form field."""
        field_name = self.field_name_edit.text().strip()
        if not field_name:
            QMessageBox.warning(self, "Warning", "Please enter a field name")
            return
        
        # Get field type and convert to operation format
        field_type_map = {
            "Text Field": "text",
            "Checkbox": "checkbox",
            "Radio Button": "radio", 
            "List/Dropdown": "list",
            "Signature": "signature"
        }
        
        field_type = field_type_map[self.field_type_combo.currentText()]
        default_value = self.default_value_edit.text().strip()
        
        # Get position and size
        page = self.page_spinbox.value() - 1  # Convert to 0-based
        x = self.x_pos_spinbox.value()
        y = self.y_pos_spinbox.value()
        width = self.width_spinbox.value()
        height = self.height_spinbox.value()
        
        # Create rectangle (x0, y0, x1, y1)
        rect = (x, y, x + width, y + height)
        
        # Get options for list fields
        options = []
        if field_type == "list":
            options_text = self.options_edit.text().strip()
            if options_text:
                options = [opt.strip() for opt in options_text.split(",") if opt.strip()]
        
        # Emit operation request
        operation_data = {
            'name': 'create_field',
            'type': field_type,
            'page': page,
            'rect': rect,
            'field_name': field_name,
            'default_value': default_value,
            'options': options
        }
        
        self.emit_operation(operation_data)
        
        # Clear form
        self.field_name_edit.clear()
        self.default_value_edit.clear()
        self.options_edit.clear()
    
    def fill_form(self):
        """Open form filling dialog."""
        # TODO: Implement form filling dialog
        operation_data = {
            'name': 'fill_form',
            'data': {}  # Would be populated from dialog
        }
        self.emit_operation(operation_data)
    
    def validate_form(self):
        """Validate form fields."""
        operation_data = {
            'name': 'validate_form',
            'rules': {}  # Would be populated from validation rules
        }
        self.emit_operation(operation_data)
    
    def export_form_data(self):
        """Export form data."""
        operation_data = {
            'name': 'export_form_data',
            'format': 'json'  # Could be json, csv, xml, fdf
        }
        self.emit_operation(operation_data)
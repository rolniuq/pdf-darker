"""Annotation tools panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QColorDialog, QSpinBox, QGroupBox, QFormLayout,
    QTextEdit, QCheckBox, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from . import BaseToolPanel
from ...utils.logging import get_logger

logger = get_logger("gui.annotation_tools")


class AnnotationToolsPanel(BaseToolPanel):
    """Panel for annotation tools."""
    
    def __init__(self):
        super().__init__("Annotation Tools")
        
        self.current_color = QColor(255, 0, 0)  # Default red
        self.current_thickness = 2
    
    def setup_panel(self):
        """Setup the annotation tools panel."""
        # Annotation type group
        type_group = QGroupBox("Annotation Type")
        type_layout = QVBoxLayout()
        
        self.annotation_type_combo = QComboBox()
        self.annotation_type_combo.addItems([
            "Highlight",
            "Underline", 
            "Strikeout",
            "Squiggly Underline",
            "Text Note",
            "Rectangle",
            "Circle",
            "Line",
            "Freehand Drawing"
        ])
        type_layout.addWidget(self.annotation_type_combo)
        type_group.setLayout(type_layout)
        self.main_layout.addWidget(type_group)
        
        # Style settings group
        style_group = QGroupBox("Style Settings")
        style_layout = QFormLayout()
        
        # Color selection
        self.color_button = QPushButton()
        self.color_button.setText("Choose Color")
        self.color_button.setStyleSheet(f"background-color: {self.current_color.name()}")
        self.color_button.clicked.connect(self.choose_color)
        style_layout.addRow("Color:", self.color_button)
        
        # Thickness
        self.thickness_spinbox = QSpinBox()
        self.thickness_spinbox.setRange(1, 20)
        self.thickness_spinbox.setValue(self.current_thickness)
        self.thickness_spinbox.valueChanged.connect(self.on_thickness_changed)
        style_layout.addRow("Thickness:", self.thickness_spinbox)
        
        # Opacity
        self.opacity_spinbox = QSpinBox()
        self.opacity_spinbox.setRange(0, 100)
        self.opacity_spinbox.setValue(80)
        style_layout.addRow("Opacity (%):", self.opacity_spinbox)
        
        style_group.setLayout(style_layout)
        self.main_layout.addWidget(style_group)
        
        # Position and size group
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
        self.height_spinbox.setRange(10, 500)
        self.height_spinbox.setValue(50)
        position_layout.addRow("Height:", self.height_spinbox)
        
        position_group.setLayout(position_layout)
        self.main_layout.addWidget(position_group)
        
        # Content group (for text annotations)
        content_group = QGroupBox("Content")
        content_layout = QVBoxLayout()
        
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Author name")
        content_layout.addWidget(QLabel("Author:"))
        content_layout.addWidget(self.author_edit)
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Annotation content or note...")
        self.content_edit.setMaximumHeight(100)
        content_layout.addWidget(QLabel("Content:"))
        content_layout.addWidget(self.content_edit)
        
        content_group.setLayout(content_layout)
        self.main_layout.addWidget(content_group)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.add_annotation_button = QPushButton("Add Annotation")
        self.add_annotation_button.clicked.connect(self.add_annotation)
        buttons_layout.addWidget(self.add_annotation_button)
        
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        buttons_layout.addWidget(self.clear_button)
        
        self.main_layout.addLayout(buttons_layout)
        
        # Connect signals
        self.annotation_type_combo.currentTextChanged.connect(self.on_annotation_type_changed)
        self.on_annotation_type_changed(self.annotation_type_combo.currentText())
        
        self.main_layout.addStretch()
    
    def on_annotation_type_changed(self, annotation_type: str):
        """Handle annotation type change."""
        # Show/hide content group based on annotation type
        content_group = self.main_layout.findChild(QGroupBox, "Content")
        if content_group:
            # For text notes, show content, for others hide
            is_text_annotation = annotation_type in ["Text Note"]
            content_group.setVisible(is_text_annotation)
        
        # Adjust default size based on type
        if annotation_type in ["Highlight", "Underline", "Strikeout", "Squiggly Underline"]:
            self.width_spinbox.setValue(150)
            self.height_spinbox.setValue(20)
        elif annotation_type in ["Rectangle", "Circle"]:
            self.width_spinbox.setValue(100)
            self.height_spinbox.setValue(100)
        elif annotation_type == "Line":
            self.height_spinbox.setValue(1)  # Line thickness
    
    def choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(self.current_color, self, "Choose Annotation Color")
        if color.isValid():
            self.current_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}")
    
    def on_thickness_changed(self, thickness: int):
        """Handle thickness change."""
        self.current_thickness = thickness
    
    def add_annotation(self):
        """Add annotation to PDF."""
        annotation_type = self.annotation_type_combo.currentText()
        
        # Convert to operation format
        type_map = {
            "Highlight": "highlight",
            "Underline": "underline",
            "Strikeout": "strikeout",
            "Squiggly Underline": "squiggly",
            "Text Note": "text",
            "Rectangle": "rectangle",
            "Circle": "circle",
            "Line": "line",
            "Freehand Drawing": "freehand"
        }
        
        op_type = type_map[annotation_type]
        
        # Get position and size
        page = self.page_spinbox.value() - 1  # Convert to 0-based
        x = self.x_pos_spinbox.value()
        y = self.y_pos_spinbox.value()
        width = self.width_spinbox.value()
        height = self.height_spinbox.value()
        
        # Create rectangle (x0, y0, x1, y1)
        rect = (x, y, x + width, y + height)
        
        # Get content and author
        content = self.content_edit.toPlainText().strip()
        author = self.author_edit.text().strip()
        
        # Get color as RGB tuple
        color = (self.current_color.red(), self.current_color.green(), self.current_color.blue())
        
        # Get opacity
        opacity = self.opacity_spinbox.value() / 100.0
        
        # Emit operation request
        operation_data = {
            'name': 'add_annotation',
            'type': op_type,
            'page': page,
            'rect': rect,
            'content': content,
            'author': author or "PDF Editor",
            'color': color,
            'thickness': self.current_thickness,
            'opacity': opacity
        }
        
        self.emit_operation(operation_data)
        
        # Clear form
        self.clear_form()
    
    def clear_form(self):
        """Clear the annotation form."""
        self.content_edit.clear()
        self.author_edit.clear()
        
        # Reset to default values
        self.x_pos_spinbox.setValue(100)
        self.y_pos_spinbox.setValue(100)
        self.width_spinbox.setValue(100)
        self.height_spinbox.setValue(50)
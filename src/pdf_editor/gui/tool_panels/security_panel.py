"""Security panel for password protection and metadata."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFormLayout, QCheckBox,
    QTextEdit, QSpinBox, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt

from . import BaseToolPanel
from ...utils.logging import get_logger

logger = get_logger("gui.security_panel")


class SecurityPanel(BaseToolPanel):
    """Panel for security and metadata operations."""
    
    def __init__(self):
        super().__init__("Security")
    
    def setup_panel(self):
        """Setup the security panel."""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Password protection tab
        self.create_password_tab()
        
        # Metadata tab
        self.create_metadata_tab()
        
        # Watermark tab
        self.create_watermark_tab()
        
        # Actions tab
        self.create_actions_tab()
    
    def create_password_tab(self):
        """Create password protection tab."""
        password_tab = QWidget()
        password_layout = QVBoxLayout(password_tab)
        
        # Password group
        password_group = QGroupBox("Password Protection")
        password_form = QFormLayout()
        
        self.user_password_edit = QLineEdit()
        self.user_password_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.user_password_edit.setPlaceholderText("Password for opening")
        password_form.addRow("User Password:", self.user_password_edit)
        
        self.owner_password_edit = QLineEdit()
        self.owner_password_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.owner_password_edit.setPlaceholderText("Password for permissions")
        password_form.addRow("Owner Password:", self.owner_password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.confirm_password_edit.setPlaceholderText("Confirm user password")
        password_form.addRow("Confirm Password:", self.confirm_password_edit)
        
        password_group.setLayout(password_form)
        password_layout.addWidget(password_group)
        
        # Encryption settings
        encryption_group = QGroupBox("Encryption Settings")
        encryption_layout = QVBoxLayout()
        
        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems(["128-bit", "256-bit", "40-bit"])
        encryption_layout.addWidget(QLabel("Encryption Strength:"))
        encryption_layout.addWidget(self.encryption_combo)
        
        encryption_group.setLayout(encryption_layout)
        password_layout.addWidget(encryption_group)
        
        # Permissions
        permissions_group = QGroupBox("Permissions")
        permissions_layout = QVBoxLayout()
        
        self.print_perm_checkbox = QCheckBox("Allow printing")
        self.print_perm_checkbox.setChecked(True)
        permissions_layout.addWidget(self.print_perm_checkbox)
        
        self.modify_perm_checkbox = QCheckBox("Allow modifications")
        self.modify_perm_checkbox.setChecked(True)
        permissions_layout.addWidget(self.modify_perm_checkbox)
        
        self.copy_perm_checkbox = QCheckBox("Allow copying")
        self.copy_perm_checkbox.setChecked(True)
        permissions_layout.addWidget(self.copy_perm_checkbox)
        
        self.annotate_perm_checkbox = QCheckBox("Allow annotations")
        self.annotate_perm_checkbox.setChecked(True)
        permissions_layout.addWidget(self.annotate_perm_checkbox)
        
        self.form_fill_perm_checkbox = QCheckBox("Allow form filling")
        self.form_fill_perm_checkbox.setChecked(True)
        permissions_layout.addWidget(self.form_fill_perm_checkbox)
        
        permissions_group.setLayout(permissions_layout)
        password_layout.addWidget(permissions_group)
        
        # Set password button
        self.set_password_button = QPushButton("Set Password Protection")
        self.set_password_button.clicked.connect(self.set_password)
        password_layout.addWidget(self.set_password_button)
        
        password_layout.addStretch()
        self.tab_widget.addTab(password_tab, "Password")
    
    def create_metadata_tab(self):
        """Create metadata editing tab."""
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        
        # Basic metadata
        basic_group = QGroupBox("Basic Information")
        basic_form = QFormLayout()
        
        self.title_edit = QLineEdit()
        basic_form.addRow("Title:", self.title_edit)
        
        self.author_edit = QLineEdit()
        basic_form.addRow("Author:", self.author_edit)
        
        self.subject_edit = QLineEdit()
        basic_form.addRow("Subject:", self.subject_edit)
        
        self.keywords_edit = QLineEdit()
        basic_form.addRow("Keywords:", self.keywords_edit)
        
        self.creator_edit = QLineEdit()
        self.creator_edit.setText("PDF Editor")
        basic_form.addRow("Creator:", self.creator_edit)
        
        basic_group.setLayout(basic_form)
        metadata_layout.addWidget(basic_group)
        
        # Update metadata button
        self.update_metadata_button = QPushButton("Update Metadata")
        self.update_metadata_button.clicked.connect(self.update_metadata)
        metadata_layout.addWidget(self.update_metadata_button)
        
        metadata_layout.addStretch()
        self.tab_widget.addTab(metadata_tab, "Metadata")
    
    def create_watermark_tab(self):
        """Create watermark tab."""
        watermark_tab = QWidget()
        watermark_layout = QVBoxLayout(watermark_tab)
        
        # Watermark settings
        watermark_group = QGroupBox("Watermark Settings")
        watermark_form = QFormLayout()
        
        self.watermark_text_edit = QLineEdit()
        self.watermark_text_edit.setPlaceholderText("CONFIDENTIAL")
        watermark_form.addRow("Text:", self.watermark_text_edit)
        
        self.watermark_font_spinbox = QSpinBox()
        self.watermark_font_spinbox.setRange(8, 72)
        self.watermark_font_spinbox.setValue(24)
        watermark_form.addRow("Font Size:", self.watermark_font_spinbox)
        
        self.watermark_opacity_spinbox = QSpinBox()
        self.watermark_opacity_spinbox.setRange(10, 100)
        self.watermark_opacity_spinbox.setValue(20)
        watermark_form.addRow("Opacity (%):", self.watermark_opacity_spinbox)
        
        self.watermark_rotation_spinbox = QSpinBox()
        self.watermark_rotation_spinbox.setRange(0, 360)
        self.watermark_rotation_spinbox.setValue(45)
        watermark_form.addRow("Rotation (degrees):", self.watermark_rotation_spinbox)
        
        watermark_group.setLayout(watermark_form)
        watermark_layout.addWidget(watermark_group)
        
        # Add watermark button
        self.add_watermark_button = QPushButton("Add Watermark")
        self.add_watermark_button.clicked.connect(self.add_watermark)
        watermark_layout.addWidget(self.add_watermark_button)
        
        watermark_layout.addStretch()
        self.tab_widget.addTab(watermark_tab, "Watermark")
    
    def create_actions_tab(self):
        """Create actions tab for export operations."""
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        
        # Export operations
        export_group = QGroupBox("Export Operations")
        export_layout = QVBoxLayout()
        
        self.export_metadata_button = QPushButton("Export Metadata")
        self.export_metadata_button.clicked.connect(self.export_metadata)
        export_layout.addWidget(self.export_metadata_button)
        
        self.export_button = QPushButton("Export to Other Formats")
        self.export_button.clicked.connect(self.export_document)
        export_layout.addWidget(self.export_button)
        
        export_group.setLayout(export_layout)
        actions_layout.addWidget(export_group)
        
        # Digital signature
        signature_group = QGroupBox("Digital Signature")
        signature_layout = QVBoxLayout()
        
        self.add_signature_button = QPushButton("Add Digital Signature")
        self.add_signature_button.clicked.connect(self.add_signature)
        signature_layout.addWidget(self.add_signature_button)
        
        signature_group.setLayout(signature_layout)
        actions_layout.addWidget(signature_group)
        
        actions_layout.addStretch()
        self.tab_widget.addTab(actions_tab, "Actions")
    
    def set_password(self):
        """Set password protection."""
        user_password = self.user_password_edit.text()
        owner_password = self.owner_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if user_password and user_password != confirm_password:
            QMessageBox.warning(self, "Warning", "Passwords do not match")
            return
        
        if not user_password and not owner_password:
            QMessageBox.warning(self, "Warning", "Please enter at least one password")
            return
        
        # Get encryption strength
        encryption_map = {"128-bit": 128, "256-bit": 256, "40-bit": 40}
        encryption = encryption_map[self.encryption_combo.currentText()]
        
        # Get permissions
        permissions = {
            'print': self.print_perm_checkbox.isChecked(),
            'modify': self.modify_perm_checkbox.isChecked(),
            'copy': self.copy_perm_checkbox.isChecked(),
            'annotate': self.annotate_perm_checkbox.isChecked(),
            'form_fill': self.form_fill_perm_checkbox.isChecked()
        }
        
        # Emit operation request
        operation_data = {
            'name': 'set_password',
            'user_password': user_password,
            'owner_password': owner_password,
            'encryption': encryption,
            'permissions': permissions
        }
        
        self.emit_operation(operation_data)
    
    def update_metadata(self):
        """Update document metadata."""
        metadata = {}
        
        title = self.title_edit.text().strip()
        if title:
            metadata['title'] = title
        
        author = self.author_edit.text().strip()
        if author:
            metadata['author'] = author
        
        subject = self.subject_edit.text().strip()
        if subject:
            metadata['subject'] = subject
        
        keywords = self.keywords_edit.text().strip()
        if keywords:
            metadata['keywords'] = keywords
        
        creator = self.creator_edit.text().strip()
        if creator:
            metadata['creator'] = creator
        
        if not metadata:
            QMessageBox.warning(self, "Warning", "Please enter at least one metadata field")
            return
        
        # Emit operation request
        operation_data = {
            'name': 'edit_metadata',
            'metadata': metadata
        }
        
        self.emit_operation(operation_data)
    
    def add_watermark(self):
        """Add security watermark."""
        text = self.watermark_text_edit.text().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter watermark text")
            return
        
        # Emit operation request
        operation_data = {
            'name': 'add_watermark',
            'text': text,
            'font_size': self.watermark_font_spinbox.value(),
            'opacity': self.watermark_opacity_spinbox.value() / 100.0,
            'rotation': self.watermark_rotation_spinbox.value()
        }
        
        self.emit_operation(operation_data)
    
    def export_metadata(self):
        """Export document metadata."""
        operation_data = {
            'name': 'export_metadata',
            'format': 'json'  # Could be json, xml, text
        }
        self.emit_operation(operation_data)
    
    def export_document(self):
        """Export document to other formats."""
        operation_data = {
            'name': 'export_document',
            'format': 'png'  # Could be various formats
        }
        self.emit_operation(operation_data)
    
    def add_signature(self):
        """Add digital signature."""
        operation_data = {
            'name': 'add_signature',
            # Would include signature details
        }
        self.emit_operation(operation_data)
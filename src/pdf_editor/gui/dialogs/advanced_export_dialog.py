"""Advanced export GUI dialog."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QSpinBox,
    QCheckBox, QGroupBox, QTabWidget, QTextEdit,
    QProgressBar, QMessageBox, QFormLayout, QSlider
)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont

from ...core.editor import PDFEditor
from ...operations.advanced_export_operations import (
    ExportToWordOperation, ExportToExcelOperation, ExportToPowerPointOperation
)
from ...utils.logging import get_logger

logger = get_logger("gui.advanced_export")


class ExportWorker(QThread):
    """Worker thread for export operations."""
    progress_updated = pyqtSignal(int, str)
    export_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, operation_type: str, input_file: str, output_file: str, operation_params: dict):
        super().__init__()
        self.operation_type = operation_type
        self.input_file = input_file
        self.output_file = output_file
        self.operation_params = operation_params
    
    def run(self):
        """Run export operation."""
        try:
            editor = PDFEditor()
            editor.load_document(self.input_file)
            
            if self.operation_type == 'word':
                operation = ExportToWordOperation(
                    output_path=self.output_file,
                    preserve_formatting=self.operation_params.get('preserve_formatting', True),
                    extract_images=self.operation_params.get('extract_images', True),
                    page_breaks=self.operation_params.get('page_breaks', True)
                )
            elif self.operation_type == 'excel':
                operation = ExportToExcelOperation(
                    output_path=self.output_file,
                    export_type=self.operation_params.get('export_type', 'form_data'),
                    include_metadata=self.operation_params.get('include_metadata', True)
                )
            elif self.operation_type == 'powerpoint':
                operation = ExportToPowerPointOperation(
                    output_path=self.output_file,
                    one_slide_per_page=self.operation_params.get('one_slide_per_page', True),
                    slide_size=self.operation_params.get('slide_size', 'standard_4_3'),
                    extract_images=self.operation_params.get('extract_images', True)
                )
            else:
                self.error_occurred.emit(f"Unknown export type: {self.operation_type}")
                return
            
            editor.add_operation(operation)
            result = editor.execute_operations()
            editor.save_document(self.output_file)
            
            self.export_completed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            logger.error(f"Export operation error: {e}")


class AdvancedExportDialog(QDialog):
    """Dialog for advanced PDF export operations."""
    
    def __init__(self, current_file: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Export")
        self.setModal(True)
        self.resize(600, 500)
        
        self.current_file = current_file
        self.export_worker = None
        
        self.init_ui()
        
        logger.info("Advanced export dialog initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Current file display
        if self.current_file:
            file_group = QGroupBox("Current File")
            file_layout = QVBoxLayout(file_group)
            
            file_label = QLabel(Path(self.current_file).name)
            file_label.setFont(QFont("Courier", 10))
            file_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
            file_layout.addWidget(file_label)
            
            layout.addWidget(file_group)
        
        # Create tab widget for different export options
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create export tabs
        self.create_word_export_tab()
        self.create_excel_export_tab()
        self.create_powerpoint_export_tab()
        self.create_batch_export_tab()
        
        # Progress and status
        self.create_progress_section(layout)
        
        # Control buttons
        self.create_control_buttons(layout)
    
    def create_word_export_tab(self):
        """Create Word export tab."""
        word_widget = QWidget()
        layout = QVBoxLayout(word_widget)
        
        # Word export options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        # Formatting options
        format_group = QGroupBox("Formatting")
        format_layout = QVBoxLayout(format_group)
        
        self.preserve_formatting_checkbox = QCheckBox("Preserve text formatting")
        self.preserve_formatting_checkbox.setChecked(True)
        format_layout.addWidget(self.preserve_formatting_checkbox)
        
        self.extract_images_checkbox = QCheckBox("Extract and embed images")
        self.extract_images_checkbox.setChecked(True)
        format_layout.addWidget(self.extract_images_checkbox)
        
        self.page_breaks_checkbox = QCheckBox("Add page breaks")
        self.page_breaks_checkbox.setChecked(True)
        format_layout.addWidget(self.page_breaks_checkbox)
        
        options_layout.addWidget(format_group)
        
        # Content options
        content_group = QGroupBox("Content")
        content_layout = QVBoxLayout(content_group)
        
        self.include_annotations_checkbox = QCheckBox("Include annotations")
        self.include_annotations_checkbox.setChecked(False)
        content_layout.addWidget(self.include_annotations_checkbox)
        
        self.include_form_data_checkbox = QCheckBox("Include form field data")
        self.include_form_data_checkbox.setChecked(True)
        content_layout.addWidget(self.include_form_data_checkbox)
        
        self.include_metadata_checkbox = QCheckBox("Include document metadata")
        self.include_metadata_checkbox.setChecked(True)
        content_layout.addWidget(self.include_metadata_checkbox)
        
        options_layout.addWidget(content_group)
        
        layout.addWidget(options_group)
        
        # Export button
        self.export_word_btn = QPushButton("Export to Word (.docx)")
        self.export_word_btn.clicked.connect(self.export_to_word)
        layout.addWidget(self.export_word_btn)
        
        self.tab_widget.addTab(word_widget, "Word")
    
    def create_excel_export_tab(self):
        """Create Excel export tab."""
        excel_widget = QWidget()
        layout = QVBoxLayout(excel_widget)
        
        # Export type selection
        type_group = QGroupBox("Export Type")
        type_layout = QFormLayout(type_group)
        
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(["form_data", "table_data", "text_blocks"])
        self.export_type_combo.setCurrentText("form_data")
        type_layout.addRow("Export Data:", self.export_type_combo)
        
        layout.addWidget(type_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_sheet_headers_checkbox = QCheckBox("Include sheet headers")
        self.include_sheet_headers_checkbox.setChecked(True)
        options_layout.addWidget(self.include_sheet_headers_checkbox)
        
        self.merge_sheets_checkbox = QCheckBox("Merge multiple sheets")
        self.merge_sheets_checkbox.setChecked(False)
        options_layout.addWidget(self.merge_sheets_checkbox)
        
        self.format_dates_checkbox = QCheckBox("Format dates as dates")
        self.format_dates_checkbox.setChecked(True)
        options_layout.addWidget(self.format_dates_checkbox)
        
        layout.addWidget(options_group)
        
        # Export button
        self.export_excel_btn = QPushButton("Export to Excel (.xlsx)")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_excel_btn)
        
        self.tab_widget.addTab(excel_widget, "Excel")
    
    def create_powerpoint_export_tab(self):
        """Create PowerPoint export tab."""
        ppt_widget = QWidget()
        layout = QVBoxLayout(ppt_widget)
        
        # Slide options
        slide_group = QGroupBox("Slide Options")
        slide_layout = QVBoxLayout(slide_group)
        
        self.one_slide_per_page_checkbox = QCheckBox("One slide per page")
        self.one_slide_per_page_checkbox.setChecked(True)
        slide_layout.addWidget(self.one_slide_per_page_checkbox)
        
        # Slide size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Slide Size:"))
        
        self.slide_size_combo = QComboBox()
        self.slide_size_combo.addItems(["standard_4_3", "standard_16_9", "widescreen", "a4"])
        self.slide_size_combo.setCurrentText("standard_4_3")
        size_layout.addWidget(self.slide_size_combo)
        
        size_layout.addStretch()
        slide_layout.addLayout(size_layout)
        
        # Content options
        content_layout = QVBoxLayout()
        
        self.ppt_extract_images_checkbox = QCheckBox("Extract high-quality images")
        self.ppt_extract_images_checkbox.setChecked(True)
        content_layout.addWidget(self.ppt_extract_images_checkbox)
        
        self.ppt_preserve_animations_checkbox = QCheckBox("Preserve animations (if present)")
        self.ppt_preserve_animations_checkbox.setChecked(False)
        content_layout.addWidget(self.ppt_preserve_animations_checkbox)
        
        slide_layout.addLayout(content_layout)
        
        layout.addWidget(slide_group)
        
        # Export button
        self.export_powerpoint_btn = QPushButton("Export to PowerPoint (.pptx)")
        self.export_powerpoint_btn.clicked.connect(self.export_to_powerpoint)
        layout.addWidget(self.export_powerpoint_btn)
        
        self.tab_widget.addTab(ppt_widget, "PowerPoint")
    
    def create_batch_export_tab(self):
        """Create batch export tab."""
        batch_widget = QWidget()
        layout = QVBoxLayout(batch_widget)
        
        # Batch export options
        batch_group = QGroupBox("Batch Export")
        batch_layout = QVBoxLayout(batch_group)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Export Format:"))
        
        self.batch_format_combo = QComboBox()
        self.batch_format_combo.addItems(["All Formats", "Word Only", "Excel Only", "PowerPoint Only"])
        format_layout.addWidget(self.batch_format_combo)
        format_layout.addStretch()
        batch_layout.addLayout(format_layout)
        
        # Output directory
        output_layout = QHBoxLayout()
        self.batch_output_edit = QLineEdit()
        self.batch_output_edit.setPlaceholderText("Select output directory...")
        output_layout.addWidget(self.batch_output_edit)
        
        self.browse_batch_output_btn = QPushButton("Browse...")
        self.browse_batch_output_btn.clicked.connect(self.browse_batch_output)
        output_layout.addWidget(self.browse_batch_output_btn)
        
        batch_layout.addLayout(output_layout)
        
        # Options
        options_layout = QVBoxLayout()
        
        self.create_subdirs_checkbox = QCheckBox("Create subdirectories for each format")
        self.create_subdirs_checkbox.setChecked(True)
        options_layout.addWidget(self.create_subdirs_checkbox)
        
        self.include_timestamp_checkbox = QCheckBox("Include timestamp in filenames")
        self.include_timestamp_checkbox.setChecked(False)
        options_layout.addWidget(self.include_timestamp_checkbox)
        
        batch_layout.addLayout(options_layout)
        
        layout.addWidget(batch_group)
        
        # Batch export button
        self.batch_export_btn = QPushButton("Batch Export All Formats")
        self.batch_export_btn.clicked.connect(self.batch_export_all)
        layout.addWidget(self.batch_export_btn)
        
        self.tab_widget.addTab(batch_widget, "Batch Export")
    
    def create_progress_section(self, layout):
        """Create progress section."""
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.export_progress_bar = QProgressBar()
        self.export_progress_bar.setVisible(False)
        progress_layout.addWidget(self.export_progress_bar)
        
        self.export_status_label = QLabel("Ready to export")
        progress_layout.addWidget(self.export_status_label)
        
        layout.addWidget(progress_group)
    
    def create_control_buttons(self, layout):
        """Create control buttons."""
        buttons_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_export)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def browse_batch_output(self):
        """Browse for batch output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.batch_output_edit.setText(directory)
    
    def export_to_word(self):
        """Export to Word format."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No file currently open")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Save Word Document", 
            Path(self.current_file).stem + ".docx",
            "Word Documents (*.docx)"
        )
        
        if output_file:
            self.start_export('word', output_file, {
                'preserve_formatting': self.preserve_formatting_checkbox.isChecked(),
                'extract_images': self.extract_images_checkbox.isChecked(),
                'page_breaks': self.page_breaks_checkbox.isChecked()
            })
    
    def export_to_excel(self):
        """Export to Excel format."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No file currently open")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Save Excel Document",
            Path(self.current_file).stem + ".xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if output_file:
            self.start_export('excel', output_file, {
                'export_type': self.export_type_combo.currentText(),
                'include_metadata': self.include_metadata_checkbox.isChecked()
            })
    
    def export_to_powerpoint(self):
        """Export to PowerPoint format."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No file currently open")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Save PowerPoint Document",
            Path(self.current_file).stem + ".pptx",
            "PowerPoint Files (*.pptx)"
        )
        
        if output_file:
            self.start_export('powerpoint', output_file, {
                'one_slide_per_page': self.one_slide_per_page_checkbox.isChecked(),
                'slide_size': self.slide_size_combo.currentText(),
                'extract_images': self.ppt_extract_images_checkbox.isChecked()
            })
    
    def batch_export_all(self):
        """Export to all formats."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No file currently open")
            return
        
        if not self.batch_output_edit.text():
            QMessageBox.warning(self, "Warning", "Please select output directory")
            return
        
        # Get export formats
        format_selection = self.batch_format_combo.currentText()
        
        exports = []
        if format_selection in ["All Formats", "Word Only"]:
            exports.append(('word', '.docx'))
        if format_selection in ["All Formats", "Excel Only"]:
            exports.append(('excel', '.xlsx'))
        if format_selection in ["All Formats", "PowerPoint Only"]:
            exports.append(('powerpoint', '.pptx'))
        
        # Export each format
        output_base = Path(self.batch_output_edit.text())
        create_subdirs = self.create_subdirs_checkbox.isChecked()
        include_timestamp = self.include_timestamp_checkbox.isChecked()
        
        for export_type, extension in exports:
            if create_subdirs:
                format_dir = output_base / export_type.upper()
                format_dir.mkdir(exist_ok=True)
            else:
                format_dir = output_base
            
            timestamp = ""
            if include_timestamp:
                from datetime import datetime
                timestamp = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            output_file = format_dir / f"{Path(self.current_file).stem}{timestamp}{extension}"
            
            # Start export (simplified - would need proper queueing)
            if export_type == 'word':
                params = {
                    'preserve_formatting': True,
                    'extract_images': True,
                    'page_breaks': True
                }
            elif export_type == 'excel':
                params = {
                    'export_type': 'form_data',
                    'include_metadata': True
                }
            elif export_type == 'powerpoint':
                params = {
                    'one_slide_per_page': True,
                    'slide_size': 'standard_4_3',
                    'extract_images': True
                }
            
            self.start_export(export_type, str(output_file), params)
        
        QMessageBox.information(self, "Batch Export", 
                           f"Started {len(exports)} export operations in the background.")
    
    def start_export(self, export_type: str, output_file: str, params: dict):
        """Start export operation."""
        # Update UI
        self.export_progress_bar.setVisible(True)
        self.export_progress_bar.setRange(0, 0)  # Indeterminate
        self.export_status_label.setText(f"Exporting to {export_type.upper()}...")
        
        # Disable controls
        self.setControlsEnabled(False)
        
        # Start export worker
        self.export_worker = ExportWorker(export_type, self.current_file, output_file, params)
        
        self.export_worker.progress_updated.connect(self.on_export_progress)
        self.export_worker.export_completed.connect(self.on_export_completed)
        self.export_worker.error_occurred.connect(self.on_export_error)
        
        self.export_worker.start()
    
    def cancel_export(self):
        """Cancel export operation."""
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.terminate()
            self.export_worker.wait()
            self.reset_export_ui()
            self.export_status_label.setText("Export cancelled")
    
    def on_export_progress(self, progress: int, message: str):
        """Handle export progress updates."""
        self.export_status_label.setText(message)
        if progress >= 0:
            self.export_progress_bar.setRange(0, 100)
            self.export_progress_bar.setValue(progress)
    
    def on_export_completed(self, result: dict):
        """Handle export completion."""
        self.reset_export_ui()
        self.export_status_label.setText("Export completed successfully!")
        
        # Show completion details
        details = f"Export Type: {result.get('operation', 'Unknown')}\\n"
        details += f"Pages Processed: {result.get('pages_processed', 0)}\\n"
        details += f"Images Extracted: {result.get('images_extracted', 0)}\\n"
        details += f"File Size: {result.get('file_size', 0):,} bytes"
        
        QMessageBox.information(self, "Export Complete", details)
    
    def on_export_error(self, error: str):
        """Handle export error."""
        self.reset_export_ui()
        self.export_status_label.setText("Export failed!")
        QMessageBox.critical(self, "Export Error", f"Export failed: {error}")
    
    def reset_export_ui(self):
        """Reset export UI state."""
        self.export_progress_bar.setVisible(False)
        self.export_progress_bar.setRange(0, 100)
        self.setControlsEnabled(True)
    
    def setControlsEnabled(self, enabled: bool):
        """Enable/disable controls."""
        self.export_word_btn.setEnabled(enabled)
        self.export_excel_btn.setEnabled(enabled)
        self.export_powerpoint_btn.setEnabled(enabled)
        self.batch_export_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)  # Enable cancel during export
    
    def close(self):
        """Close dialog with cleanup."""
        if self.export_worker and self.export_worker.isRunning():
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Export is still in progress. Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            self.cancel_export()
        
        super().close()
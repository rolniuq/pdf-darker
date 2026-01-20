"""Batch processing GUI dialog."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QSpinBox,
    QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QCheckBox, QTabWidget,
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont

from ...core.editor import PDFEditor
from ...operations.batch_operations import BatchProcessOperation, BatchTemplateOperation
from ...utils.logging import get_logger

logger = get_logger("gui.batch_dialog")


class BatchWorker(QThread):
    """Worker thread for batch processing."""
    progress_updated = pyqtSignal(int, str)  # progress, message
    task_completed = pyqtSignal(dict)  # task result
    batch_completed = pyqtSignal(dict)  # batch result
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, operations: List[Dict], input_files: List[str], output_dir: str, max_workers: int = 4):
        super().__init__()
        self.operations = operations
        self.input_files = input_files
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.should_stop = False
    
    def run(self):
        """Run batch processing."""
        try:
            # Create PDF editor for batch processing
            editor = PDFEditor()
            
            # Create batch operation
            from pathlib import Path
            input_pattern = str(Path(self.input_files[0]).parent / "*.pdf") if self.input_files else "*.pdf"
            
            batch_op = BatchProcessOperation(
                input_pattern=input_pattern,
                output_dir=self.output_dir,
                operations=self.operations,
                max_workers=self.max_workers
            )
            
            # Validate and execute
            batch_op.validate(editor)
            result = batch_op.execute(editor)
            
            self.batch_completed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            logger.error(f"Batch processing error: {e}")
    
    def stop(self):
        """Stop batch processing."""
        self.should_stop = True


class BatchProcessingDialog(QDialog):
    """Dialog for batch processing of PDF files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing")
        self.setModal(True)
        self.resize(900, 700)
        
        self.operations = []
        self.input_files = []
        self.batch_worker = None
        
        self.init_ui()
        
        logger.info("Batch processing dialog initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_files_tab()
        self.create_operations_tab()
        self.create_templates_tab()
        self.create_settings_tab()
        
        # Control buttons
        self.create_control_buttons(layout)
    
    def create_files_tab(self):
        """Create files selection tab."""
        files_widget = QWidget()
        layout = QVBoxLayout(files_widget)
        
        # Input files selection
        files_group = QGroupBox("Input Files")
        files_layout = QVBoxLayout(files_group)
        
        # Files selection area
        files_sel_layout = QHBoxLayout()
        
        self.files_list = QTableWidget()
        self.files_list.setColumnCount(3)
        self.files_list.setHorizontalHeaderLabels(["File Name", "Size", "Path"])
        self.files_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.files_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        files_sel_layout.addWidget(self.files_list, 1)
        
        # Files selection buttons
        files_btn_layout = QVBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files...")
        self.add_files_btn.clicked.connect(self.add_files)
        files_btn_layout.addWidget(self.add_files_btn)
        
        self.add_folder_btn = QPushButton("Add Folder...")
        self.add_folder_btn.clicked.connect(self.add_folder)
        files_btn_layout.addWidget(self.add_folder_btn)
        
        self.clear_files_btn = QPushButton("Clear All")
        self.clear_files_btn.clicked.connect(self.clear_files)
        files_btn_layout.addWidget(self.clear_files_btn)
        
        files_btn_layout.addStretch()
        
        files_sel_layout.addLayout(files_btn_layout)
        files_layout.addLayout(files_sel_layout)
        
        # File count label
        self.file_count_label = QLabel("0 files selected")
        files_layout.addWidget(self.file_count_label)
        
        layout.addWidget(files_group)
        
        # Output directory selection
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory...")
        output_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        output_layout.addWidget(self.browse_output_btn)
        
        layout.addWidget(output_group)
        
        self.tab_widget.addTab(files_widget, "Files")
    
    def create_operations_tab(self):
        """Create operations configuration tab."""
        ops_widget = QWidget()
        layout = QVBoxLayout(ops_widget)
        
        # Operations list
        ops_group = QGroupBox("Operations")
        ops_layout = QVBoxLayout(ops_group)
        
        # Operations table
        self.operations_table = QTableWidget()
        self.operations_table.setColumnCount(4)
        self.operations_table.setHorizontalHeaderLabels(["Type", "Parameters", "Enabled", "Actions"])
        self.operations_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.operations_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.operations_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.operations_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        ops_layout.addWidget(self.operations_table)
        
        # Operations buttons
        ops_btn_layout = QHBoxLayout()
        
        self.add_operation_btn = QPushButton("Add Operation...")
        self.add_operation_btn.clicked.connect(self.add_operation)
        ops_btn_layout.addWidget(self.add_operation_btn)
        
        self.add_sequence_btn = QPushButton("Add Sequence...")
        self.add_sequence_btn.clicked.connect(self.add_sequence)
        ops_btn_layout.addWidget(self.add_sequence_btn)
        
        self.remove_operation_btn = QPushButton("Remove Selected")
        self.remove_operation_btn.clicked.connect(self.remove_operation)
        ops_btn_layout.addWidget(self.remove_operation_btn)
        
        self.clear_operations_btn = QPushButton("Clear All")
        self.clear_operations_btn.clicked.connect(self.clear_operations)
        ops_btn_layout.addWidget(self.clear_operations_btn)
        
        ops_btn_layout.addStretch()
        ops_layout.addLayout(ops_btn_layout)
        
        layout.addWidget(ops_group)
        
        self.tab_widget.addTab(ops_widget, "Operations")
    
    def create_templates_tab(self):
        """Create templates tab."""
        templates_widget = QWidget()
        layout = QVBoxLayout(templates_widget)
        
        # Templates selection
        template_group = QGroupBox("Predefined Templates")
        template_layout = QVBoxLayout(template_group)
        
        self.templates_combo = QComboBox()
        self.templates_combo.addItem("Select a template...")
        self.load_templates()
        template_layout.addWidget(self.templates_combo)
        
        # Template info
        self.template_info = QTextEdit()
        self.template_info.setMaximumHeight(150)
        self.template_info.setPlaceholderText("Template information will appear here...")
        template_layout.addWidget(self.template_info)
        
        # Template parameters
        params_layout = QHBoxLayout()
        
        self.use_template_btn = QPushButton("Use Template")
        self.use_template_btn.clicked.connect(self.use_template)
        params_layout.addWidget(self.use_template_btn)
        
        self.save_template_btn = QPushButton("Save as Template")
        self.save_template_btn.clicked.connect(self.save_as_template)
        params_layout.addWidget(self.save_template_btn)
        
        params_layout.addStretch()
        template_layout.addLayout(params_layout)
        
        layout.addWidget(template_group)
        
        self.tab_widget.addTab(templates_widget, "Templates")
    
    def create_settings_tab(self):
        """Create settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Processing settings
        processing_group = QGroupBox("Processing Settings")
        processing_layout = QVBoxLayout(processing_group)
        
        # Workers setting
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("Max Workers:"))
        
        self.max_workers_spinbox = QSpinBox()
        self.max_workers_spinbox.setRange(1, 16)
        self.max_workers_spinbox.setValue(4)
        workers_layout.addWidget(self.max_workers_spinbox)
        
        workers_layout.addStretch()
        processing_layout.addLayout(workers_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.continue_on_error_checkbox = QCheckBox("Continue on Error")
        self.continue_on_error_checkbox.setChecked(True)
        options_layout.addWidget(self.continue_on_error_checkbox)
        
        self.preserve_structure_checkbox = QCheckBox("Preserve Directory Structure")
        self.preserve_structure_checkbox.setChecked(True)
        options_layout.addWidget(self.preserve_structure_checkbox)
        
        options_layout.addStretch()
        processing_layout.addLayout(options_layout)
        
        layout.addWidget(processing_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout(output_group)
        
        # Report options
        report_layout = QHBoxLayout()
        
        self.generate_report_checkbox = QCheckBox("Generate Report")
        self.generate_report_checkbox.setChecked(True)
        report_layout.addWidget(self.generate_report_checkbox)
        
        self.report_format_combo = QComboBox()
        self.report_format_combo.addItems(["JSON", "CSV", "HTML"])
        report_layout.addWidget(QLabel("Format:"))
        report_layout.addWidget(self.report_format_combo)
        
        report_layout.addStretch()
        output_layout.addLayout(report_layout)
        
        layout.addWidget(output_group)
        
        self.tab_widget.addTab(settings_widget, "Settings")
    
    def create_control_buttons(self, layout):
        """Create control buttons."""
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.clicked.connect(self.start_processing)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def load_templates(self):
        """Load available templates."""
        templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
        
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r') as f:
                        template = json.load(f)
                        template_name = template.get('name', template_file.stem)
                        self.templates_combo.addItem(template_name, template_file)
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")
    
    def add_files(self):
        """Add individual files."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        
        if files:
            for file_path in files:
                self.add_file_to_list(file_path)
            self.update_file_count()
    
    def add_folder(self):
        """Add all PDFs from a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folder:
            folder_path = Path(folder)
            for pdf_file in folder_path.glob("*.pdf"):
                self.add_file_to_list(str(pdf_file))
            self.update_file_count()
    
    def add_file_to_list(self, file_path: str):
        """Add a file to the list."""
        if file_path not in self.input_files:
            self.input_files.append(file_path)
            
            path_obj = Path(file_path)
            row = self.files_list.rowCount()
            self.files_list.insertRow(row)
            
            self.files_list.setItem(row, 0, QTableWidgetItem(path_obj.name))
            self.files_list.setItem(row, 1, QTableWidgetItem(f"{path_obj.stat().st_size:,} bytes"))
            self.files_list.setItem(row, 2, QTableWidgetItem(file_path))
    
    def clear_files(self):
        """Clear all files."""
        self.input_files.clear()
        self.files_list.setRowCount(0)
        self.update_file_count()
    
    def update_file_count(self):
        """Update file count label."""
        count = len(self.input_files)
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''} selected")
    
    def browse_output_directory(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_edit.setText(directory)
    
    def add_operation(self):
        """Add a new operation."""
        # For now, add a simple dark mode operation
        operation = {
            'type': 'dark_mode',
            'parameters': {
                'dpi': 300,
                'quality': 95,
                'preserve_text': True
            },
            'enabled': True
        }
        self.add_operation_to_list(operation)
    
    def add_sequence(self):
        """Add a sequence of operations."""
        QMessageBox.information(self, "Coming Soon", "Operation sequences coming soon!")
    
    def add_operation_to_list(self, operation: Dict):
        """Add operation to the list."""
        row = self.operations_table.rowCount()
        self.operations_table.insertRow(row)
        
        # Type
        self.operations_table.setItem(row, 0, QTableWidgetItem(operation['type']))
        
        # Parameters
        params_str = json.dumps(operation['parameters'], indent=2)[:100] + "..."
        self.operations_table.setItem(row, 1, QTableWidgetItem(params_str))
        
        # Enabled checkbox
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(operation.get('enabled', True))
        self.operations_table.setCellWidget(row, 2, enabled_checkbox)
        
        # Actions
        actions_btn = QPushButton("Configure")
        actions_btn.clicked.connect(lambda: self.configure_operation(operation))
        self.operations_table.setCellWidget(row, 3, actions_btn)
        
        self.operations.append(operation)
    
    def configure_operation(self, operation: Dict):
        """Configure an operation (placeholder)."""
        QMessageBox.information(self, "Configure Operation", 
                           f"Configuration for {operation['type']} operation coming soon!")
    
    def remove_operation(self):
        """Remove selected operation."""
        current_row = self.operations_table.currentRow()
        if current_row >= 0:
            self.operations_table.removeRow(current_row)
            if current_row < len(self.operations):
                del self.operations[current_row]
    
    def clear_operations(self):
        """Clear all operations."""
        self.operations.clear()
        self.operations_table.setRowCount(0)
    
    def use_template(self):
        """Use selected template."""
        if self.templates_combo.currentIndex() > 0:
            template_file = self.templates_combo.currentData()
            if template_file:
                try:
                    with open(template_file, 'r') as f:
                        template = json.load(f)
                    
                    # Display template info
                    info_text = f"Name: {template.get('name', 'Unknown')}\\n"
                    info_text += f"Description: {template.get('description', 'No description')}\\n"
                    info_text += f"Operations: {len(template.get('operations', []))}"
                    self.template_info.setPlainText(info_text)
                    
                    # Load template operations
                    self.clear_operations()
                    for operation in template.get('operations', []):
                        self.add_operation_to_list(operation)
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to load template: {e}")
    
    def save_as_template(self):
        """Save current operations as template."""
        QMessageBox.information(self, "Coming Soon", "Save as template coming soon!")
    
    def start_processing(self):
        """Start batch processing."""
        if not self.input_files:
            QMessageBox.warning(self, "Warning", "No input files selected")
            return
        
        if not self.operations:
            QMessageBox.warning(self, "Warning", "No operations configured")
            return
        
        if not self.output_dir_edit.text():
            QMessageBox.warning(self, "Warning", "No output directory selected")
            return
        
        # Get enabled operations
        enabled_operations = []
        for i, operation in enumerate(self.operations):
            checkbox = self.operations_table.cellWidget(i, 2)
            if checkbox and checkbox.isChecked():
                enabled_operations.append(operation)
        
        if not enabled_operations:
            QMessageBox.warning(self, "Warning", "No operations enabled")
            return
        
        # Start processing
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Starting batch processing...")
        
        # Create and start worker
        self.batch_worker = BatchWorker(
            operations=enabled_operations,
            input_files=self.input_files,
            output_dir=self.output_dir_edit.text(),
            max_workers=self.max_workers_spinbox.value()
        )
        
        self.batch_worker.progress_updated.connect(self.on_progress_updated)
        self.batch_worker.task_completed.connect(self.on_task_completed)
        self.batch_worker.batch_completed.connect(self.on_batch_completed)
        self.batch_worker.error_occurred.connect(self.on_error_occurred)
        
        self.batch_worker.start()
    
    def stop_processing(self):
        """Stop batch processing."""
        if self.batch_worker:
            self.batch_worker.stop()
            self.batch_worker.wait()
        
        self.reset_ui_state()
        self.status_label.setText("Processing stopped")
    
    def on_progress_updated(self, progress: int, message: str):
        """Handle progress updates."""
        self.status_label.setText(message)
        if progress >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
    
    def on_task_completed(self, result: dict):
        """Handle task completion."""
        logger.info(f"Task completed: {result}")
    
    def on_batch_completed(self, result: dict):
        """Handle batch completion."""
        self.reset_ui_state()
        self.status_label.setText(f"Completed: {result.get('successful', 0)} successful, {result.get('failed', 0)} failed")
        
        # Generate report if requested
        if self.generate_report_checkbox.isChecked():
            self.generate_report(result)
        
        # Show completion dialog
        self.show_completion_dialog(result)
    
    def on_error_occurred(self, error: str):
        """Handle processing error."""
        self.reset_ui_state()
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Processing Error", f"Batch processing failed: {error}")
    
    def reset_ui_state(self):
        """Reset UI state after processing."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
    
    def generate_report(self, result: dict):
        """Generate processing report."""
        output_dir = Path(self.output_dir_edit.text())
        report_format = self.report_format_combo.currentText().lower()
        report_file = output_dir / f"batch_report.{report_format}"
        
        try:
            if report_format == 'json':
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2)
            elif report_format == 'csv':
                # Simple CSV report
                with open(report_file, 'w') as f:
                    f.write("Status,File,Time\\n")
                    for res in result.get('results', []):
                        status = "Success" if res.get('success') else "Failed"
                        file_name = res.get('task', {}).get('input_file', 'Unknown')
                        time_taken = str(res.get('processing_time', 0))
                        f.write(f"{status},{file_name},{time_taken}\\n")
            # HTML report would need more implementation
            
            logger.info(f"Report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
    
    def show_completion_dialog(self, result: dict):
        """Show completion dialog."""
        QMessageBox.information(
            self, 
            "Batch Processing Complete",
            f"Processing completed successfully!\\n\\n"
            f"Total files: {result.get('total_files', 0)}\\n"
            f"Successful: {result.get('successful', 0)}\\n"
            f"Failed: {result.get('failed', 0)}\\n"
            f"Total time: {result.get('total_time', 0):.2f} seconds"
        )
    
    def close(self):
        """Close dialog with cleanup."""
        if self.batch_worker and self.batch_worker.isRunning():
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Batch processing is still running. Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            self.stop_processing()
        
        super().close()
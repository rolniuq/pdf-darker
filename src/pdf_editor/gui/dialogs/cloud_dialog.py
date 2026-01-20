"""Cloud storage integration GUI components."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QTreeWidget,
    QTreeWidgetItem, QProgressBar, QMessageBox, QGroupBox,
    QTabWidget, QTextEdit, QCheckBox, QFormLayout,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from PySide6.QtGui import QIcon, QFont

from ...core.editor import PDFEditor
from ...operations.cloud_operations import (
    CloudUploadOperation, CloudDownloadOperation, CloudListOperation
)
from ...utils.logging import get_logger

logger = get_logger("gui.cloud_integration")


class CloudWorker(QThread):
    """Worker thread for cloud operations."""
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, operation_type: str, operation_data: dict, config: dict):
        super().__init__()
        self.operation_type = operation_type
        self.operation_data = operation_data
        self.config = config
    
    def run(self):
        """Run cloud operation."""
        try:
            editor = PDFEditor()
            
            if self.operation_type == 'upload':
                operation = CloudUploadOperation(
                    local_path=self.operation_data['local_path'],
                    provider=self.operation_data['provider'],
                    cloud_path=self.operation_data['cloud_path'],
                    config=self.config
                )
            elif self.operation_type == 'download':
                operation = CloudDownloadOperation(
                    file_id=self.operation_data['file_id'],
                    local_path=self.operation_data['local_path'],
                    provider=self.operation_data['provider'],
                    config=self.config
                )
            elif self.operation_type == 'list':
                operation = CloudListOperation(
                    provider=self.operation_data['provider'],
                    config=self.config
                )
            else:
                self.error_occurred.emit(f"Unknown operation type: {self.operation_type}")
                return
            
            self.operation_completed.emit(operation.execute(editor))
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            logger.error(f"Cloud operation error: {e}")


class CloudStorageDialog(QDialog):
    """Dialog for cloud storage operations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cloud Storage")
        self.setModal(True)
        self.resize(800, 600)
        
        self.config = {}
        self.cloud_worker = None
        self.current_provider = None
        
        self.init_ui()
        self.load_config()
        
        logger.info("Cloud storage dialog initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_config_tab()
        self.create_browser_tab()
        self.create_upload_tab()
        self.create_download_tab()
        
        # Control buttons
        self.create_control_buttons(layout)
    
    def create_config_tab(self):
        """Create configuration tab."""
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        
        # Provider selection
        provider_group = QGroupBox("Cloud Provider")
        provider_layout = QVBoxLayout(provider_group)
        
        provider_select_layout = QHBoxLayout()
        provider_select_layout.addWidget(QLabel("Provider:"))
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Google Drive", "Dropbox"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_select_layout.addWidget(self.provider_combo)
        provider_select_layout.addStretch()
        
        provider_layout.addLayout(provider_select_layout)
        
        # Provider-specific configuration
        self.config_form = QFormLayout()
        
        # Google Drive fields
        self.google_client_id_edit = QLineEdit()
        self.google_client_id_edit.setPlaceholderText("Google Client ID")
        self.config_form.addRow("Google Client ID:", self.google_client_id_edit)
        
        self.google_client_secret_edit = QLineEdit()
        self.google_client_secret_edit.setPlaceholderText("Google Client Secret")
        self.config_form.addRow("Google Client Secret:", self.google_client_secret_edit)
        
        # Dropbox fields
        self.dropbox_app_key_edit = QLineEdit()
        self.dropbox_app_key_edit.setPlaceholderText("Dropbox App Key")
        self.config_form.addRow("Dropbox App Key:", self.dropbox_app_key_edit)
        
        self.dropbox_app_secret_edit = QLineEdit()
        self.dropbox_app_secret_edit.setPlaceholderText("Dropbox App Secret")
        self.config_form.addRow("Dropbox App Secret:", self.dropbox_app_secret_edit)
        
        provider_layout.addLayout(self.config_form)
        
        # Auth buttons
        auth_layout = QHBoxLayout()
        
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        auth_layout.addWidget(self.test_connection_btn)
        
        self.save_config_btn = QPushButton("Save Configuration")
        self.save_config_btn.clicked.connect(self.save_config)
        auth_layout.addWidget(self.save_config_btn)
        
        auth_layout.addStretch()
        provider_layout.addLayout(auth_layout)
        
        layout.addWidget(provider_group)
        
        # Connection status
        self.connection_status_label = QLabel("Not connected")
        self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.connection_status_label)
        
        self.tab_widget.addTab(config_widget, "Configuration")
    
    def create_browser_tab(self):
        """Create cloud file browser tab."""
        browser_widget = QWidget()
        layout = QVBoxLayout(browser_widget)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_file_list)
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.create_folder_btn = QPushButton("📁 New Folder")
        self.create_folder_btn.clicked.connect(self.create_folder)
        toolbar_layout.addWidget(self.create_folder_btn)
        
        toolbar_layout.addStretch()
        
        # Current path display
        self.current_path_label = QLabel("/")
        self.current_path_label.setFont(QFont("Courier", 10))
        toolbar_layout.addWidget(self.current_path_label)
        
        layout.addLayout(toolbar_layout)
        
        # File browser
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Size", "Modified", "Type"])
        self.file_tree.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.file_tree.itemClicked.connect(self.on_file_clicked)
        layout.addWidget(self.file_tree)
        
        self.tab_widget.addTab(browser_widget, "Browse")
    
    def create_upload_tab(self):
        """Create upload tab."""
        upload_widget = QWidget()
        layout = QVBoxLayout(upload_widget)
        
        # File selection
        file_group = QGroupBox("Select Files to Upload")
        file_layout = QVBoxLayout(file_group)
        
        # Local file browser
        self.local_file_tree = QTreeWidget()
        self.local_file_tree.setHeaderLabels(["Name", "Size", "Path"])
        self.local_file_tree.itemSelectionChanged.connect(self.on_local_file_selection)
        file_layout.addWidget(self.local_file_tree)
        
        # Upload controls
        upload_controls_layout = QHBoxLayout()
        
        self.select_files_btn = QPushButton("Select Files...")
        self.select_files_btn.clicked.connect(self.select_files_to_upload)
        upload_controls_layout.addWidget(self.select_files_btn)
        
        self.upload_all_btn = QPushButton("Upload Selected")
        self.upload_all_btn.clicked.connect(self.upload_selected_files)
        upload_controls_layout.addWidget(self.upload_all_btn)
        
        upload_controls_layout.addStretch()
        file_layout.addLayout(upload_controls_layout)
        
        layout.addWidget(file_group)
        
        # Upload progress
        progress_group = QGroupBox("Upload Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.upload_progress_bar = QProgressBar()
        self.upload_progress_bar.setVisible(False)
        progress_layout.addWidget(self.upload_progress_bar)
        
        self.upload_status_label = QLabel("Ready")
        progress_layout.addWidget(self.upload_status_label)
        
        layout.addWidget(progress_group)
        
        self.tab_widget.addTab(upload_widget, "Upload")
    
    def create_download_tab(self):
        """Create download tab."""
        download_widget = QWidget()
        layout = QVBoxLayout(download_widget)
        
        # Download queue
        queue_group = QGroupBox("Download Queue")
        queue_layout = QVBoxLayout(queue_group)
        
        self.download_queue_tree = QTreeWidget()
        self.download_queue_tree.setHeaderLabels(["File", "Status", "Progress"])
        queue_layout.addWidget(self.download_queue_tree)
        
        # Download controls
        download_controls_layout = QHBoxLayout()
        
        self.add_to_queue_btn = QPushButton("Add to Queue")
        self.add_to_queue_btn.clicked.connect(self.add_to_download_queue)
        download_controls_layout.addWidget(self.add_to_queue_btn)
        
        self.start_download_btn = QPushButton("Start Downloads")
        self.start_download_btn.clicked.connect(self.start_downloads)
        download_controls_layout.addWidget(self.start_download_btn)
        
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_download_queue)
        download_controls_layout.addWidget(self.clear_queue_btn)
        
        download_controls_layout.addStretch()
        queue_layout.addLayout(download_controls_layout)
        
        layout.addWidget(queue_group)
        
        # Download settings
        settings_group = QGroupBox("Download Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        self.download_dir_edit = QLineEdit()
        self.download_dir_edit.setPlaceholderText("Select download directory...")
        settings_layout.addWidget(self.download_dir_edit)
        
        browse_layout = QHBoxLayout()
        self.browse_download_btn = QPushButton("Browse...")
        self.browse_download_btn.clicked.connect(self.browse_download_directory)
        browse_layout.addWidget(self.browse_download_btn)
        browse_layout.addStretch()
        
        settings_layout.addLayout(browse_layout)
        
        # Options
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        self.overwrite_checkbox.setChecked(False)
        settings_layout.addWidget(self.overwrite_checkbox)
        
        layout.addWidget(settings_group)
        
        self.tab_widget.addTab(download_widget, "Download")
    
    def create_control_buttons(self, layout):
        """Create control buttons."""
        buttons_layout = QHBoxLayout()
        
        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.show_help)
        buttons_layout.addWidget(self.help_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_config(self):
        """Load cloud configuration."""
        config_file = Path.home() / ".pdf_editor_cloud_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                
                # Update UI
                if 'google_drive' in self.config:
                    self.google_client_id_edit.setText(self.config['google_drive'].get('client_id', ''))
                    self.google_client_secret_edit.setText(self.config['google_drive'].get('client_secret', ''))
                
                if 'dropbox' in self.config:
                    self.dropbox_app_key_edit.setText(self.config['dropbox'].get('app_key', ''))
                    self.dropbox_app_secret_edit.setText(self.config['dropbox'].get('app_secret', ''))
                
                if 'download_dir' in self.config:
                    self.download_dir_edit.setText(self.config['download_dir'])
                
            except Exception as e:
                logger.error(f"Failed to load cloud config: {e}")
    
    def save_config(self):
        """Save cloud configuration."""
        provider = self.provider_combo.currentText().lower().replace(' ', '_')
        
        self.config[provider] = {
            'client_id': self.google_client_id_edit.text() if provider == 'google_drive' else self.dropbox_app_key_edit.text(),
            'client_secret': self.google_client_secret_edit.text() if provider == 'google_drive' else self.dropbox_app_secret_edit.text()
        }
        
        if self.download_dir_edit.text():
            self.config['download_dir'] = self.download_dir_edit.text()
        
        try:
            config_file = Path.home() / ".pdf_editor_cloud_config.json"
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def on_provider_changed(self, provider: str):
        """Handle provider change."""
        self.current_provider = provider.lower().replace(' ', '_')
        
        # Show/hide relevant configuration fields
        is_google = provider == "Google Drive"
        
        # Enable/disable fields based on provider
        self.google_client_id_edit.setEnabled(is_google)
        self.google_client_secret_edit.setEnabled(is_google)
        self.dropbox_app_key_edit.setEnabled(not is_google)
        self.dropbox_app_secret_edit.setEnabled(not is_google)
    
    def test_connection(self):
        """Test connection to cloud provider."""
        provider = self.current_provider
        
        if not provider:
            QMessageBox.warning(self, "Warning", "Please select a cloud provider")
            return
        
        self.connection_status_label.setText("Testing connection...")
        self.connection_status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Test connection in background thread
        test_worker = CloudWorker('list', {'provider': provider}, self.config)
        test_worker.operation_completed.connect(lambda result: self.on_connection_test_result(True))
        test_worker.error_occurred.connect(lambda error: self.on_connection_test_result(False, error))
        test_worker.start()
    
    def on_connection_test_result(self, success: bool, error: str = ""):
        """Handle connection test result."""
        if success:
            self.connection_status_label.setText("Connected successfully!")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_status_label.setText(f"Connection failed: {error}")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def refresh_file_list(self):
        """Refresh the file list."""
        if not self.current_provider:
            QMessageBox.warning(self, "Warning", "Please configure cloud provider first")
            return
        
        self.file_tree.clear()
        self.file_tree.setEnabled(False)
        self.current_path_label.setText("Loading...")
        
        # Load files in background
        list_worker = CloudWorker('list', {'provider': self.current_provider}, self.config)
        list_worker.operation_completed.connect(self.on_file_list_loaded)
        list_worker.error_occurred.connect(lambda error: self.on_file_list_error(error))
        list_worker.start()
    
    def on_file_list_loaded(self, result: dict):
        """Handle loaded file list."""
        self.file_tree.clear()
        self.file_tree.setEnabled(True)
        
        files = result.get('files', [])
        for file_info in files:
            item = QTreeWidgetItem(self.file_tree)
            item.setText(0, file_info['name'])
            item.setText(1, f"{file_info['size']:,}" if file_info['size'] else "N/A")
            item.setText(2, file_info.get('modified_time', 'Unknown'))
            item.setText(3, file_info.get('mime_type', 'Folder'))
            item.setData(0, Qt.UserRole, file_info)
        
        self.file_tree.resizeColumnToContents(0)
        self.current_path_label.setText("/")
    
    def on_file_list_error(self, error: str):
        """Handle file list error."""
        self.file_tree.clear()
        self.file_tree.setEnabled(True)
        self.current_path_label.setText("Error loading files")
        QMessageBox.critical(self, "Error", f"Failed to load file list: {error}")
    
    def on_file_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle file double click."""
        file_info = item.data(0, Qt.UserRole)
        if file_info and file_info.get('mime_type') == 'application/pdf':
            # Add to download queue
            self.add_file_to_download_queue(file_info)
    
    def on_file_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle file click."""
        file_info = item.data(0, Qt.UserRole)
        if file_info:
            # Show file details
            self.show_file_details(file_info)
    
    def show_file_details(self, file_info: dict):
        """Show file details (placeholder)."""
        details = f"Name: {file_info['name']}\\n"
        details += f"Size: {file_info['size']:,} bytes\\n"
        details += f"Modified: {file_info.get('modified_time', 'Unknown')}\\n"
        details += f"Type: {file_info.get('mime_type', 'Unknown')}"
        
        QMessageBox.information(self, "File Details", details)
    
    def select_files_to_upload(self):
        """Select files to upload."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Upload", "", "All Files (*)"
        )
        
        if files:
            self.local_file_tree.clear()
            for file_path in files:
                self.add_local_file_to_tree(file_path)
    
    def add_local_file_to_tree(self, file_path: str):
        """Add local file to tree."""
        path_obj = Path(file_path)
        if path_obj.exists():
            item = QTreeWidgetItem(self.local_file_tree)
            item.setText(0, path_obj.name)
            item.setText(1, f"{path_obj.stat().st_size:,}" if path_obj.is_file() else "N/A")
            item.setText(2, file_path)
            item.setData(0, Qt.UserRole, file_path)
    
    def on_local_file_selection(self):
        """Handle local file selection."""
        pass
    
    def upload_selected_files(self):
        """Upload selected files."""
        selected_items = self.local_file_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No files selected")
            return
        
        for item in selected_items:
            file_path = item.data(0, Qt.UserRole)
            if file_path:
                self.upload_file(file_path)
    
    def upload_file(self, file_path: str):
        """Upload a single file."""
        if not self.current_provider:
            QMessageBox.warning(self, "Warning", "Please configure cloud provider first")
            return
        
        self.upload_progress_bar.setVisible(True)
        self.upload_progress_bar.setRange(0, 0)  # Indeterminate
        self.upload_status_label.setText(f"Uploading {Path(file_path).name}...")
        
        # Upload in background thread
        upload_worker = CloudWorker('upload', {
            'local_path': file_path,
            'provider': self.current_provider,
            'cloud_path': f"/{Path(file_path).name}"
        }, self.config)
        
        upload_worker.operation_completed.connect(self.on_upload_completed)
        upload_worker.error_occurred.connect(self.on_upload_error)
        upload_worker.start()
    
    def on_upload_completed(self, result: dict):
        """Handle upload completion."""
        self.upload_progress_bar.setVisible(False)
        self.upload_status_label.setText("Upload completed successfully!")
        
        # Refresh file list
        self.refresh_file_list()
        
        QMessageBox.information(self, "Upload Complete", 
                           f"File uploaded successfully to {result.get('provider', 'cloud')}")
    
    def on_upload_error(self, error: str):
        """Handle upload error."""
        self.upload_progress_bar.setVisible(False)
        self.upload_status_label.setText("Upload failed!")
        QMessageBox.critical(self, "Upload Error", f"Upload failed: {error}")
    
    def create_folder(self):
        """Create new folder (placeholder)."""
        QMessageBox.information(self, "Coming Soon", "Create folder functionality coming soon!")
    
    def browse_download_directory(self):
        """Browse for download directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir_edit.setText(directory)
    
    def add_to_download_queue(self):
        """Add selected file to download queue."""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No file selected")
            return
        
        for item in selected_items:
            file_info = item.data(0, Qt.UserRole)
            if file_info:
                self.add_file_to_download_queue(file_info)
    
    def add_file_to_download_queue(self, file_info: dict):
        """Add file to download queue."""
        # Check if already in queue
        for i in range(self.download_queue_tree.topLevelItemCount()):
            item = self.download_queue_tree.topLevelItem(i)
            existing_info = item.data(0, Qt.UserRole)
            if existing_info and existing_info.get('id') == file_info.get('id'):
                return
        
        # Add to queue
        queue_item = QTreeWidgetItem(self.download_queue_tree)
        queue_item.setText(0, file_info['name'])
        queue_item.setText(1, "Queued")
        queue_item.setText(2, "0%")
        queue_item.setData(0, Qt.UserRole, file_info)
    
    def start_downloads(self):
        """Start download queue processing."""
        if not self.download_dir_edit.text():
            QMessageBox.warning(self, "Warning", "Please select download directory")
            return
        
        # Process download queue (placeholder)
        QMessageBox.information(self, "Coming Soon", "Download queue processing coming soon!")
    
    def clear_download_queue(self):
        """Clear download queue."""
        self.download_queue_tree.clear()
    
    def show_help(self):
        """Show help information."""
        help_text = """
Cloud Storage Integration Help

1. Configuration Tab:
   - Select cloud provider (Google Drive or Dropbox)
   - Enter API credentials
   - Test connection
   - Save configuration

2. Browse Tab:
   - View cloud files
   - Double-click PDFs to download
   - Refresh file list

3. Upload Tab:
   - Select local files
   - Upload to cloud storage
   - Monitor progress

4. Download Tab:
   - Manage download queue
   - Set download directory
   - Control overwrite behavior

Getting API Credentials:
- Google Drive: https://console.developers.google.com/
- Dropbox: https://www.dropbox.com/developers/apps
        """
        
        QMessageBox.information(self, "Cloud Storage Help", help_text)
    
    def close(self):
        """Close dialog with cleanup."""
        if self.cloud_worker and self.cloud_worker.isRunning():
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Cloud operations are still running. Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            self.cloud_worker.terminate()
            self.cloud_worker.wait()
        
        super().close()
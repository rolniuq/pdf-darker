"""Settings dialog for the GUI application."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSpinBox, QGroupBox, QFormLayout, QCheckBox,
    QDialogButtonBox, QTabWidget, QLineEdit
)
from PySide6.QtCore import Qt

from ...config.manager import config_manager
from ...utils.logging import get_logger

logger = get_logger("gui.settings_dialog")


class SettingsDialog(QDialog):
    """Settings dialog for application preferences."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        self.load_settings()
        
        logger.info("Settings dialog opened")
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create settings tabs
        self.create_general_tab()
        self.create_appearance_tab()
        self.create_dark_mode_tab()
        self.create_advanced_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_general_tab(self):
        """Create general settings tab."""
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Default settings group
        defaults_group = QGroupBox("Default Settings")
        defaults_layout = QFormLayout()
        
        self.default_dpi_spinbox = QSpinBox()
        self.default_dpi_spinbox.setRange(72, 600)
        self.default_dpi_spinbox.setValue(300)
        defaults_layout.addRow("Default DPI:", self.default_dpi_spinbox)
        
        self.default_quality_spinbox = QSpinBox()
        self.default_quality_spinbox.setRange(10, 100)
        self.default_quality_spinbox.setValue(95)
        defaults_layout.addRow("Default Quality (%):", self.default_quality_spinbox)
        
        defaults_group.setLayout(defaults_layout)
        general_layout.addWidget(defaults_group)
        
        # File handling group
        file_group = QGroupBox("File Handling")
        file_layout = QVBoxLayout()
        
        self.backup_checkbox = QCheckBox("Create backup files before saving")
        file_layout.addWidget(self.backup_checkbox)
        
        self.autosave_checkbox = QCheckBox("Enable autosave")
        file_layout.addWidget(self.autosave_checkbox)
        
        self.autosave_interval_spinbox = QSpinBox()
        self.autosave_interval_spinbox.setRange(1, 60)
        self.autosave_interval_spinbox.setValue(5)
        self.autosave_interval_spinbox.setSuffix(" minutes")
        
        autosave_layout = QHBoxLayout()
        autosave_layout.addWidget(QLabel("Autosave interval:"))
        autosave_layout.addWidget(self.autosave_interval_spinbox)
        autosave_layout.addStretch()
        file_layout.addLayout(autosave_layout)
        
        file_group.setLayout(file_layout)
        general_layout.addWidget(file_group)
        
        general_layout.addStretch()
        self.tab_widget.addTab(general_tab, "General")
    
    def create_appearance_tab(self):
        """Create appearance settings tab."""
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addWidget(QLabel("Application Theme:"))
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        appearance_layout.addWidget(theme_group)
        
        # Interface group
        interface_group = QGroupBox("Interface")
        interface_layout = QVBoxLayout()
        
        self.show_toolbar_checkbox = QCheckBox("Show toolbar")
        self.show_toolbar_checkbox.setChecked(True)
        interface_layout.addWidget(self.show_toolbar_checkbox)
        
        self.show_statusbar_checkbox = QCheckBox("Show status bar")
        self.show_statusbar_checkbox.setChecked(True)
        interface_layout.addWidget(self.show_statusbar_checkbox)
        
        self.dock_floatable_checkbox = QCheckBox("Allow dock widgets to float")
        interface_layout.addWidget(self.dock_floatable_checkbox)
        
        interface_group.setLayout(interface_layout)
        appearance_layout.addWidget(interface_group)
        
        appearance_layout.addStretch()
        self.tab_widget.addTab(appearance_tab, "Appearance")
    
    def create_dark_mode_tab(self):
        """Create dark mode specific settings tab."""
        dark_mode_tab = QWidget()
        dark_mode_layout = QVBoxLayout(dark_mode_tab)
        
        # Dark mode defaults
        dark_defaults_group = QGroupBox("Dark Mode Defaults")
        dark_defaults_layout = QFormLayout()
        
        self.preserve_text_checkbox = QCheckBox("Preserve text layer and links")
        self.preserve_text_checkbox.setChecked(True)
        dark_defaults_layout.addRow(self.preserve_text_checkbox)
        
        self.enhanced_mode_checkbox = QCheckBox("Use enhanced dark mode")
        self.enhanced_mode_checkbox.setChecked(True)
        dark_defaults_layout.addRow(self.enhanced_mode_checkbox)
        
        self.dark_background_edit = QLineEdit()
        self.dark_background_edit.setText("#1e1e1e")
        dark_defaults_layout.addRow("Background Color:", self.dark_background_edit)
        
        self.dark_text_edit = QLineEdit()
        self.dark_text_edit.setText("#f0f0f0")
        dark_defaults_layout.addRow("Text Color:", self.dark_text_edit)
        
        dark_defaults_group.setLayout(dark_defaults_layout)
        dark_mode_layout.addWidget(dark_defaults_group)
        
        # Performance settings
        performance_group = QGroupBox("Performance")
        performance_layout = QVBoxLayout()
        
        self.hardware_accel_checkbox = QCheckBox("Use hardware acceleration")
        self.hardware_accel_checkbox.setChecked(True)
        performance_layout.addWidget(self.hardware_accel_checkbox)
        
        self.cache_enabled_checkbox = QCheckBox("Enable page caching")
        self.cache_enabled_checkbox.setChecked(True)
        performance_layout.addWidget(self.cache_enabled_checkbox)
        
        performance_group.setLayout(performance_layout)
        dark_mode_layout.addWidget(performance_group)
        
        dark_mode_layout.addStretch()
        self.tab_widget.addTab(dark_mode_tab, "Dark Mode")
    
    def create_advanced_tab(self):
        """Create advanced settings tab."""
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Logging group
        logging_group = QGroupBox("Logging")
        logging_layout = QVBoxLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addWidget(QLabel("Log Level:"))
        logging_layout.addWidget(self.log_level_combo)
        
        self.log_file_checkbox = QCheckBox("Enable logging to file")
        logging_layout.addWidget(self.log_file_checkbox)
        
        logging_group.setLayout(logging_layout)
        advanced_layout.addWidget(logging_group)
        
        # Experimental features
        experimental_group = QGroupBox("Experimental Features")
        experimental_layout = QVBoxLayout()
        
        self.ocr_checkbox = QCheckBox("Enable OCR features")
        experimental_layout.addWidget(self.ocr_checkbox)
        
        self.batch_checkbox = QCheckBox("Enable batch processing")
        experimental_layout.addWidget(self.batch_checkbox)
        
        self.web_interface_checkbox = QCheckBox("Enable web interface")
        experimental_layout.addWidget(self.web_interface_checkbox)
        
        experimental_group.setLayout(experimental_layout)
        advanced_layout.addWidget(experimental_group)
        
        advanced_layout.addStretch()
        self.tab_widget.addTab(advanced_tab, "Advanced")
    
    def load_settings(self):
        """Load current settings from config."""
        # General settings
        self.default_dpi_spinbox.setValue(config_manager.get('dpi', 300))
        self.default_quality_spinbox.setValue(config_manager.get('quality', 95))
        self.backup_checkbox.setChecked(config_manager.get('backup_enabled', True))
        self.autosave_checkbox.setChecked(config_manager.get('autosave_enabled', False))
        self.autosave_interval_spinbox.setValue(config_manager.get('autosave_interval', 5))
        
        # Appearance settings
        theme = config_manager.get('theme', 'light')
        theme_map = {'light': 'Light', 'dark': 'Dark', 'system': 'System'}
        self.theme_combo.setCurrentText(theme_map.get(theme, 'Light'))
        
        self.show_toolbar_checkbox.setChecked(config_manager.get('show_toolbar', True))
        self.show_statusbar_checkbox.setChecked(config_manager.get('show_statusbar', True))
        self.dock_floatable_checkbox.setChecked(config_manager.get('dock_floatable', True))
        
        # Dark mode settings
        self.preserve_text_checkbox.setChecked(config_manager.get('dark_mode_preserve_text', True))
        self.enhanced_mode_checkbox.setChecked(config_manager.get('dark_mode_enhanced', True))
        self.dark_background_edit.setText(config_manager.get('dark_mode_bg_color', '#1e1e1e'))
        self.dark_text_edit.setText(config_manager.get('dark_mode_text_color', '#f0f0f0'))
        
        self.hardware_accel_checkbox.setChecked(config_manager.get('hardware_acceleration', True))
        self.cache_enabled_checkbox.setChecked(config_manager.get('page_caching', True))
        
        # Advanced settings
        log_level = config_manager.get('log_level', 'INFO')
        self.log_level_combo.setCurrentText(log_level)
        self.log_file_checkbox.setChecked(config_manager.get('log_to_file', False))
        
        self.ocr_checkbox.setChecked(config_manager.get('ocr_enabled', False))
        self.batch_checkbox.setChecked(config_manager.get('batch_enabled', False))
        self.web_interface_checkbox.setChecked(config_manager.get('web_interface_enabled', False))
    
    def accept(self):
        """Save settings and close dialog."""
        try:
            # Save general settings
            config_manager.set('dpi', self.default_dpi_spinbox.value())
            config_manager.set('quality', self.default_quality_spinbox.value())
            config_manager.set('backup_enabled', self.backup_checkbox.isChecked())
            config_manager.set('autosave_enabled', self.autosave_checkbox.isChecked())
            config_manager.set('autosave_interval', self.autosave_interval_spinbox.value())
            
            # Save appearance settings
            theme_map = {'Light': 'light', 'Dark': 'dark', 'System': 'system'}
            config_manager.set('theme', theme_map[self.theme_combo.currentText()])
            
            config_manager.set('show_toolbar', self.show_toolbar_checkbox.isChecked())
            config_manager.set('show_statusbar', self.show_statusbar_checkbox.isChecked())
            config_manager.set('dock_floatable', self.dock_floatable_checkbox.isChecked())
            
            # Save dark mode settings
            config_manager.set('dark_mode_preserve_text', self.preserve_text_checkbox.isChecked())
            config_manager.set('dark_mode_enhanced', self.enhanced_mode_checkbox.isChecked())
            config_manager.set('dark_mode_bg_color', self.dark_background_edit.text())
            config_manager.set('dark_mode_text_color', self.dark_text_edit.text())
            
            config_manager.set('hardware_acceleration', self.hardware_accel_checkbox.isChecked())
            config_manager.set('page_caching', self.cache_enabled_checkbox.isChecked())
            
            # Save advanced settings
            config_manager.set('log_level', self.log_level_combo.currentText())
            config_manager.set('log_to_file', self.log_file_checkbox.isChecked())
            
            config_manager.set('ocr_enabled', self.ocr_checkbox.isChecked())
            config_manager.set('batch_enabled', self.batch_checkbox.isChecked())
            config_manager.set('web_interface_enabled', self.web_interface_checkbox.isChecked())
            
            logger.info("Settings saved successfully")
            super().accept()
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            super().reject()
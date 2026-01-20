"""Main application window for PDF Editor GUI."""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QSplitter, QFileDialog,
    QMessageBox, QDockWidget, QShortcut
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QFont

from ..core.editor import PDFEditor
from ..config.manager import config_manager
from ..utils.logging import get_logger
from .pdf_viewer import PDFViewer
from .tool_panels.form_editor import FormEditorPanel
from .tool_panels.annotation_tools import AnnotationToolsPanel
from .tool_panels.security_panel import SecurityPanel
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.batch_dialog import BatchProcessingDialog
from .dialogs.cloud_dialog import CloudStorageDialog
from .dialogs.advanced_export_dialog import AdvancedExportDialog
from .themes.theme_manager import ThemeManager

logger = get_logger("gui.main_window")


class MainWindow(QMainWindow):
    """Main application window for PDF Editor."""
    
    # Signals
    document_opened = Signal(str)  # file path
    document_saved = Signal(str)  # file path
    operation_completed = Signal(str)  # operation description
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.pdf_editor = PDFEditor()
        self.theme_manager = ThemeManager()
        self.current_file: Optional[Path] = None
        self.is_modified = False
        
        # Initialize UI
        self.init_ui()
        self.apply_theme()
        self.setup_connections()
        
        logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("PDF Editor - Advanced PDF Editing Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # PDF Viewer (left side)
        self.pdf_viewer = PDFViewer()
        self.main_splitter.addWidget(self.pdf_viewer)
        
        # Tool panels area (right side)
        self.tool_panels_container = QWidget()
        self.tool_panels_layout = QVBoxLayout(self.tool_panels_container)
        self.main_splitter.addWidget(self.tool_panels_container)
        
        # Set splitter proportions
        self.main_splitter.setSizes([800, 400])
        
        # Create menus
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
        # Create dock widgets for tool panels
        self.create_dock_widgets()
        
        # Apply initial theme
        self.apply_theme()
    
    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open PDF...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open a PDF file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current PDF")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("Save PDF with new name")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("&Export...", self)
        export_action.setStatusTip("Export PDF to other formats")
        export_action.triggered.connect(self.export_document)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setStatusTip("Undo last operation")
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setStatusTip("Redo last operation")
        edit_menu.addAction(redo_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        dark_mode_action = QAction("Toggle &Dark Mode", self)
        dark_mode_action.setShortcut("Ctrl+D")
        dark_mode_action.setStatusTip("Toggle dark mode for current PDF")
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        tools_menu.addAction(dark_mode_action)
        
        batch_action = QAction("&Batch Processing...", self)
        batch_action.setStatusTip("Process multiple PDF files")
        batch_action.setShortcut("Ctrl+B")
        batch_action.triggered.connect(self.open_batch_dialog)
        tools_menu.addAction(batch_action)
        
        cloud_action = QAction("&Cloud Storage...", self)
        cloud_action.setStatusTip("Manage cloud storage")
        cloud_action.setShortcut("Ctrl+Shift+C")
        cloud_action.triggered.connect(self.open_cloud_dialog)
        tools_menu.addAction(cloud_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.setStatusTip("Zoom in")
        zoom_in_action.triggered.connect(self.pdf_viewer.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.setStatusTip("Zoom out")
        zoom_out_action.triggered.connect(self.pdf_viewer.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        fit_action = QAction("&Fit to Window", self)
        fit_action.setShortcut("Ctrl+F")
        fit_action.setStatusTip("Fit PDF to window")
        fit_action.triggered.connect(self.pdf_viewer.fit_to_window)
        view_menu.addAction(fit_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setStatusTip("Open application settings")
        preferences_action.triggered.connect(self.open_settings)
        settings_menu.addAction(preferences_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show information about PDF Editor")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create main toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # File operations
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open PDF file")
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save PDF file")
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Edit operations
        dark_mode_action = QAction("Dark Mode", self)
        dark_mode_action.setStatusTip("Toggle dark mode")
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        toolbar.addAction(dark_mode_action)
        
        toolbar.addSeparator()
        
        # View operations
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setStatusTip("Zoom in")
        zoom_in_action.triggered.connect(self.pdf_viewer.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setStatusTip("Zoom out")
        zoom_out_action.triggered.connect(self.pdf_viewer.zoom_out)
        toolbar.addAction(zoom_out_action)
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Page info
        self.page_info_label = QLabel("No document loaded")
        self.status_bar.addPermanentWidget(self.page_info_label)
        
        # Zoom info
        self.zoom_info_label = QLabel("100%")
        self.status_bar.addPermanentWidget(self.zoom_info_label)
    
    def create_dock_widgets(self):
        """Create dockable tool panels."""
        # Form Editor Dock
        self.form_dock = QDockWidget("Form Editor", self)
        self.form_panel = FormEditorPanel()
        self.form_dock.setWidget(self.form_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.form_dock)
        
        # Annotation Tools Dock
        self.annotation_dock = QDockWidget("Annotation Tools", self)
        self.annotation_panel = AnnotationToolsPanel()
        self.annotation_dock.setWidget(self.annotation_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.annotation_dock)
        
        # Security Panel Dock
        self.security_dock = QDockWidget("Security", self)
        self.security_panel = SecurityPanel()
        self.security_dock.setWidget(self.security_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.security_dock)
        
        # Initially dock all panels
        self.tabifyDockWidget(self.form_dock, self.annotation_dock)
        self.tabifyDockWidget(self.annotation_dock, self.security_dock)
        self.form_dock.raise_()
    
    def setup_connections(self):
        """Setup signal connections."""
        # PDF viewer signals
        self.pdf_viewer.page_changed.connect(self.update_page_info)
        self.pdf_viewer.zoom_changed.connect(self.update_zoom_info)
        
        # Tool panel signals
        self.form_panel.operation_requested.connect(self.handle_operation)
        self.annotation_panel.operation_requested.connect(self.handle_operation)
        self.security_panel.operation_requested.connect(self.handle_operation)
        
        # Document signals
        self.document_opened.connect(self.on_document_opened)
        self.document_saved.connect(self.on_document_saved)
        self.operation_completed.connect(self.on_operation_completed)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def open_file(self):
        """Open a PDF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                self.pdf_editor.load_document(file_path)
                self.pdf_viewer.load_document(file_path)
                self.current_file = Path(file_path)
                self.is_modified = False
                self.document_opened.emit(file_path)
                self.update_window_title()
                self.update_status("PDF loaded successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open PDF: {e}")
                logger.error(f"Failed to open PDF {file_path}: {e}")
    
    def save_file(self):
        """Save current PDF file."""
        if not self.current_file:
            return self.save_file_as()
        
        try:
            self.pdf_editor.save_document(str(self.current_file))
            self.is_modified = False
            self.document_saved.emit(str(self.current_file))
            self.update_window_title()
            self.update_status("PDF saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF: {e}")
            logger.error(f"Failed to save PDF {self.current_file}: {e}")
    
    def save_file_as(self):
        """Save PDF with new filename."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                self.pdf_editor.save_document(file_path)
                self.current_file = Path(file_path)
                self.is_modified = False
                self.document_saved.emit(file_path)
                self.update_window_title()
                self.update_status("PDF saved successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF: {e}")
                logger.error(f"Failed to save PDF {file_path}: {e}")
    
    def export_document(self):
        """Export document to other formats."""
        # TODO: Implement export dialog
        QMessageBox.information(self, "Export", "Export functionality coming soon!")
    
    def toggle_dark_mode(self):
        """Toggle dark mode for current PDF."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No PDF file loaded")
            return
        
        # TODO: Implement dark mode toggle
        QMessageBox.information(self, "Dark Mode", "Dark mode toggle coming soon!")
    
    def open_batch_dialog(self):
        """Open batch processing dialog."""
        dialog = BatchProcessingDialog(self)
        dialog.exec()
    
    def open_cloud_dialog(self):
        """Open cloud storage dialog."""
        dialog = CloudStorageDialog(self)
        dialog.exec()
    
    def open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About PDF Editor",
            "PDF Editor v1.0\\n\\n"
            "A comprehensive PDF editing tool with dark mode conversion\\n"
            "and advanced editing capabilities.\\n\\n"
            "Built with PySide6 and PyMuPDF"
        )
    
    def apply_theme(self):
        """Apply current theme."""
        theme = config_manager.get('theme', 'light')
        self.theme_manager.apply_theme(self, theme)
    
    def handle_operation(self, operation_data):
        """Handle operation from tool panels."""
        # TODO: Implement operation handling
        operation_name = operation_data.get('name', 'Unknown')
        self.update_status(f"Executing: {operation_name}")
        self.operation_completed.emit(f"Completed: {operation_name}")
    
    def update_window_title(self):
        """Update window title with current file info."""
        title = "PDF Editor"
        if self.current_file:
            title += f" - {self.current_file.name}"
            if self.is_modified:
                title += "*"
        self.setWindowTitle(title)
    
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(message)
        logger.info(f"Status: {message}")
    
    def update_page_info(self, page_num: int, total_pages: int):
        """Update page information in status bar."""
        self.page_info_label.setText(f"Page {page_num} of {total_pages}")
    
    def update_zoom_info(self, zoom_level: int):
        """Update zoom information in status bar."""
        self.zoom_info_label.setText(f"{zoom_level}%")
    
    def on_document_opened(self, file_path: str):
        """Handle document opened event."""
        logger.info(f"Document opened: {file_path}")
    
    def on_document_saved(self, file_path: str):
        """Handle document saved event."""
        logger.info(f"Document saved: {file_path}")
    
    def on_operation_completed(self, description: str):
        """Handle operation completed event."""
        logger.info(f"Operation completed: {description}")
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'You have unsaved changes. Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        logger.info("Application closing")
        event.accept()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for accessibility."""
        # File operations
        self.shortcut_new = QShortcut("Ctrl+N", self)
        self.shortcut_new.activated.connect(self.new_document)
        
        self.shortcut_open = QShortcut("Ctrl+O", self)
        self.shortcut_open.activated.connect(self.open_file)
        
        self.shortcut_save = QShortcut("Ctrl+S", self)
        self.shortcut_save.activated.connect(self.save_file)
        
        self.shortcut_save_as = QShortcut("Ctrl+Shift+S", self)
        self.shortcut_save_as.activated.connect(self.save_file_as)
        
        self.shortcut_close = QShortcut("Ctrl+W", self)
        self.shortcut_close.activated.connect(self.close)
        
        # Navigation
        self.shortcut_first_page = QShortcut("Home", self)
        self.shortcut_first_page.activated.connect(self.pdf_viewer.go_to_first_page)
        
        self.shortcut_last_page = QShortcut("End", self)
        self.shortcut_last_page.activated.connect(self.pdf_viewer.go_to_last_page)
        
        self.shortcut_prev_page = QShortcut("PgUp", self)
        self.shortcut_prev_page.activated.connect(self.pdf_viewer.go_to_previous_page)
        
        self.shortcut_next_page = QShortcut("PgDown", self)
        self.shortcut_next_page.activated.connect(self.pdf_viewer.go_to_next_page)
        
        # Zoom
        self.shortcut_zoom_in = QShortcut("Ctrl++", self)
        self.shortcut_zoom_in.activated.connect(self.pdf_viewer.zoom_in)
        
        self.shortcut_zoom_out = QShortcut("Ctrl+-", self)
        self.shortcut_zoom_out.activated.connect(self.pdf_viewer.zoom_out)
        
        self.shortcut_fit_window = QShortcut("Ctrl+0", self)
        self.shortcut_fit_window.activated.connect(self.pdf_viewer.fit_to_window)
        
        # Search
        self.shortcut_search = QShortcut("Ctrl+F", self)
        self.shortcut_search.activated.connect(self.show_search_dialog)
        
        self.shortcut_search_next = QShortcut("F3", self)
        self.shortcut_search_next.activated.connect(self.search_next)
        
        # Tools
        self.shortcut_batch = QShortcut("Ctrl+B", self)
        self.shortcut_batch.activated.connect(self.open_batch_dialog)
        
        self.shortcut_cloud = QShortcut("Ctrl+Shift+C", self)
        self.shortcut_cloud.activated.connect(self.open_cloud_dialog)
        
        self.shortcut_settings = QShortcut("Ctrl+,", self)
        self.shortcut_settings.activated.connect(self.open_settings)
        
        # Help
        self.shortcut_help = QShortcut("F1", self)
        self.shortcut_help.activated.connect(self.show_help)
        
        # Accessibility
        self.shortcut_increase_font = QShortcut("Ctrl+Shift+=", self)
        self.shortcut_increase_font.activated.connect(self.increase_font_size)
        
        self.shortcut_decrease_font = QShortcut("Ctrl+Shift+-", self)
        self.shortcut_decrease_font.activated.connect(self.decrease_font_size)
        
        self.shortcut_reset_font = QShortcut("Ctrl+Shift+0", self)
        self.shortcut_reset_font.activated.connect(self.reset_font_size)
        
        # Dark mode toggle
        self.shortcut_dark_mode = QShortcut("Ctrl+D", self)
        self.shortcut_dark_mode.activated.connect(lambda: self.pdf_viewer.toggle_dark_mode(True))
        
        self.shortcut_light_mode = QShortcut("Ctrl+Shift+D", self)
        self.shortcut_light_mode.activated.connect(lambda: self.pdf_viewer.toggle_dark_mode(False))
    
    def new_document(self):
        """Create new document (placeholder)."""
        QMessageBox.information(self, "New Document", "New document creation coming soon!")
    
    def show_search_dialog(self):
        """Show search dialog."""
        QMessageBox.information(self, "Search", "Search functionality coming soon!")
    
    def search_next(self):
        """Search for next occurrence."""
        QMessageBox.information(self, "Search", "Search next coming soon!")
    
    def increase_font_size(self):
        """Increase UI font size for accessibility."""
        current_font = self.font()
        new_size = current_font.pointSize() + 2
        if new_size <= 24:
            new_font = current_font
            new_font.setPointSize(new_size)
            self.setFont(new_font)
            QApplication.setFont(new_font)
    
    def decrease_font_size(self):
        """Decrease UI font size for accessibility."""
        current_font = self.font()
        new_size = current_font.pointSize() - 2
        if new_size >= 8:
            new_font = current_font
            new_font.setPointSize(new_size)
            self.setFont(new_font)
            QApplication.setFont(new_font)
    
    def reset_font_size(self):
        """Reset UI font size to default."""
        default_font = QFont()
        default_font.setPointSize(10)
        self.setFont(default_font)
        QApplication.setFont(default_font)
    
    def open_advanced_export(self):
        """Open advanced export dialog."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No PDF file currently open")
            return
        
        dialog = AdvancedExportDialog(str(self.current_file), self)
        dialog.exec()
    
    def export_to_word(self):
        """Quick export to Word."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No PDF file currently open")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Export to Word", 
            str(self.current_file).replace('.pdf', '.docx'),
            "Word Documents (*.docx)"
        )
        
        if output_file:
            from ..operations.advanced_export_operations import ExportToWordOperation
            
            with console.status("Exporting to Word..."):
                self.pdf_editor.load_document(str(self.current_file))
                
                operation = ExportToWordOperation(
                    output_path=output_file,
                    preserve_formatting=True,
                    extract_images=True,
                    page_breaks=True
                )
                
                self.pdf_editor.add_operation(operation)
                result = self.pdf_editor.execute_operations()
                self.pdf_editor.save_document(output_file)
            
            console.print(Panel.fit(
                f"[green]✓[/green] Word export completed\\n"
                f"[blue]Pages:[/blue] {result['pages_processed']}\\n"
                f"[blue]Images:[/blue] {result['images_extracted']}\\n"
                f"[blue]Output:[/blue] {output_file}",
                title="Word Export"
            ))
    
    def export_to_excel(self):
        """Quick export to Excel."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No PDF file currently open")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel",
            str(self.current_file).replace('.pdf', '.xlsx'),
            "Excel Files (*.xlsx)"
        )
        
        if output_file:
            from ..operations.advanced_export_operations import ExportToExcelOperation
            
            with console.status("Exporting to Excel..."):
                self.pdf_editor.load_document(str(self.current_file))
                
                operation = ExportToExcelOperation(
                    output_path=output_file,
                    export_type='form_data',
                    include_metadata=True
                )
                
                self.pdf_editor.add_operation(operation)
                result = self.pdf_editor.execute_operations()
                self.pdf_editor.save_document(output_file)
            
            console.print(Panel.fit(
                f"[green]✓[/green] Excel export completed\\n"
                f"[blue]Type:[/blue] {result['export_type']}\\n"
                f"[blue]Output:[/blue] {output_file}",
                title="Excel Export"
            ))
    
    def export_to_powerpoint(self):
        """Quick export to PowerPoint."""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No PDF file currently open")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Export to PowerPoint",
            str(self.current_file).replace('.pdf', '.pptx'),
            "PowerPoint Files (*.pptx)"
        )
        
        if output_file:
            from ..operations.advanced_export_operations import ExportToPowerPointOperation
            
            with console.status("Exporting to PowerPoint..."):
                self.pdf_editor.load_document(str(self.current_file))
                
                operation = ExportToPowerPointOperation(
                    output_path=output_file,
                    one_slide_per_page=True,
                    slide_size='standard_4_3',
                    extract_images=True
                )
                
                self.pdf_editor.add_operation(operation)
                result = self.pdf_editor.execute_operations()
                self.pdf_editor.save_document(output_file)
            
            console.print(Panel.fit(
                f"[green]✓[/green] PowerPoint export completed\\n"
                f"[blue]Slides:[/blue] {result['slides_created']}\\n"
                f"[blue]Images:[/blue] {result['images_extracted']}\\n"
                f"[blue]Output:[/blue] {output_file}",
                title="PowerPoint Export"
            ))
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
PDF Editor - Keyboard Shortcuts

File Operations:
Ctrl+N        - New document
Ctrl+O        - Open file
Ctrl+S        - Save file
Ctrl+Shift+S  - Save as
Ctrl+W        - Close file

Navigation:
Home          - First page
End           - Last page
PgUp          - Previous page
PgDown        - Next page

Zoom:
Ctrl++         - Zoom in
Ctrl+-         - Zoom out
Ctrl+0         - Fit to window

Search:
Ctrl+F        - Find text
F3            - Find next

Tools:
Ctrl+B        - Batch processing
Ctrl+Shift+C  - Cloud storage
Ctrl+D        - Toggle dark mode
Ctrl+Shift+D  - Toggle light mode

Accessibility:
Ctrl+Shift+=  - Increase font size
Ctrl+Shift+-  - Decrease font size
Ctrl+Shift+0  - Reset font size

Help:
F1            - Show this help
        """
        
        QMessageBox.information(self, "Keyboard Shortcuts", help_text)


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Editor")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("PDF Editor")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()
"""PDF viewer component using PySide6."""

import fitz  # PyMuPDF
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollBar, QSlider, QSpinBox, QTabWidget,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter,
    QCheckBox, QGroupBox, QFormLayout, QLineEdit,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont

from ..utils.logging import get_logger
from ..operations.ocr_operations import OCRExtractTextOperation

logger = get_logger("gui.pdf_viewer")


class OCRWorker(QThread):
    """Worker thread for OCR operations."""
    ocr_completed = pyqtSignal(dict)
    ocr_progress = pyqtSignal(int, str)
    
    def __init__(self, document, page_num, language='eng', dpi=300):
        super().__init__()
        self.document = document
        self.page_num = page_num
        self.language = language
        self.dpi = dpi
    
    def run(self):
        """Run OCR extraction in background thread."""
        try:
            self.ocr_progress.emit(0, "Starting OCR extraction...")
            
            operation = OCRExtractTextOperation(
                pages=[self.page_num],
                language=self.language,
                dpi=self.dpi
            )
            
            result = operation.execute(self.document)
            
            self.ocr_progress.emit(100, "OCR extraction completed")
            self.ocr_completed.emit(result)
            
        except Exception as e:
            self.ocr_progress.emit(0, f"OCR failed: {e}")
            logger.error(f"OCR extraction failed: {e}")


class PDFViewer(QWidget):
    """PDF viewing widget with advanced features."""
    
    # Signals
    page_changed = Signal(int, int)  # current_page, total_pages
    zoom_changed = Signal(int)      # zoom_percentage
    annotation_added = Signal(dict)    # annotation data
    form_field_clicked = Signal(dict)  # field data
    text_selected = Signal(str)       # selected text
    
    def __init__(self):
        super().__init__()
        
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 100
        self.document = None
        self.page_cache = {}
        
        # Advanced features
        self.annotations = []
        self.form_fields = []
        self.selected_text = ""
        self.ocr_results = {}
        self.dark_mode_enabled = False
        
        self.init_ui()
        
        logger.info("Advanced PDF viewer initialized")
    
    def init_ui(self):
        """Initialize the advanced user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Main PDF view tab
        self.create_pdf_view_tab()
        
        # OCR results tab
        self.create_ocr_tab()
        
        # Properties tab
        self.create_properties_tab()
        
        # Status bar
        self.create_status_bar(main_layout)
        
    def load_document(self, file_path: str):
        """Load a PDF document."""
        try:
            self.document = fitz.open(file_path)
            self.total_pages = len(self.document)
            self.current_page = 0
            self.page_cache.clear()
            
            # Update UI
            self.update_page_controls()
            self.render_current_page()
            
            logger.info(f"PDF loaded: {file_path} ({self.total_pages} pages)")
            
        except Exception as e:
            logger.error(f"Failed to load PDF {file_path}: {e}")
            raise
    
    def update_page_controls(self):
        """Update page navigation controls."""
        if self.total_pages == 0:
            return
        
        # Update spinbox range and value
        self.page_spinbox.setMaximum(self.total_pages)
        self.page_spinbox.setValue(self.current_page + 1)
        
        # Update labels
        self.page_label.setText("Page:")
        self.of_label.setText(f"of {self.total_pages}")
        
        # Update button states
        self.first_page_btn.setEnabled(self.current_page > 0)
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages - 1)
        self.last_page_btn.setEnabled(self.current_page < self.total_pages - 1)
        
        self.page_spinbox.setEnabled(True)
        
        # Emit signal
        self.page_changed.emit(self.current_page + 1, self.total_pages)
    
    def render_current_page(self):
        """Render the current page."""
        if not self.document or self.current_page >= self.total_pages:
            return
        
        try:
            # Check cache first
            cache_key = (self.current_page, self.zoom_level)
            if cache_key in self.page_cache:
                pixmap = self.page_cache[cache_key]
            else:
                # Render page
                page = self.document[self.current_page]
                zoom_factor = self.zoom_level / 100.0
                
                # Create transformation matrix
                matrix = fitz.Matrix(zoom_factor, zoom_factor)
                pix = page.get_pixmap(matrix=matrix)
                
                # Convert to QPixmap
                img_data = pix.tobytes("ppm")
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                
                # Cache the result
                self.page_cache[cache_key] = pixmap
                
                # Limit cache size
                if len(self.page_cache) > 10:
                    # Remove oldest entries
                    oldest_keys = sorted(self.page_cache.keys())[:5]
                    for key in oldest_keys:
                        del self.page_cache[key]
            
            self.pdf_display.set_pixmap(pixmap)
            
        except Exception as e:
            logger.error(f"Failed to render page {self.current_page}: {e}")
    
    def go_to_first_page(self):
        """Go to first page."""
        if self.current_page != 0:
            self.current_page = 0
            self.update_page_controls()
            self.render_current_page()
    
    def go_to_previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_controls()
            self.render_current_page()
    
    def go_to_next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_controls()
            self.render_current_page()
    
    def go_to_last_page(self):
        """Go to last page."""
        if self.current_page != self.total_pages - 1:
            self.current_page = self.total_pages - 1
            self.update_page_controls()
            self.render_current_page()
    
    def go_to_page(self, page_num: int):
        """Go to specific page number."""
        # Convert from 1-based to 0-based indexing
        page_index = page_num - 1
        if 0 <= page_index < self.total_pages:
            self.current_page = page_index
            self.update_page_controls()
            self.render_current_page()
    
    def zoom_in(self):
        """Zoom in."""
        new_zoom = min(self.zoom_level + 25, 400)
        self.set_zoom(new_zoom)
    
    def zoom_out(self):
        """Zoom out."""
        new_zoom = max(self.zoom_level - 25, 25)
        self.set_zoom(new_zoom)
    
    def set_zoom(self, zoom_level: int):
        """Set zoom level."""
        if zoom_level != self.zoom_level:
            self.zoom_level = zoom_level
            self.zoom_label.setText(f"{zoom_level}%")
            
            # Update zoom controls
            self.zoom_label.setText(f"{zoom_level}%")
            
            # Re-render page with new zoom
            self.render_current_page()
            
            # Emit signal
            self.zoom_changed.emit(zoom_level)
    
    def create_pdf_view_tab(self):
        """Create the main PDF viewing tab."""
        pdf_widget = QWidget()
        layout = QVBoxLayout(pdf_widget)
        
        # Advanced toolbar
        self.create_advanced_toolbar(layout)
        
        # Splitter for PDF display and side panel
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # PDF display area (left)
        self.create_pdf_display_area(splitter)
        
        # Side panel (right) for annotations and info
        self.create_side_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([800, 300])
        
        self.tab_widget.addTab(pdf_widget, "PDF View")
    
    def create_advanced_toolbar(self, layout):
        """Create advanced toolbar with all controls."""
        toolbar_layout = QHBoxLayout()
        
        # File operations group
        file_group = QGroupBox("File")
        file_layout = QHBoxLayout()
        
        self.dark_mode_btn = QPushButton("🌙 Dark Mode")
        self.dark_mode_btn.setCheckable(True)
        self.dark_mode_btn.toggled.connect(self.toggle_dark_mode)
        file_layout.addWidget(self.dark_mode_btn)
        
        self.ocr_btn = QPushButton("🔍 OCR Page")
        self.ocr_btn.clicked.connect(self.extract_current_page_ocr)
        file_layout.addWidget(self.ocr_btn)
        
        file_group.setLayout(file_layout)
        toolbar_layout.addWidget(file_group)
        
        # Navigation group
        nav_group = QGroupBox("Navigation")
        nav_layout = QHBoxLayout()
        
        self.first_page_btn = QPushButton("<<")
        self.first_page_btn.clicked.connect(self.go_to_first_page)
        self.first_page_btn.setEnabled(False)
        nav_layout.addWidget(self.first_page_btn)
        
        self.prev_page_btn = QPushButton("<")
        self.prev_page_btn.clicked.connect(self.go_to_previous_page)
        self.prev_page_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_page_btn)
        
        # Page controls
        self.page_label = QLabel("No document")
        nav_layout.addWidget(self.page_label)
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        self.page_spinbox.setEnabled(False)
        nav_layout.addWidget(self.page_spinbox)
        
        self.of_label = QLabel("of 0")
        nav_layout.addWidget(self.of_label)
        
        self.next_page_btn = QPushButton(">")
        self.next_page_btn.clicked.connect(self.go_to_next_page)
        self.next_page_btn.setEnabled(False)
        nav_layout.addWidget(self.next_page_btn)
        
        self.last_page_btn = QPushButton(">>")
        self.last_page_btn.clicked.connect(self.go_to_last_page)
        self.last_page_btn.setEnabled(False)
        nav_layout.addWidget(self.last_page_btn)
        
        nav_group.setLayout(nav_layout)
        toolbar_layout.addWidget(nav_group)
        
        # Zoom group
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QHBoxLayout()
        
        self.zoom_out_btn = QPushButton("➖")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(25, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.set_zoom)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setRange(25, 400)
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.valueChanged.connect(self.set_zoom)
        zoom_layout.addWidget(self.zoom_spinbox)
        
        self.zoom_in_btn = QPushButton("➕")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_label)
        
        # Connect zoom controls
        self.zoom_slider.valueChanged.connect(self.zoom_spinbox.setValue)
        self.zoom_spinbox.valueChanged.connect(self.zoom_slider.setValue)
        
        zoom_group.setLayout(zoom_layout)
        toolbar_layout.addWidget(zoom_group)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
    
    def create_pdf_display_area(self, splitter):
        """Create the main PDF display area."""
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        
        # Main PDF display
        self.pdf_display = AdvancedPDFDisplayWidget()
        self.pdf_display.text_selected.connect(self.on_text_selected)
        self.pdf_display.annotation_clicked.connect(self.on_annotation_clicked)
        self.pdf_display.form_field_clicked.connect(self.on_form_field_clicked)
        display_layout.addWidget(self.pdf_display)
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        display_layout.addWidget(self.progress_bar)
        
        # Scroll bars
        scrollbar_layout = QHBoxLayout()
        
        self.h_scrollbar = QScrollBar(Qt.Horizontal)
        self.h_scrollbar.valueChanged.connect(self.on_horizontal_scroll)
        scrollbar_layout.addWidget(self.h_scrollbar)
        
        self.v_scrollbar = QScrollBar(Qt.Vertical)
        self.v_scrollbar.valueChanged.connect(self.on_vertical_scroll)
        scrollbar_layout.addWidget(self.v_scrollbar)
        
        display_layout.addLayout(scrollbar_layout)
        
        splitter.addWidget(display_widget)
    
    def create_side_panel(self, splitter):
        """Create side panel for annotations and properties."""
        side_widget = QWidget()
        side_layout = QVBoxLayout(side_widget)
        
        # Annotations panel
        self.annotations_list = QTreeWidget()
        self.annotations_list.setHeaderLabel("Annotations")
        self.annotations_list.itemClicked.connect(self.on_annotation_item_clicked)
        side_layout.addWidget(self.annotations_list)
        
        # Form fields panel
        self.form_fields_list = QTreeWidget()
        self.form_fields_list.setHeaderLabel("Form Fields")
        self.form_fields_list.itemClicked.connect(self.on_form_field_item_clicked)
        side_layout.addWidget(self.form_fields_list)
        
        splitter.addWidget(side_widget)
    
    def create_ocr_tab(self):
        """Create OCR results tab."""
        ocr_widget = QWidget()
        layout = QVBoxLayout(ocr_widget)
        
        # OCR controls
        controls_layout = QHBoxLayout()
        
        self.ocr_language_combo = QComboBox()
        self.ocr_language_combo.addItems(['eng', 'spa', 'fra', 'deu', 'jpn'])
        self.ocr_language_combo.setCurrentText('eng')
        controls_layout.addWidget(QLabel("Language:"))
        controls_layout.addWidget(self.ocr_language_combo)
        
        self.ocr_dpi_spinbox = QSpinBox()
        self.ocr_dpi_spinbox.setRange(72, 600)
        self.ocr_dpi_spinbox.setValue(300)
        controls_layout.addWidget(QLabel("DPI:"))
        controls_layout.addWidget(self.ocr_dpi_spinbox)
        
        self.ocr_confidence_spinbox = QSpinBox()
        self.ocr_confidence_spinbox.setRange(0, 100)
        self.ocr_confidence_spinbox.setValue(70)
        controls_layout.addWidget(QLabel("Confidence:"))
        controls_layout.addWidget(self.ocr_confidence_spinbox)
        
        self.extract_all_ocr_btn = QPushButton("Extract All Pages")
        self.extract_all_ocr_btn.clicked.connect(self.extract_all_pages_ocr)
        controls_layout.addWidget(self.extract_all_ocr_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # OCR results area
        self.ocr_results_text = QTextEdit()
        self.ocr_results_text.setPlaceholderText("OCR results will appear here...")
        self.ocr_results_text.setReadOnly(True)
        layout.addWidget(self.ocr_results_text)
        
        self.tab_widget.addTab(ocr_widget, "OCR")
    
    def create_properties_tab(self):
        """Create document properties tab."""
        props_widget = QWidget()
        layout = QVBoxLayout(props_widget)
        
        # Document info
        self.props_tree = QTreeWidget()
        self.props_tree.setHeaderLabel("Document Properties")
        layout.addWidget(self.props_tree)
        
        self.tab_widget.addTab(props_widget, "Properties")
    
    def create_status_bar(self, layout):
        """Create status bar with additional info."""
        status_layout = QHBoxLayout()
        
        # Status message
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        # Document info
        self.doc_info_label = QLabel("No document loaded")
        status_layout.addWidget(self.doc_info_label)
        
        status_layout.addStretch()
        
        # OCR status
        self.ocr_status_label = QLabel()
        status_layout.addWidget(self.ocr_status_label)
        
        layout.addLayout(status_layout)
    
    def fit_to_window(self):
        """Fit PDF to window size."""
        if self.pdf_display.pixmap:
            widget_size = self.pdf_display.size()
            pixmap_size = self.pdf_display.pixmap.size()
            
            # Calculate zoom factor
            zoom_x = (widget_size.width() - 40) / pixmap_size.width()
            zoom_y = (widget_size.height() - 40) / pixmap_size.height()
            zoom_factor = min(zoom_x, zoom_y)
            
            # Set zoom
            new_zoom = int(self.zoom_level * zoom_factor)
            self.set_zoom(min(max(new_zoom, 25), 400))
    
    def toggle_dark_mode(self, enabled: bool):
        """Toggle dark mode for PDF display."""
        self.dark_mode_enabled = enabled
        if enabled:
            self.pdf_display.setStyleSheet("background-color: #1e1e1e; color: #f0f0f0;")
            self.dark_mode_btn.setText("☀️ Light Mode")
        else:
            self.pdf_display.setStyleSheet("background-color: white; color: black;")
            self.dark_mode_btn.setText("🌙 Dark Mode")
        
        # Re-render current page
        if self.document:
            self.render_current_page()
    
    def extract_current_page_ocr(self):
        """Extract OCR for current page."""
        if not self.document:
            QMessageBox.warning(self, "Warning", "No document loaded")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Extracting OCR for current page...")
        
        # Create OCR worker
        self.ocr_worker = OCRWorker(
            self.document, 
            self.current_page,
            self.ocr_language_combo.currentText(),
            self.ocr_dpi_spinbox.value()
        )
        
        self.ocr_worker.ocr_completed.connect(self.on_ocr_completed)
        self.ocr_worker.ocr_progress.connect(self.on_ocr_progress)
        self.ocr_worker.start()
    
    def extract_all_pages_ocr(self):
        """Extract OCR for all pages."""
        if not self.document:
            QMessageBox.warning(self, "Warning", "No document loaded")
            return
        
        QMessageBox.information(self, "Info", "Batch OCR extraction coming soon!")
    
    def on_ocr_completed(self, result: dict):
        """Handle OCR completion."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
        # Update OCR results
        page_num = result['results'][0]['page_number'] if result['results'] else self.current_page
        self.ocr_results[page_num] = result
        
        # Update OCR text display
        if result['results']:
            ocr_text = result['results'][0]['full_text']
            self.ocr_results_text.setPlainText(ocr_text)
            self.status_label.setText(f"OCR completed for page {page_num}")
        else:
            self.status_label.setText("No text found")
    
    def on_ocr_progress(self, progress: int, message: str):
        """Handle OCR progress updates."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_text_selected(self, text: str):
        """Handle text selection."""
        self.selected_text = text
        self.text_selected.emit(text)
        self.status_label.setText(f"Selected: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def on_annotation_clicked(self, annotation: dict):
        """Handle annotation click."""
        self.annotation_added.emit(annotation)
    
    def on_form_field_clicked(self, field: dict):
        """Handle form field click."""
        self.form_field_clicked.emit(field)
    
    def on_annotation_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle annotation item click."""
        # Navigate to annotation page
        annotation_data = item.data(0, Qt.UserRole)
        if annotation_data and 'page' in annotation_data:
            self.go_to_page(annotation_data['page'] + 1)
    
    def on_form_field_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle form field item click."""
        # Navigate to field page and highlight
        field_data = item.data(0, Qt.UserRole)
        if field_data and 'page' in field_data:
            self.go_to_page(field_data['page'] + 1)
    
    def on_horizontal_scroll(self, value: int):
        """Handle horizontal scroll."""
        self.pdf_display.set_horizontal_scroll(value)
    
    def on_vertical_scroll(self, value: int):
        """Handle vertical scroll."""
        self.pdf_display.set_vertical_scroll(value)


class AdvancedPDFDisplayWidget(QWidget):
    """Advanced widget for displaying PDF pages with annotations and interaction."""
    
    # Signals
    text_selected = pyqtSignal(str)
    annotation_clicked = pyqtSignal(dict)
    form_field_clicked = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        self.pixmap = None
        self.annotations = []
        self.form_fields = []
        self.horizontal_offset = 0
        self.vertical_offset = 0
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        self.dark_mode = False
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        
    def set_pixmap(self, pixmap: QPixmap):
        """Set PDF page pixmap."""
        self.pixmap = pixmap
        self.update()
        self.update_scroll_bars()
    
    def set_annotations(self, annotations: List[dict]):
        """Set annotations for current page."""
        self.annotations = annotations
        self.update()
    
    def set_form_fields(self, form_fields: List[dict]):
        """Set form fields for current page."""
        self.form_fields = form_fields
        self.update()
    
    def set_horizontal_scroll(self, offset: int):
        """Set horizontal scroll offset."""
        self.horizontal_offset = offset
        self.update()
    
    def set_vertical_scroll(self, offset: int):
        """Set vertical scroll offset."""
        self.vertical_offset = offset
        self.update()
    
    def update_scroll_bars(self):
        """Update scrollbar ranges based on pixmap size."""
        if self.pixmap:
            max_h = max(0, self.pixmap.width() - self.width())
            max_v = max(0, self.pixmap.height() - self.height())
            # Parent widget would update scrollbars
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.selection_start = event.pos()
            self.selection_rect = None
            
            # Check for annotation clicks
            self.check_annotation_click(event.pos())
            
            # Check for form field clicks
            self.check_form_field_click(event.pos())
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.selection_start and event.buttons() & Qt.LeftButton:
            self.selection_end = event.pos()
            self.update_selection_rect()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton and self.selection_rect:
            self.extract_selected_text()
    
    def check_annotation_click(self, pos):
        """Check if click is on an annotation."""
        for annotation in self.annotations:
            rect = annotation.get('rect')
            if rect and self.point_in_rect(pos, rect):
                self.annotation_clicked.emit(annotation)
                return
        return False
    
    def check_form_field_click(self, pos):
        """Check if click is on a form field."""
        for field in self.form_fields:
            rect = field.get('rect')
            if rect and self.point_in_rect(pos, rect):
                self.form_field_clicked.emit(field)
                return
        return False
    
    def point_in_rect(self, pos, rect: Tuple[int, int, int, int]):
        """Check if point is within rectangle."""
        x, y = pos.x(), pos.y()
        x0, y0, x1, y1 = rect
        return x0 <= x <= x1 and y0 <= y <= y1
    
    def update_selection_rect(self):
        """Update selection rectangle."""
        if self.selection_start and self.selection_end:
            x1 = min(self.selection_start.x(), self.selection_end.x())
            y1 = min(self.selection_start.y(), self.selection_end.y())
            x2 = max(self.selection_start.x(), self.selection_end.x())
            y2 = max(self.selection_start.y(), self.selection_end.y())
            self.selection_rect = (x1, y1, x2 - x1, y2 - y1)
    
    def extract_selected_text(self):
        """Extract text from selection (simplified)."""
        if self.selection_rect:
            # This is a simplified implementation
            # In practice, you'd need to integrate with OCR or text extraction
            selected_text = f"Selected area: {self.selection_rect}"
            self.text_selected.emit(selected_text)
            self.selection_rect = None
            self.update()
    
    def paintEvent(self, event):
        """Paint PDF page with overlays."""
        painter = QPainter(self)
        
        # Background
        if self.dark_mode:
            painter.fillRect(self.rect(), QColor("#1e1e1e"))
        else:
            painter.fillRect(self.rect(), QColor("white"))
        
        if self.pixmap:
            # Calculate centered position
            x = max(0, (self.width() - self.pixmap.width()) // 2 - self.horizontal_offset)
            y = max(0, (self.height() - self.pixmap.height()) // 2 - self.vertical_offset)
            
            # Draw PDF page
            if self.dark_mode:
                # Invert colors for dark mode
                inverted_pixmap = self.pixmap.createMaskFromColor(QColor("black"))
                painter.setPen(QPen(QColor("#f0f0f0")))
                painter.drawPixmap(x, y, inverted_pixmap)
            else:
                painter.drawPixmap(x, y, self.pixmap)
            
            # Draw form fields
            self.draw_form_fields(painter, x, y)
            
            # Draw annotations
            self.draw_annotations(painter, x, y)
            
            # Draw selection rectangle
            if self.selection_rect:
                pen = QPen(QColor("#0078d7"), 2, Qt.DashLine)
                painter.setPen(pen)
                painter.drawRect(*self.selection_rect)
    
    def draw_form_fields(self, painter, offset_x, offset_y):
        """Draw form fields on the page."""
        for field in self.form_fields:
            rect = field.get('rect')
            if not rect:
                continue
            
            field_type = field.get('type', 'text')
            
            # Adjust for PDF offset
            field_rect = (
                rect[0] + offset_x,
                rect[1] + offset_y,
                rect[2] - rect[0],
                rect[3] - rect[1]
            )
            
            # Set pen based on field type
            if field_type == 'text':
                painter.setPen(QPen(QColor("#0066cc"), 1))
                painter.setBrush(QColor("#e6f3ff"))
            elif field_type == 'checkbox':
                painter.setPen(QPen(QColor("#00aa00"), 1))
                painter.setBrush(QColor("#e6ffe6"))
            elif field_type == 'radio':
                painter.setPen(QPen(QColor("#cc6600"), 1))
                painter.setBrush(QColor("#fff3e6"))
            else:
                painter.setPen(QPen(QColor("#666666"), 1))
                painter.setBrush(QColor("#f5f5f5"))
            
            painter.drawRect(*field_rect)
            
            # Add field label
            field_name = field.get('name', '')
            if field_name:
                painter.setPen(QPen(QColor("black")))
                painter.drawText(field_rect[0] + 2, field_rect[1] - 2, field_name)
    
    def draw_annotations(self, painter, offset_x, offset_y):
        """Draw annotations on the page."""
        for annotation in self.annotations:
            rect = annotation.get('rect')
            if not rect:
                continue
            
            ann_type = annotation.get('type', 'highlight')
            
            # Adjust for PDF offset
            ann_rect = (
                rect[0] + offset_x,
                rect[1] + offset_y,
                rect[2] - rect[0],
                rect[3] - rect[1]
            )
            
            # Set style based on annotation type
            color = QColor(annotation.get('color', '#ffff00'))
            
            if ann_type == 'highlight':
                painter.fillRect(*ann_rect, QColor(color.red(), color.green(), color.blue(), 50))
                painter.setPen(QPen(color, 1))
                painter.drawRect(*ann_rect)
            elif ann_type == 'underline':
                painter.setPen(QPen(color, 2))
                y = ann_rect[1] + ann_rect[3] - 2
                painter.drawLine(ann_rect[0], y, ann_rect[0] + ann_rect[2], y)
            elif ann_type == 'strikeout':
                painter.setPen(QPen(color, 2))
                y = ann_rect[1] + ann_rect[3] // 2
                painter.drawLine(ann_rect[0], y, ann_rect[0] + ann_rect[2], y)
            elif ann_type in ['rectangle', 'circle']:
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 30)))
                
                if ann_type == 'rectangle':
                    painter.drawRect(*ann_rect)
                else:
                    painter.drawEllipse(*ann_rect)
            elif ann_type == 'text':
                painter.setPen(QPen(color, 1))
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 20)))
                painter.drawRoundedRect(*ann_rect, 5, 5)
                
                # Add text content
                content = annotation.get('content', '')
                if content:
                    painter.drawText(ann_rect[0] + 5, ann_rect[1] + 15, content[:50])
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update_scroll_bars()


class PDFDisplayWidget(QWidget):
    """Legacy PDF display widget for backward compatibility."""
    
    def __init__(self):
        super().__init__()
        self.advanced_display = AdvancedPDFDisplayWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.advanced_display)
        
        # Forward signals
        self.advanced_display.text_selected.connect(lambda x: None)
        self.advanced_display.annotation_clicked.connect(lambda x: None)
        self.advanced_display.form_field_clicked.connect(lambda x: None)
    
    def set_pixmap(self, pixmap: QPixmap):
        """Set PDF page pixmap."""
        self.advanced_display.set_pixmap(pixmap)
    
    def set_horizontal_scroll(self, offset: int):
        """Set horizontal scroll offset."""
        self.advanced_display.set_horizontal_scroll(offset)
    
    def set_vertical_scroll(self, offset: int):
        """Set vertical scroll offset."""
        self.advanced_display.set_vertical_scroll(offset)
    
    def update_scroll_bars(self):
        """Update scrollbar ranges."""
        self.advanced_display.update_scroll_bars()
    
    def paintEvent(self, event):
        """Paint event (handled by advanced display)."""
        pass
    
    def resizeEvent(self, event):
        """Handle resize events."""
        self.advanced_display.resizeEvent(event)
    
    def set_horizontal_scroll(self, offset: int):
        """Set horizontal scroll offset."""
        self.horizontal_offset = offset
        self.update()
    
    def set_vertical_scroll(self, offset: int):
        """Set vertical scroll offset."""
        self.vertical_offset = offset
        self.update()
    
    def update_scroll_bars(self):
        """Update scrollbar ranges based on pixmap size."""
        if self.pixmap:
            # Update scroll ranges based on pixmap and widget size
            max_h = max(0, self.pixmap.width() - self.width())
            max_v = max(0, self.pixmap.height() - self.height())
            
            # This would need to be connected to actual scrollbars
            # For now, we'll handle it in the parent widget
    
    def paintEvent(self, event):
        """Paint the PDF page."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        
        if self.pixmap:
            # Center the image if smaller than widget
            x = max(0, (self.width() - self.pixmap.width()) // 2 - self.horizontal_offset)
            y = max(0, (self.height() - self.pixmap.height()) // 2 - self.vertical_offset)
            
            painter.drawPixmap(x, y, self.pixmap)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update_scroll_bars()
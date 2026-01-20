"""Theme manager for GUI application."""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from ..utils.logging import get_logger

logger = get_logger("gui.theme_manager")


class ThemeManager(QObject):
    """Manages application themes (light/dark mode)."""
    
    def __init__(self):
        super().__init__()
        
        # Define themes
        self.themes = {
            'light': {
                'window_bg': QColor(240, 240, 240),
                'text_color': QColor(30, 30, 30),
                'button_bg': QColor(250, 250, 250),
                'button_hover': QColor(230, 230, 230),
                'panel_bg': QColor(245, 245, 245),
                'border_color': QColor(200, 200, 200),
                'accent_color': QColor(0, 120, 215)
            },
            'dark': {
                'window_bg': QColor(30, 30, 30),
                'text_color': QColor(240, 240, 240),
                'button_bg': QColor(45, 45, 45),
                'button_hover': QColor(60, 60, 60),
                'panel_bg': QColor(40, 40, 40),
                'border_color': QColor(70, 70, 70),
                'accent_color': QColor(0, 120, 215)
            }
        }
    
    def apply_theme(self, widget, theme_name: str):
        """Apply theme to widget and its children."""
        if theme_name not in self.themes:
            logger.warning(f"Unknown theme: {theme_name}")
            return
        
        theme = self.themes[theme_name]
        app = QApplication.instance()
        
        if app:
            palette = app.palette()
            
            # Apply theme colors
            palette.setColor(QPalette.Window, theme['window_bg'])
            palette.setColor(QPalette.WindowText, theme['text_color'])
            palette.setColor(QPalette.Base, theme['panel_bg'])
            palette.setColor(QPalette.AlternateBase, theme['button_bg'])
            palette.setColor(QPalette.ToolTipBase, theme['text_color'])
            palette.setColor(QPalette.ToolTipText, theme['text_color'])
            palette.setColor(QPalette.Text, theme['text_color'])
            palette.setColor(QPalette.Button, theme['button_bg'])
            palette.setColor(QPalette.ButtonText, theme['text_color'])
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, theme['accent_color'])
            palette.setColor(QPalette.Highlight, theme['accent_color'])
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
            
            app.setPalette(palette)
            
            # Apply stylesheet for additional styling
            self.apply_stylesheet(app, theme_name)
            
            logger.info(f"Applied {theme_name} theme")
    
    def apply_stylesheet(self, app, theme_name: str):
        """Apply stylesheet for advanced styling."""
        if theme_name == 'dark':
            stylesheet = """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QDockWidget {
                background-color: #282828;
                color: #f0f0f0;
                border: 1px solid #464646;
            }
            QDockWidget::title {
                background-color: #2d2d2d;
                padding: 5px;
                border-bottom: 1px solid #464646;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: 1px solid #464646;
                spacing: 3px;
            }
            QToolBar QToolButton {
                background-color: #3d3d3d;
                border: 1px solid #464646;
                border-radius: 3px;
                padding: 4px;
                margin: 1px;
            }
            QToolBar QToolButton:hover {
                background-color: #4d4d4d;
            }
            QToolBar QToolButton:pressed {
                background-color: #5d5d5d;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border-bottom: 1px solid #464646;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #464646;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border-top: 1px solid #464646;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #f0f0f0;
                border: 1px solid #464646;
                border-radius: 3px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3d3d3d;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d7;
                border: 1px solid #464646;
                width: 14px;
                border-radius: 7px;
                margin: -4px 0;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border: 1px solid #464646;
            }
            QScrollBar::handle:vertical {
                background-color: #4d4d4d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5d5d5d;
            }
            """
        else:
            stylesheet = """
            QMainWindow {
                background-color: #f0f0f0;
            }
            QDockWidget {
                background-color: #f5f5f5;
                color: #1e1e1e;
                border: 1px solid #c8c8c8;
            }
            QDockWidget::title {
                background-color: #fafafa;
                padding: 5px;
                border-bottom: 1px solid #c8c8c8;
            }
            QToolBar {
                background-color: #fafafa;
                border: 1px solid #c8c8c8;
                spacing: 3px;
            }
            QToolBar QToolButton {
                background-color: #ffffff;
                border: 1px solid #c8c8c8;
                border-radius: 3px;
                padding: 4px;
                margin: 1px;
            }
            QToolBar QToolButton:hover {
                background-color: #e6e6e6;
            }
            QToolBar QToolButton:pressed {
                background-color: #d4d4d4;
            }
            QMenuBar {
                background-color: #fafafa;
                color: #1e1e1e;
                border-bottom: 1px solid #c8c8c8;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #e6e6e6;
            }
            QMenu {
                background-color: #fafafa;
                color: #1e1e1e;
                border: 1px solid #c8c8c8;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #e6e6e6;
            }
            QStatusBar {
                background-color: #fafafa;
                color: #1e1e1e;
                border-top: 1px solid #c8c8c8;
            }
            QPushButton {
                background-color: #ffffff;
                color: #1e1e1e;
                border: 1px solid #c8c8c8;
                border-radius: 3px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d4d4d4;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #ffffff;
                border: 1px solid #c8c8c8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d7;
                border: 1px solid #c8c8c8;
                width: 14px;
                border-radius: 7px;
                margin: -4px 0;
            }
            QScrollBar:vertical {
                background-color: #fafafa;
                width: 12px;
                border: 1px solid #c8c8c8;
            }
            QScrollBar::handle:vertical {
                background-color: #e6e6e6;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #d4d4d4;
            }
            """
        
        app.setStyleSheet(stylesheet)
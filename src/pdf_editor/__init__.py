"""PDF Editor - A comprehensive PDF editing tool."""

__version__ = "0.1.0"
__author__ = "PDF Editor Team"
__description__ = "A comprehensive PDF editing tool"

from .core.document import PDFDocument
from .core.editor import PDFEditor

__all__ = ["PDFDocument", "PDFEditor"]
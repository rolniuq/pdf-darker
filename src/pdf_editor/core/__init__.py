"""Core module for PDF document handling."""

from .base import (
    BaseOperation, OperationType, OperationResult, PDFException,
    ValidationError, ProcessingError, PDFDocument as BasePDFDocument,
    OperationManager, PluginManager, Plugin
)
from .document import PDFDocument, PDFPage
from .editor import PDFEditor

__all__ = [
    "BaseOperation", "OperationType", "OperationResult", "PDFException",
    "ValidationError", "ProcessingError", "BasePDFDocument",
    "OperationManager", "PluginManager", "Plugin",
    "PDFDocument", "PDFPage", "PDFEditor"
]
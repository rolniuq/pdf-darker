"""Operations module for PDF editing operations."""

from .text_operations import TextOperation, AddTextOperation, ReplaceTextOperation, DeleteTextOperation
from .page_operations import PageOperation, RotatePageOperation, DeletePageOperation, ReorderPagesOperation
from .image_operations import ImageOperation, AddImageOperation, ReplaceImageOperation
from .dark_mode import DarkModeOperation
from .dark_mode_legacy import convert_pdf_to_dark

__all__ = [
    # Text operations
    "TextOperation",
    "AddTextOperation", 
    "ReplaceTextOperation",
    "DeleteTextOperation",
    
    # Page operations
    "PageOperation",
    "RotatePageOperation",
    "DeletePageOperation", 
    "ReorderPagesOperation",
    
    # Image operations
    "ImageOperation",
    "AddImageOperation",
    "ReplaceImageOperation",
    
    # Special operations
    "DarkModeOperation",
    "convert_pdf_to_dark",
]
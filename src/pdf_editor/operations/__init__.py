"""Operations module for PDF editing operations."""

from .text_operations import TextOperation, AddTextOperation, ReplaceTextOperation, DeleteTextOperation
from .page_operations import PageOperation, RotatePageOperation, DeletePageOperation, ReorderPagesOperation
from .image_operations import ImageOperation, AddImageOperation, ReplaceImageOperation
from .form_operations import (
    FormOperation, CreateFormFieldOperation, FillFormFieldOperation, 
    ValidateFormOperation, ExportFormDataOperation
)
from .annotation_operations import (
    AnnotationOperation, AddAnnotationOperation, AddCommentOperation,
    AddDrawingOperation, AddFreehandOperation
)
from .security_operations import (
    SecurityOperation, SetPasswordOperation, AddSignatureOperation,
    EditMetadataOperation, AddSecurityWatermarkOperation, ExportMetadataOperation
)
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
    
    # Form operations
    "FormOperation",
    "CreateFormFieldOperation",
    "FillFormFieldOperation",
    "ValidateFormOperation",
    "ExportFormDataOperation",
    
    # Annotation operations
    "AnnotationOperation",
    "AddAnnotationOperation",
    "AddCommentOperation",
    "AddDrawingOperation",
    "AddFreehandOperation",
    
    # Security operations
    "SecurityOperation",
    "SetPasswordOperation",
    "AddSignatureOperation",
    "EditMetadataOperation",
    "AddSecurityWatermarkOperation",
    "ExportMetadataOperation",
    
    # Special operations
    "DarkModeOperation",
    "convert_pdf_to_dark",
]
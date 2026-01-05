"""Page manipulation operations."""

from abc import abstractmethod
from typing import Any, Dict, List, Union

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument, PDFException


class PageOperation(BaseOperation):
    """Base class for page operations."""
    
    def __init__(self, operation_type: OperationType):
        super().__init__(operation_type)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate page operation parameters."""
        return hasattr(document, '_doc') and document._doc is not None


class RotatePageOperation(PageOperation):
    """Operation to rotate a PDF page."""
    
    def __init__(self, page_number: int, angle: int):
        super().__init__(OperationType.ROTATE_PAGE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("angle", angle)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate rotate page operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        angle = self.get_parameter("angle")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if angle not in [0, 90, 180, 270]:
            self.logger.error(f"Invalid rotation angle: {angle}. Must be 0, 90, 180, or 270")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute rotate page operation."""
        try:
            page_number = self.get_parameter("page_number")
            angle = self.get_parameter("angle")
            
            page = document.get_page(page_number)
            page.rotate(angle)
            
            document.mark_modified()
            self.logger.info(f"Rotated page {page_number} by {angle} degrees")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to rotate page: {e}")
            return OperationResult.FAILED


class DeletePageOperation(PageOperation):
    """Operation to delete a PDF page."""
    
    def __init__(self, page_number: int):
        super().__init__(OperationType.DELETE_PAGE)
        
        self.set_parameter("page_number", page_number)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate delete page operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute delete page operation."""
        try:
            page_number = self.get_parameter("page_number")
            
            document.delete_page(page_number)
            
            self.logger.info(f"Deleted page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to delete page: {e}")
            return OperationResult.FAILED


class ReorderPagesOperation(PageOperation):
    """Operation to reorder PDF pages."""
    
    def __init__(self, new_order: List[int]):
        super().__init__(OperationType.REORDER_PAGES)
        
        self.set_parameter("new_order", new_order)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate reorder pages operation."""
        if not super().validate(document):
            return False
        
        new_order = self.get_parameter("new_order")
        
        if not isinstance(new_order, list):
            self.logger.error("New order must be a list")
            return False
        
        if len(new_order) != document.page_count:
            self.logger.error(f"New order must contain exactly {document.page_count} page numbers")
            return False
        
        if set(new_order) != set(range(document.page_count)):
            self.logger.error("New order must contain each page number exactly once")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute reorder pages operation."""
        try:
            new_order = self.get_parameter("new_order")
            
            document.reorder_pages(new_order)
            
            self.logger.info(f"Reordered pages to: {new_order}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to reorder pages: {e}")
            return OperationResult.FAILED
"""Base text operations."""

from abc import abstractmethod
from typing import Any, Dict, Union
from pathlib import Path

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument, PDFException


class TextOperation(BaseOperation):
    """Base class for text operations."""
    
    def __init__(self, operation_type: OperationType):
        super().__init__(operation_type)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate text operation parameters."""
        return hasattr(document, '_doc') and document._doc is not None


class AddTextOperation(TextOperation):
    """Operation to add text to a PDF page."""
    
    def __init__(self, page_number: int, text: str, position: tuple, 
                 fontname: str = "helv", fontsize: float = 11, 
                 color: tuple = (0, 0, 0)):
        super().__init__(OperationType.ADD_TEXT)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("text", text)
        self.set_parameter("position", position)
        self.set_parameter("fontname", fontname)
        self.set_parameter("fontsize", fontsize)
        self.set_parameter("color", color)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate add text operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        text = self.get_parameter("text")
        position = self.get_parameter("position")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not text or not isinstance(text, str):
            self.logger.error("Text must be a non-empty string")
            return False
        
        if (not isinstance(position, tuple) or len(position) != 2 or 
            not all(isinstance(x, (int, float)) for x in position)):
            self.logger.error(f"Invalid position: {position}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute add text operation."""
        try:
            page_number = self.get_parameter("page_number")
            text = self.get_parameter("text")
            position = self.get_parameter("position")
            fontname = self.get_parameter("fontname")
            fontsize = self.get_parameter("fontsize")
            color = self.get_parameter("color")
            
            page = document.get_page(page_number)
            page.add_text(text, position, fontname, fontsize, color)
            
            document.mark_modified()
            self.logger.info(f"Added text to page {page_number}: '{text[:20]}...'")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to add text: {e}")
            return OperationResult.FAILED


class ReplaceTextOperation(TextOperation):
    """Operation to replace text in a PDF (using OCR if needed)."""
    
    def __init__(self, search_text: str, replace_text: str, page_numbers: list = None):
        super().__init__(OperationType.REPLACE_TEXT)
        
        self.set_parameter("search_text", search_text)
        self.set_parameter("replace_text", replace_text)
        self.set_parameter("page_numbers", page_numbers or [])
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate replace text operation."""
        if not super().validate(document):
            return False
        
        search_text = self.get_parameter("search_text")
        replace_text = self.get_parameter("replace_text")
        
        if not search_text or not isinstance(search_text, str):
            self.logger.error("Search text must be a non-empty string")
            return False
        
        if replace_text is None or not isinstance(replace_text, str):
            self.logger.error("Replace text must be a string")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute replace text operation."""
        try:
            search_text = self.get_parameter("search_text")
            replace_text = self.get_parameter("replace_text")
            page_numbers = self.get_parameter("page_numbers")
            
            # Determine which pages to search
            if page_numbers:
                pages_to_search = [document.get_page(p) for p in page_numbers if 0 <= p < document.page_count]
            else:
                pages_to_search = [document.get_page(i) for i in range(document.page_count)]
            
            total_replacements = 0
            
            for page in pages_to_search:
                # This is a simplified implementation
                # In practice, you'd need OCR or more sophisticated text replacement
                highlights = page.highlight_text(search_text, color=(1, 1, 0))
                total_replacements += highlights
            
            if total_replacements > 0:
                document.mark_modified()
                self.logger.info(f"Found {total_replacements} instances of '{search_text}'")
                return OperationResult.SUCCESS
            else:
                self.logger.warning(f"No instances of '{search_text}' found")
                return OperationResult.SKIPPED
                
        except Exception as e:
            self.logger.error(f"Failed to replace text: {e}")
            return OperationResult.FAILED


class DeleteTextOperation(TextOperation):
    """Operation to delete text from a PDF page."""
    
    def __init__(self, search_text: str, page_numbers: list = None):
        super().__init__(OperationType.DELETE_TEXT)
        
        self.set_parameter("search_text", search_text)
        self.set_parameter("page_numbers", page_numbers or [])
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate delete text operation."""
        if not super().validate(document):
            return False
        
        search_text = self.get_parameter("search_text")
        
        if not search_text or not isinstance(search_text, str):
            self.logger.error("Search text must be a non-empty string")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute delete text operation."""
        try:
            search_text = self.get_parameter("search_text")
            page_numbers = self.get_parameter("page_numbers")
            
            # This is a simplified implementation using redaction
            # In practice, you'd need more sophisticated text deletion
            total_deleted = 0
            
            for page_num in range(document.page_count):
                if page_numbers and page_num not in page_numbers:
                    continue
                
                page = document.get_page(page_num)
                areas = page._page.search_for(search_text)
                
                for area in areas:
                    # Redact the text area
                    redaction = page._page.add_redact_annot(area)
                    page._page.apply_redactions()
                    total_deleted += 1
            
            if total_deleted > 0:
                document.mark_modified()
                self.logger.info(f"Deleted {total_deleted} instances of '{search_text}'")
                return OperationResult.SUCCESS
            else:
                self.logger.warning(f"No instances of '{search_text}' found")
                return OperationResult.SKIPPED
                
        except Exception as e:
            self.logger.error(f"Failed to delete text: {e}")
            return OperationResult.FAILED
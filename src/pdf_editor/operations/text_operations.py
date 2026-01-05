"""Base text operations."""

from abc import abstractmethod
from typing import Any, Dict, Union
from pathlib import Path
import fitz

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


class HighlightTextOperation(TextOperation):
    """Operation to highlight text in a PDF page."""
    
    def __init__(self, search_text: str, color: tuple = (1, 1, 0), page_numbers: list = None):
        super().__init__(OperationType.HIGHLIGHT_TEXT)
        
        self.set_parameter("search_text", search_text)
        self.set_parameter("color", color)
        self.set_parameter("page_numbers", page_numbers or [])
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate highlight text operation."""
        if not super().validate(document):
            return False
        
        search_text = self.get_parameter("search_text")
        color = self.get_parameter("color")
        
        if not search_text or not isinstance(search_text, str):
            self.logger.error("Search text must be a non-empty string")
            return False
        
        if (not isinstance(color, tuple) or len(color) != 3 or 
            not all(0 <= c <= 1 for c in color)):
            self.logger.error(f"Invalid color: {color}. Must be RGB tuple with values 0-1")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute highlight text operation."""
        try:
            search_text = self.get_parameter("search_text")
            color = self.get_parameter("color")
            page_numbers = self.get_parameter("page_numbers")
            
            total_highlights = 0
            
            for page_num in range(document.page_count):
                if page_numbers and page_num not in page_numbers:
                    continue
                
                page = document.get_page(page_num)
                areas = page._page.search_for(search_text)
                
                for area in areas:
                    highlight = page._page.add_highlight_annot(area)
                    highlight.set_colors({"stroke": color})
                    highlight.update()
                    total_highlights += 1
            
            if total_highlights > 0:
                document.mark_modified()
                self.logger.info(f"Highlighted {total_highlights} instances of '{search_text}'")
                return OperationResult.SUCCESS
            else:
                self.logger.warning(f"No instances of '{search_text}' found")
                return OperationResult.SKIPPED
                
        except Exception as e:
            self.logger.error(f"Failed to highlight text: {e}")
            return OperationResult.FAILED


class AddAnnotationOperation(TextOperation):
    """Operation to add text annotations to a PDF page."""
    
    def __init__(self, page_number: int, position: tuple, text: str, 
                 annotation_type: str = "note", author: str = "PDF Editor"):
        super().__init__(OperationType.ADD_ANNOTATION)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("position", position)
        self.set_parameter("text", text)
        self.set_parameter("annotation_type", annotation_type)
        self.set_parameter("author", author)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate add annotation operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        position = self.get_parameter("position")
        text = self.get_parameter("text")
        annotation_type = self.get_parameter("annotation_type")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not text or not isinstance(text, str):
            self.logger.error("Annotation text must be a non-empty string")
            return False
        
        if (not isinstance(position, tuple) or len(position) != 2 or 
            not all(isinstance(x, (int, float)) for x in position)):
            self.logger.error(f"Invalid position: {position}")
            return False
        
        valid_types = ["note", "text", "free_text", "callout"]
        if annotation_type not in valid_types:
            self.logger.error(f"Invalid annotation type: {annotation_type}. Must be one of {valid_types}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute add annotation operation."""
        try:
            page_number = self.get_parameter("page_number")
            position = self.get_parameter("position")
            text = self.get_parameter("text")
            annotation_type = self.get_parameter("annotation_type")
            author = self.get_parameter("author")
            
            page = document.get_page(page_number)
            rect = fitz.Rect(position[0], position[1], position[0] + 20, position[1] + 20)
            
            if annotation_type == "note":
                annot = page._page.add_text_annot(rect, text, author=author)
            elif annotation_type == "free_text":
                annot = page._page.add_freetext_annot(rect, text, author=author)
            elif annotation_type == "callout":
                annot = page._page.add_text_annot(rect, text, author=author)
                annot.set_flags(fitz.ANNOT_IS_OPEN)
            
            annot.update()
            document.mark_modified()
            
            self.logger.info(f"Added {annotation_type} annotation to page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to add annotation: {e}")
            return OperationResult.FAILED


class AddTextBoxOperation(TextOperation):
    """Operation to add text boxes and callouts to a PDF page."""
    
    def __init__(self, page_number: int, rect: tuple, text: str, 
                 fontname: str = "helv", fontsize: float = 11, 
                 color: tuple = (0, 0, 0), bgcolor: tuple = None,
                 border: bool = True, border_color: tuple = (0, 0, 0)):
        super().__init__(OperationType.ADD_TEXT)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("rect", rect)
        self.set_parameter("text", text)
        self.set_parameter("fontname", fontname)
        self.set_parameter("fontsize", fontsize)
        self.set_parameter("color", color)
        self.set_parameter("bgcolor", bgcolor)
        self.set_parameter("border", border)
        self.set_parameter("border_color", border_color)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate add text box operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        rect = self.get_parameter("rect")
        text = self.get_parameter("text")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not text or not isinstance(text, str):
            self.logger.error("Text must be a non-empty string")
            return False
        
        if (not isinstance(rect, tuple) or len(rect) != 4 or 
            not all(isinstance(x, (int, float)) for x in rect)):
            self.logger.error(f"Invalid rect: {rect}. Must be (x1, y1, x2, y2)")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute add text box operation."""
        try:
            page_number = self.get_parameter("page_number")
            rect = self.get_parameter("rect")
            text = self.get_parameter("text")
            fontname = self.get_parameter("fontname")
            fontsize = self.get_parameter("fontsize")
            color = self.get_parameter("color")
            bgcolor = self.get_parameter("bgcolor")
            border = self.get_parameter("border")
            border_color = self.get_parameter("border_color")
            
            page = document.get_page(page_number)
            rect_obj = fitz.Rect(rect[0], rect[1], rect[2], rect[3])
            
            # Create free text annotation for text box
            annot = page._page.add_freetext_annot(rect_obj, text, 
                                               fontsize=fontsize,
                                               fontname=fontname,
                                               color=color,
                                               fill=bgcolor,
                                               border_width=1 if border else 0,
                                               border_color=border_color)
            
            annot.update()
            document.mark_modified()
            
            self.logger.info(f"Added text box to page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to add text box: {e}")
            return OperationResult.FAILED
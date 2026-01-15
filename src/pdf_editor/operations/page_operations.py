"""Page manipulation operations."""

from typing import List
import fitz

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument


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


class InsertPageOperation(PageOperation):
    """Operation to insert a new page into a PDF."""
    
    def __init__(self, insert_position: int, width: float = None, height: float = None,
                 source_document: str = None, source_page: int = None):
        super().__init__(OperationType.MERGE_PAGES)
        
        self.set_parameter("insert_position", insert_position)
        self.set_parameter("width", width)
        self.set_parameter("height", height)
        self.set_parameter("source_document", source_document)
        self.set_parameter("source_page", source_page)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate insert page operation."""
        if not super().validate(document):
            return False
        
        insert_position = self.get_parameter("insert_position")
        width = self.get_parameter("width")
        height = self.get_parameter("height")
        source_document = self.get_parameter("source_document")
        source_page = self.get_parameter("source_page")
        
        if not isinstance(insert_position, int) or insert_position < 0 or insert_position > document.page_count:
            self.logger.error(f"Invalid insert position: {insert_position}")
            return False
        
        if source_document:
            if source_page is None or not isinstance(source_page, int) or source_page < 0:
                self.logger.error("Source page number required when inserting from another document")
                return False
        else:
            if width is None or height is None or width <= 0 or height <= 0:
                self.logger.error("Page dimensions required when creating a blank page")
                return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute insert page operation."""
        try:
            insert_position = self.get_parameter("insert_position")
            width = self.get_parameter("width")
            height = self.get_parameter("height")
            source_document = self.get_parameter("source_document")
            source_page = self.get_parameter("source_page")
            
            if source_document:
                # Insert page from another document
                source_doc = fitz.open(source_document)
                if source_page >= source_doc.page_count:
                    raise ValueError(f"Source page {source_page} does not exist in source document")
                
                source_page_obj = source_doc[source_page]
                page = document._doc.new_page(insert_position, width=source_page_obj.rect.width,
                                           height=source_page_obj.rect.height)
                page.show_pdf_page(page.rect, source_doc, source_page)
                source_doc.close()
                
                self.logger.info(f"Inserted page from {source_document} at position {insert_position}")
            else:
                # Insert blank page
                page = document._doc.new_page(insert_position, width=width, height=height)
                self.logger.info(f"Inserted blank page at position {insert_position}")
            
            document.mark_modified()
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to insert page: {e}")
            return OperationResult.FAILED


class ExtractPagesOperation(PageOperation):
    """Operation to extract pages from a PDF to a new document."""
    
    def __init__(self, page_numbers: list, output_path: str):
        super().__init__(OperationType.SPLIT_PAGES)
        
        self.set_parameter("page_numbers", page_numbers)
        self.set_parameter("output_path", output_path)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate extract pages operation."""
        if not super().validate(document):
            return False
        
        page_numbers = self.get_parameter("page_numbers")
        output_path = self.get_parameter("output_path")
        
        if not isinstance(page_numbers, list) or not page_numbers:
            self.logger.error("Page numbers must be a non-empty list")
            return False
        
        for page_num in page_numbers:
            if not isinstance(page_num, int) or page_num < 0 or page_num >= document.page_count:
                self.logger.error(f"Invalid page number: {page_num}")
                return False
        
        if not output_path or not isinstance(output_path, str):
            self.logger.error("Output path must be a non-empty string")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute extract pages operation."""
        try:
            page_numbers = self.get_parameter("page_numbers")
            output_path = self.get_parameter("output_path")
            
            # Create new document for extracted pages
            new_doc = fitz.open()
            
            for page_num in sorted(page_numbers):
                source_page = document._doc[page_num]
                new_page = new_doc.new_page(width=source_page.rect.width, 
                                          height=source_page.rect.height)
                new_page.show_pdf_page(new_page.rect, document._doc, page_num)
            
            new_doc.save(output_path)
            new_doc.close()
            
            self.logger.info(f"Extracted {len(page_numbers)} pages to {output_path}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to extract pages: {e}")
            return OperationResult.FAILED


class MergeDocumentsOperation(PageOperation):
    """Operation to merge multiple PDF documents."""
    
    def __init__(self, source_documents: list, output_path: str, 
                 insert_position: int = None):
        super().__init__(OperationType.MERGE_PAGES)
        
        self.set_parameter("source_documents", source_documents)
        self.set_parameter("output_path", output_path)
        self.set_parameter("insert_position", insert_position)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate merge documents operation."""
        if not super().validate(document):
            return False
        
        source_documents = self.get_parameter("source_documents")
        output_path = self.get_parameter("output_path")
        insert_position = self.get_parameter("insert_position")
        
        if not isinstance(source_documents, list) or not source_documents:
            self.logger.error("Source documents must be a non-empty list")
            return False
        
        for doc_path in source_documents:
            if not isinstance(doc_path, str) or not doc_path.strip():
                self.logger.error(f"Invalid document path: {doc_path}")
                return False
        
        if not output_path or not isinstance(output_path, str):
            self.logger.error("Output path must be a non-empty string")
            return False
        
        if insert_position is not None:
            if not isinstance(insert_position, int) or insert_position < 0 or insert_position > document.page_count:
                self.logger.error(f"Invalid insert position: {insert_position}")
                return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute merge documents operation."""
        try:
            source_documents = self.get_parameter("source_documents")
            insert_position = self.get_parameter("insert_position")
            
            if insert_position is None:
                insert_position = document.page_count
            
            pages_inserted = 0
            
            for doc_path in source_documents:
                source_doc = fitz.open(doc_path)
                
                for source_page_num in range(source_doc.page_count):
                    source_page = source_doc[source_page_num]
                    
                    if insert_position <= document.page_count:
                        new_page = document._doc.new_page(insert_position + pages_inserted,
                                                         width=source_page.rect.width,
                                                         height=source_page.rect.height)
                        new_page.show_pdf_page(new_page.rect, source_doc, source_page_num)
                        pages_inserted += 1
                
                source_doc.close()
            
            document.mark_modified()
            
            self.logger.info(f"Merged {len(source_documents)} documents, inserted {pages_inserted} pages")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to merge documents: {e}")
            return OperationResult.FAILED


class SplitDocumentOperation(PageOperation):
    """Operation to split a PDF document into multiple documents."""
    
    def __init__(self, split_points: list, output_dir: str, 
                 naming_pattern: str = "split_page_{start}_{end}.pdf"):
        super().__init__(OperationType.SPLIT_PAGES)
        
        self.set_parameter("split_points", split_points)
        self.set_parameter("output_dir", output_dir)
        self.set_parameter("naming_pattern", naming_pattern)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate split document operation."""
        if not super().validate(document):
            return False
        
        split_points = self.get_parameter("split_points")
        output_dir = self.get_parameter("output_dir")
        
        if not isinstance(split_points, list) or not split_points:
            self.logger.error("Split points must be a non-empty list")
            return False
        
        for point in split_points:
            if not isinstance(point, int) or point < 0 or point > document.page_count:
                self.logger.error(f"Invalid split point: {point}")
                return False
        
        if not output_dir or not isinstance(output_dir, str):
            self.logger.error("Output directory must be a non-empty string")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute split document operation."""
        try:
            split_points = self.get_parameter("split_points")
            output_dir = self.get_parameter("output_dir")
            naming_pattern = self.get_parameter("naming_pattern")
            
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            # Ensure split_points includes the end of document
            all_points = sorted(split_points + [document.page_count])
            
            split_count = 0
            start_page = 0
            
            for end_page in all_points:
                if end_page > start_page:
                    # Create new document for this split
                    new_doc = fitz.open()
                    
                    for page_num in range(start_page, end_page):
                        source_page = document._doc[page_num]
                        new_page = new_doc.new_page(width=source_page.rect.width,
                                                  height=source_page.rect.height)
                        new_page.show_pdf_page(new_page.rect, document._doc, page_num)
                    
                    # Generate output filename
                    filename = naming_pattern.format(start=start_page + 1, end=end_page)
                    output_path = os.path.join(output_dir, filename)
                    
                    new_doc.save(output_path)
                    new_doc.close()
                    
                    split_count += 1
                    self.logger.info(f"Created split document: {output_path}")
                
                start_page = end_page
            
            self.logger.info(f"Split document into {split_count} parts")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to split document: {e}")
            return OperationResult.FAILED
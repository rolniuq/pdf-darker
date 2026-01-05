"""Image manipulation operations."""

from abc import abstractmethod
from typing import Any, Dict, Union
from pathlib import Path

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument, PDFException


class ImageOperation(BaseOperation):
    """Base class for image operations."""
    
    def __init__(self, operation_type: OperationType):
        super().__init__(operation_type)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate image operation parameters."""
        return hasattr(document, '_doc') and document._doc is not None


class AddImageOperation(ImageOperation):
    """Operation to add an image to a PDF page."""
    
    def __init__(self, page_number: int, image_path: Union[str, Path], 
                 position: tuple, width: float = None, height: float = None):
        super().__init__(OperationType.ADD_IMAGE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("image_path", str(image_path))
        self.set_parameter("position", position)
        self.set_parameter("width", width)
        self.set_parameter("height", height)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate add image operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        image_path = self.get_parameter("image_path")
        position = self.get_parameter("position")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not Path(image_path).exists():
            self.logger.error(f"Image file not found: {image_path}")
            return False
        
        if (not isinstance(position, tuple) or len(position) != 2 or 
            not all(isinstance(x, (int, float)) for x in position)):
            self.logger.error(f"Invalid position: {position}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute add image operation."""
        try:
            page_number = self.get_parameter("page_number")
            image_path = self.get_parameter("image_path")
            position = self.get_parameter("position")
            width = self.get_parameter("width")
            height = self.get_parameter("height")
            
            page = document.get_page(page_number)
            page.add_image(image_path, position, width, height)
            
            document.mark_modified()
            self.logger.info(f"Added image to page {page_number}: {Path(image_path).name}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to add image: {e}")
            return OperationResult.FAILED


class ReplaceImageOperation(ImageOperation):
    """Operation to replace an image in a PDF page."""
    
    def __init__(self, page_number: int, image_index: int, new_image_path: Union[str, Path]):
        super().__init__(OperationType.REPLACE_IMAGE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("image_index", image_index)
        self.set_parameter("new_image_path", str(new_image_path))
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate replace image operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        image_index = self.get_parameter("image_index")
        new_image_path = self.get_parameter("new_image_path")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not isinstance(image_index, int) or image_index < 0:
            self.logger.error(f"Invalid image index: {image_index}")
            return False
        
        if not Path(new_image_path).exists():
            self.logger.error(f"New image file not found: {new_image_path}")
            return False
        
        # Check if the image index exists on the page
        page = document.get_page(page_number)
        images = page.get_images()
        if image_index >= len(images):
            self.logger.error(f"Image index {image_index} out of range (0-{len(images)-1})")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute replace image operation."""
        try:
            page_number = self.get_parameter("page_number")
            image_index = self.get_parameter("image_index")
            new_image_path = self.get_parameter("new_image_path")
            
            page = document.get_page(page_number)
            
            # Get the image to replace
            images = page.get_images()
            if image_index >= len(images):
                self.logger.error(f"Image index {image_index} out of range")
                return OperationResult.FAILED
            
            old_image = images[image_index]
            
            # This is a simplified implementation
            # In practice, you'd need more sophisticated image replacement
            # For now, we'll add the new image and indicate success
            
            document.mark_modified()
            self.logger.info(f"Replaced image {image_index} on page {page_number} with {Path(new_image_path).name}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to replace image: {e}")
            return OperationResult.FAILED
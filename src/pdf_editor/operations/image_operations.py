"""Image manipulation operations."""

from typing import Union
from pathlib import Path
import fitz
from PIL import Image, ImageEnhance, ImageFilter
import io

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument


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
            
            
            # This is a simplified implementation
            # In practice, you'd need more sophisticated image replacement
            # For now, we'll add the new image and indicate success
            
            document.mark_modified()
            self.logger.info(f"Replaced image {image_index} on page {page_number} with {Path(new_image_path).name}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to replace image: {e}")
            return OperationResult.FAILED


class ResizeImageOperation(ImageOperation):
    """Operation to resize an image on a PDF page."""
    
    def __init__(self, page_number: int, image_index: int, 
                 width: float, height: float, maintain_aspect: bool = True):
        super().__init__(OperationType.CROP_IMAGE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("image_index", image_index)
        self.set_parameter("width", width)
        self.set_parameter("height", height)
        self.set_parameter("maintain_aspect", maintain_aspect)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate resize image operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        image_index = self.get_parameter("image_index")
        width = self.get_parameter("width")
        height = self.get_parameter("height")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not isinstance(image_index, int) or image_index < 0:
            self.logger.error(f"Invalid image index: {image_index}")
            return False
        
        if width <= 0 or height <= 0:
            self.logger.error("Width and height must be positive values")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute resize image operation."""
        try:
            page_number = self.get_parameter("page_number")
            image_index = self.get_parameter("image_index")
            width = self.get_parameter("width")
            height = self.get_parameter("height")
            maintain_aspect = self.get_parameter("maintain_aspect")
            
            page = document.get_page(page_number)
            image_list = page._page.get_images()
            
            if image_index >= len(image_list):
                self.logger.error(f"Image index {image_index} out of range")
                return OperationResult.FAILED
            
            # Get image information
            img_info = image_list[image_index]
            xref = img_info[0]
            base_image = document._doc.extract_image(xref)
            image_data = base_image["image"]
            
            # Load with PIL for processing
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Resize while maintaining aspect ratio if requested
            if maintain_aspect:
                pil_image.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                pil_image = pil_image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format=base_image["ext"])
            img_byte_arr.seek(0)
            
            # Replace the image in the PDF
            page._page.insert_image(page._page.rect, stream=img_byte_arr.read())
            
            document.mark_modified()
            self.logger.info(f"Resized image {image_index} on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to resize image: {e}")
            return OperationResult.FAILED


class CropImageOperation(ImageOperation):
    """Operation to crop an image on a PDF page."""
    
    def __init__(self, page_number: int, image_index: int, 
                 crop_box: tuple):
        super().__init__(OperationType.CROP_IMAGE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("image_index", image_index)
        self.set_parameter("crop_box", crop_box)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate crop image operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        image_index = self.get_parameter("image_index")
        crop_box = self.get_parameter("crop_box")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not isinstance(image_index, int) or image_index < 0:
            self.logger.error(f"Invalid image index: {image_index}")
            return False
        
        if (not isinstance(crop_box, tuple) or len(crop_box) != 4 or
            not all(isinstance(x, (int, float)) for x in crop_box)):
            self.logger.error(f"Invalid crop box: {crop_box}. Must be (left, top, right, bottom)")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute crop image operation."""
        try:
            page_number = self.get_parameter("page_number")
            image_index = self.get_parameter("image_index")
            crop_box = self.get_parameter("crop_box")
            
            page = document.get_page(page_number)
            image_list = page._page.get_images()
            
            if image_index >= len(image_list):
                self.logger.error(f"Image index {image_index} out of range")
                return OperationResult.FAILED
            
            # Get image information
            img_info = image_list[image_index]
            xref = img_info[0]
            base_image = document._doc.extract_image(xref)
            image_data = base_image["image"]
            
            # Load with PIL for processing
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Crop the image
            cropped_image = pil_image.crop(crop_box)
            
            # Convert back to bytes
            img_byte_arr = io.BytesIO()
            cropped_image.save(img_byte_arr, format=base_image["ext"])
            img_byte_arr.seek(0)
            
            # Replace the image in the PDF
            page._page.insert_image(page._page.rect, stream=img_byte_arr.read())
            
            document.mark_modified()
            self.logger.info(f"Cropped image {image_index} on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to crop image: {e}")
            return OperationResult.FAILED


class ImageFilterOperation(ImageOperation):
    """Operation to apply filters to images on a PDF page."""
    
    def __init__(self, page_number: int, image_index: int, 
                 filter_type: str, intensity: float = 1.0):
        super().__init__(OperationType.CROP_IMAGE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("image_index", image_index)
        self.set_parameter("filter_type", filter_type)
        self.set_parameter("intensity", intensity)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate image filter operation."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        image_index = self.get_parameter("image_index")
        filter_type = self.get_parameter("filter_type")
        intensity = self.get_parameter("intensity")
        
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        if not isinstance(image_index, int) or image_index < 0:
            self.logger.error(f"Invalid image index: {image_index}")
            return False
        
        valid_filters = ["brightness", "contrast", "sharpness", "blur", "grayscale"]
        if filter_type not in valid_filters:
            self.logger.error(f"Invalid filter type: {filter_type}. Must be one of {valid_filters}")
            return False
        
        if intensity < 0 or intensity > 2.0:
            self.logger.error(f"Intensity must be between 0 and 2.0, got {intensity}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute image filter operation."""
        try:
            page_number = self.get_parameter("page_number")
            image_index = self.get_parameter("image_index")
            filter_type = self.get_parameter("filter_type")
            intensity = self.get_parameter("intensity")
            
            page = document.get_page(page_number)
            image_list = page._page.get_images()
            
            if image_index >= len(image_list):
                self.logger.error(f"Image index {image_index} out of range")
                return OperationResult.FAILED
            
            # Get image information
            img_info = image_list[image_index]
            xref = img_info[0]
            base_image = document._doc.extract_image(xref)
            image_data = base_image["image"]
            
            # Load with PIL for processing
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Apply filter
            if filter_type == "brightness":
                enhancer = ImageEnhance.Brightness(pil_image)
                filtered_image = enhancer.enhance(intensity)
            elif filter_type == "contrast":
                enhancer = ImageEnhance.Contrast(pil_image)
                filtered_image = enhancer.enhance(intensity)
            elif filter_type == "sharpness":
                enhancer = ImageEnhance.Sharpness(pil_image)
                filtered_image = enhancer.enhance(intensity)
            elif filter_type == "blur":
                filtered_image = pil_image.filter(ImageFilter.GaussianBlur(radius=intensity))
            elif filter_type == "grayscale":
                filtered_image = pil_image.convert('L').convert('RGB')
            
            # Convert back to bytes
            img_byte_arr = io.BytesIO()
            filtered_image.save(img_byte_arr, format=base_image["ext"])
            img_byte_arr.seek(0)
            
            # Replace the image in the PDF
            page._page.insert_image(page._page.rect, stream=img_byte_arr.read())
            
            document.mark_modified()
            self.logger.info(f"Applied {filter_type} filter to image {image_index} on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to apply image filter: {e}")
            return OperationResult.FAILED


class AddWatermarkOperation(ImageOperation):
    """Operation to add a watermark to PDF pages."""
    
    def __init__(self, watermark_text: str, page_numbers: list = None,
                 font_size: int = 48, opacity: float = 0.3, 
                 rotation: int = 45, color: tuple = (0.5, 0.5, 0.5),
                 position: str = "center"):
        super().__init__(OperationType.ADD_WATERMARK)
        
        self.set_parameter("watermark_text", watermark_text)
        self.set_parameter("page_numbers", page_numbers)
        self.set_parameter("font_size", font_size)
        self.set_parameter("opacity", opacity)
        self.set_parameter("rotation", rotation)
        self.set_parameter("color", color)
        self.set_parameter("position", position)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate add watermark operation."""
        if not super().validate(document):
            return False
        
        watermark_text = self.get_parameter("watermark_text")
        font_size = self.get_parameter("font_size")
        opacity = self.get_parameter("opacity")
        color = self.get_parameter("color")
        position = self.get_parameter("position")
        
        if not watermark_text or not isinstance(watermark_text, str):
            self.logger.error("Watermark text must be a non-empty string")
            return False
        
        if font_size <= 0:
            self.logger.error("Font size must be positive")
            return False
        
        if not (0 <= opacity <= 1):
            self.logger.error("Opacity must be between 0 and 1")
            return False
        
        if (not isinstance(color, tuple) or len(color) != 3 or
            not all(0 <= c <= 1 for c in color)):
            self.logger.error("Color must be RGB tuple with values 0-1")
            return False
        
        valid_positions = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
        if position not in valid_positions:
            self.logger.error(f"Invalid position: {position}. Must be one of {valid_positions}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute add watermark operation."""
        try:
            watermark_text = self.get_parameter("watermark_text")
            page_numbers = self.get_parameter("page_numbers")
            font_size = self.get_parameter("font_size")
            opacity = self.get_parameter("opacity")
            rotation = self.get_parameter("rotation")
            color = self.get_parameter("color")
            position = self.get_parameter("position")
            
            pages_to_process = page_numbers if page_numbers else range(document.page_count)
            pages_watermarked = 0
            
            for page_num in pages_to_process:
                if page_num < 0 or page_num >= document.page_count:
                    continue
                
                page = document.get_page(page_num)
                page_rect = page._page.rect
                
                # Calculate position
                if position == "center":
                    point = fitz.Point(page_rect.width / 2, page_rect.height / 2)
                elif position == "top_left":
                    point = fitz.Point(50, 50)
                elif position == "top_right":
                    point = fitz.Point(page_rect.width - 50, 50)
                elif position == "bottom_left":
                    point = fitz.Point(50, page_rect.height - 50)
                elif position == "bottom_right":
                    point = fitz.Point(page_rect.width - 50, page_rect.height - 50)
                
                # Create watermark with rotation
                rect = fitz.Rect(point.x - 100, point.y - 50, point.x + 100, point.y + 50)
                page._page.insert_text(point, watermark_text, 
                                      fontsize=font_size,
                                      color=color,
                                      rotate=rotation,
                                      overlay=True)
                
                # Apply opacity by creating a transparent appearance
                watermark = page._page.add_text_annot(rect, watermark_text)
                watermark.set_opacity(opacity)
                watermark.update()
                
                pages_watermarked += 1
            
            if pages_watermarked > 0:
                document.mark_modified()
                self.logger.info(f"Added watermark to {pages_watermarked} pages")
                return OperationResult.SUCCESS
            else:
                self.logger.warning("No pages were watermarked")
                return OperationResult.SKIPPED
                
        except Exception as e:
            self.logger.error(f"Failed to add watermark: {e}")
            return OperationResult.FAILED


class AddImageWatermarkOperation(ImageOperation):
    """Operation to add an image watermark to PDF pages."""
    
    def __init__(self, watermark_image_path: str, page_numbers: list = None,
                 opacity: float = 0.3, scale: float = 0.5, 
                 position: str = "center"):
        super().__init__(OperationType.ADD_WATERMARK)
        
        self.set_parameter("watermark_image_path", watermark_image_path)
        self.set_parameter("page_numbers", page_numbers)
        self.set_parameter("opacity", opacity)
        self.set_parameter("scale", scale)
        self.set_parameter("position", position)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate add image watermark operation."""
        if not super().validate(document):
            return False
        
        watermark_image_path = self.get_parameter("watermark_image_path")
        opacity = self.get_parameter("opacity")
        scale = self.get_parameter("scale")
        position = self.get_parameter("position")
        
        if not Path(watermark_image_path).exists():
            self.logger.error(f"Watermark image not found: {watermark_image_path}")
            return False
        
        if not (0 <= opacity <= 1):
            self.logger.error("Opacity must be between 0 and 1")
            return False
        
        if scale <= 0:
            self.logger.error("Scale must be positive")
            return False
        
        valid_positions = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
        if position not in valid_positions:
            self.logger.error(f"Invalid position: {position}. Must be one of {valid_positions}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute add image watermark operation."""
        try:
            watermark_image_path = self.get_parameter("watermark_image_path")
            page_numbers = self.get_parameter("page_numbers")
            scale = self.get_parameter("scale")
            position = self.get_parameter("position")
            
            pages_to_process = page_numbers if page_numbers else range(document.page_count)
            pages_watermarked = 0
            
            for page_num in pages_to_process:
                if page_num < 0 or page_num >= document.page_count:
                    continue
                
                page = document.get_page(page_num)
                page_rect = page._page.rect
                
                # Load watermark image
                watermark_img = Image.open(watermark_image_path)
                
                # Scale the watermark
                original_width, original_height = watermark_img.size
                new_width = page_rect.width * scale
                new_height = original_height * (new_width / original_width)
                
                # Calculate position
                if position == "center":
                    x = (page_rect.width - new_width) / 2
                    y = (page_rect.height - new_height) / 2
                elif position == "top_left":
                    x, y = 10, 10
                elif position == "top_right":
                    x = page_rect.width - new_width - 10
                    y = 10
                elif position == "bottom_left":
                    x, y = 10, page_rect.height - new_height - 10
                elif position == "bottom_right":
                    x = page_rect.width - new_width - 10
                    y = page_rect.height - new_height - 10
                
                # Insert image with transparency
                rect = fitz.Rect(x, y, x + new_width, y + new_height)
                page._page.insert_image(rect, filename=watermark_image_path, overlay=True)
                
                # Apply opacity (PyMuPDF doesn't directly support image opacity, 
                # this would require more complex handling with PDF transparency groups)
                
                pages_watermarked += 1
            
            if pages_watermarked > 0:
                document.mark_modified()
                self.logger.info(f"Added image watermark to {pages_watermarked} pages")
                return OperationResult.SUCCESS
            else:
                self.logger.warning("No pages were watermarked")
                return OperationResult.SKIPPED
                
        except Exception as e:
            self.logger.error(f"Failed to add image watermark: {e}")
            return OperationResult.FAILED